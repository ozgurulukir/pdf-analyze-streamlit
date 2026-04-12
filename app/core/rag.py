"""RAG orchestration with LangChain, Ollama, and ChromaDB."""

import collections
from collections.abc import Generator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.config import AppConfig
from app.core.database import DatabaseManager
from app.core.exceptions import (
    ChromaError,
    LLMConnectionError,
    LLMError,
)
from app.core.logger import logger
from app.core.models import Message, QAPair, UserPreferences


def create_llm(
    base_url: str,
    api_key: str,
    model: str,
    temperature: float | None = None,
    streaming: bool = False,
) -> ChatOpenAI:
    """
    Standalone helper to create a LangChain LLM instance.
    Useful for connection testing or external orchestration.
    """
    from app.core.container import get_config
    config = get_config()
    temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
    try:
        return ChatOpenAI(
            openai_api_key=SecretStr(api_key) if api_key else None,
            openai_api_base=base_url,
            model_name=model,
            temperature=temperature,
            streaming=streaming,
        )
    except Exception as e:
        logger.error(f"LLM creation failed: {e}")
        raise LLMError(f"Failed to create LLM: {e}")


class PromptTemplates:
    """Centralized prompt templates for RAG operations."""

    SYSTEM_IDENTITY = (
        "Sen gelişmiş bir PDF ve Belge Analiz Asistanısın. "
        "Sana sağlanan bağlamı (context) kullanarak soruları yanıtlıyorsun. "
        "Eğer yanıt bağlamda yoksa, bunu belirt ve yanlış bilgi uydurma. "
        "Yanıtlarını her zaman Türkçe dilinde ver."
    )

    RAG_CONTEXT_TEMPLATE = (
        "Aşağıdaki bağlamı kullanarak soruyu yanıtla:\n\n"
        "--- BAĞLAM ---\n"
        "{context}\n"
        "--- BAĞLAM SONU ---\n\n"
        "Kullanıcı Tercihleri (Yanıt stilini buna göre ayarla):\n"
        "{preferences}\n\n"
        "Soru: {question}"
    )

    TAG_GENERATION_PROMPT = (
        "Aşağıdaki soru ve cevabı analiz ederek, bu içeriği en iyi tanımlayan en fazla 3 adet kısa etiket (tag) oluştur. "
        "Etiketler Türkçe olmalı, aralarına virgül koyarak tek bir satırda yaz. "
        "Sadece etiketleri dön, açıklama yapma.\n\n"
        "Soru: {question}\n"
        "Cevap: {answer}"
    )


class MessageCache:
    """Thread-safe LRU cache for chat history using deque for O(1) operations."""

    def __init__(self, max_size: int | None = None):
        """
        Initialize the message cache.

        Args:
            max_size: Maximum messages (uses config if None).
        """
        from app.core.container import get_config
        config = get_config()
        self.max_size = max_size or config.MAX_MESSAGES_IN_MEMORY
        self.messages: collections.deque = collections.deque(maxlen=self.max_size)

    def add(self, message: Message) -> None:
        """Add a message to the cache."""
        self.messages.append(message)

    def get_all(self) -> list[Message]:
        """Return all cached messages in chronological order."""
        return list(self.messages)

    def clear(self) -> None:
        """Wipe the cache."""
        self.messages.clear()

    def to_langchain(self) -> list[Any]:
        """Convert cached messages to LangChain message format."""
        lc_messages = []
        for msg in self.messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages


class QAManager:
    """Manages Q&A pair extraction and management."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize the QA manager.

        Args:
            db: Database manager instance
        """
        self.db = db

    def save_qa(
        self, workspace_id: str, question: str, answer: str, file_ids: list[str]
    ) -> QAPair:
        """
        Create and persist a new Q&A pair.

        Args:
            workspace_id: ID of the workspace
            question: The user's query
            answer: The systematic response
            file_ids: List of source file IDs

        Returns:
            QAPair: The created model
        """
        qa = QAPair(
            workspace_id=workspace_id,
            file_ids=file_ids,
            question=question,
            answer=answer,
        )
        return self.db.qa.create(qa)

    def get_workspace_qa(self, workspace_id: str) -> list[QAPair]:
        """Fetch all QA pairs for a workspace."""
        return self.db.qa.get_by_workspace(workspace_id)

    def like(self, qa_id: str) -> None:
        """
        Increment likes for a QA pair.

        Args:
            qa_id: Unique ID of the QA pair
        """
        try:
            target = self.db.qa.get_by_id(qa_id)
            if target:
                self.db.qa.update_votes(qa_id, target.likes + 1, target.dislikes)
        except Exception as e:
            logger.error(f"Failed to like QA {qa_id}: {e}")

    def dislike(self, qa_id: str) -> None:
        """
        Increment dislikes for a QA pair.

        Args:
            qa_id: Unique ID of the QA pair
        """
        try:
            target = self.db.qa.get_by_id(qa_id)
            if target:
                self.db.qa.update_votes(qa_id, target.likes, target.dislikes + 1)
        except Exception as e:
            logger.error(f"Failed to dislike QA {qa_id}: {e}")


class RAGChain:
    """Orchestrates the Retrieval-Augmented Generation pipeline."""

    def __init__(
        self,
        db: DatabaseManager,
        chroma: ChromaManager,
        embedding: EmbeddingManager,
        llm_config: dict[str, Any],
        workspace_id: str,
        session_id: str | None = None,
        config: AppConfig | None = None,
    ):
        """
        Initialize the RAG chain.
        """
        from app.core.container import get_config
        self.db = db
        self.chroma = chroma
        self.embedding = embedding
        self.llm_config = llm_config
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.config = config or get_config()

        # Load workspace metadata
        self.workspace = self.db.workspaces.get_by_id(workspace_id)
        if not self.workspace:
            raise ChromaError(f"Workspace {workspace_id} not found in database.")

        self.cache = MessageCache(max_size=self.config.MAX_MESSAGES_IN_MEMORY)
        self._load_history()

    def _load_history(self) -> None:
        """Populate the message cache from database history."""
        messages = self.db.messages.get_by_workspace(
            self.workspace_id, limit=self.config.MAX_MESSAGES_IN_MEMORY, session_id=self.session_id
        )
        for msg in messages:
            self.cache.add(msg)

    def generate_tags(self, question: str, answer: str) -> list[str]:
        """Generate descriptive tags for a Q&A pair using the LLM."""
        try:
            llm = self._get_llm(streaming=False)
            prompt = ChatPromptTemplate.from_template(PromptTemplates.TAG_GENERATION_PROMPT)
            chain = prompt | llm | StrOutputParser()

            response = chain.invoke({"question": question, "answer": answer})
            tags = [tag.strip().replace("#", "").title() for tag in response.split(",") if tag.strip()]
            return tags[:3]
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            return ["Genel"]

    def _get_llm(self, streaming: bool = False) -> ChatOpenAI:
        try:
            return ChatOpenAI(
                openai_api_key=SecretStr(self.llm_config.get("api_key", self.config.OLLAMA_API_KEY))
                if self.llm_config.get("api_key", self.config.OLLAMA_API_KEY) else None,
                openai_api_base=self.llm_config.get("base_url", self.config.LLM_BASE_URL),
                model_name=self.llm_config.get("model", self.config.LLM_MODEL),
                temperature=self.llm_config.get("temperature", self.config.LLM_TEMPERATURE),
                streaming=streaming,
            )
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            raise LLMConnectionError(f"Failed to start LLM: {e}")

    def _format_prefs(self, prefs: UserPreferences) -> str:
        """Convert preference weights to a natural language response instruction."""
        instructions = []
        if prefs.weights.get("concise", 0) > 0.7:
            instructions.append("Yanıtların çok kısa, öz ve net olsun.")
        if prefs.weights.get("detailed", 0) > 0.7:
            instructions.append("Mümkün olduğunca detaylı ve kapsamlı açıkla.")
        if prefs.weights.get("examples", 0) > 0.7:
            instructions.append("Açıklamalarını somut örneklerle destekle.")
        if prefs.weights.get("step_by_step", 0) > 0.7:
            instructions.append("Karmaşık konuları adım adım (liste şeklinde) anlat.")

        return (
            " ".join(instructions)
            if instructions
            else "Bağlama dayalı yardımcı bir yanıt ver."
        )

    def stream_query(self, question: str) -> Generator[dict[str, Any], None, None]:
        """
        Execute RAG query and yield tokens in a stream.

        Yields:
            Dict: Stream events like 'status', 'token', 'source', 'error'
        """
        try:
            yield {"type": "status", "content": "🔍 Dökümanlar taranıyor..."}

            # 0. Check Collection Count (Early exit if empty)
            try:
                if not self.workspace:
                    raise ChromaError("Çalışma alanı bulunamadı.")

                # Check DB first
                db_file_count = self.db.files.count_by_workspace(self.workspace_id)

                ws_name = self.workspace.name
                collection = self.chroma.get_collection(self.workspace_id, ws_name)

                if not collection or collection.count() == 0:
                    if db_file_count > 0:
                        yield {
                            "type": "error",
                            "content": f"⚠️ Veritabanında {db_file_count} belge görünüyor ancak vektör dizini (Chroma) boş. Lütfen belgeleri tekrar yükleyin veya 'Sistemi Senkronize Et' butonunu kullanın.",
                        }
                    else:
                        yield {
                            "type": "error",
                            "content": "⚠️ Seçili çalışma alanında taranmış döküman bulunamadı. Lütfen önce döküman yükleyin.",
                        }
                    return
            except Exception as checker_e:
                logger.warning(f"[RAG] Collection check failed: {checker_e}")

            # 1. Similarity Search
            query_vec = self.embedding.get_query_embedding(question)
            logger.info(f"[RAG] Query embedding generated, length: {len(query_vec)}")

            if not self.workspace:
                 raise ChromaError("Çalışma alanı bulunamadı.")

            docs, distances, metadatas = self.chroma.query(
                self.workspace_id,
                self.workspace.name,
                query_vec,
                n_results=self.config.DEFAULT_RETRIEVER_K,
            )

            # DEBUG: Log query results
            logger.info(f"[RAG] Query returned {len(docs)} documents")
            if distances:
                logger.info(f"[RAG] Distances: {distances}")

            if not docs:
                yield {
                    "type": "status",
                    "content": "⚠️ Bağlam bulunamadı, genel bilgi kullanılıyor...",
                }
                context_text = "Seçili dökümanlarda bu konuyla ilgili bilgi bulunamadı."
            else:
                context_text = "\n\n".join(docs)

            # 2. Extract sources
            sources = list({m.get("source", "Bilinmeyen") for m in metadatas})
            if sources:
                yield {"type": "sources", "content": sources}

            # 3. Pull preferences
            prefs = self.db.preferences.get()
            pref_instructions = self._format_prefs(prefs)

            # 4. Prepare Chain
            llm = self._get_llm(streaming=True)
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", PromptTemplates.SYSTEM_IDENTITY),
                    ("human", PromptTemplates.RAG_CONTEXT_TEMPLATE),
                ]
            )

            chain = prompt | llm | StrOutputParser()

            # 5. Execute Stream
            full_response = ""

            yield {"type": "status", "content": "🧠 Yanıt oluşturuluyor..."}

            for token in chain.stream(
                {
                    "context": context_text,
                    "question": question,
                    "preferences": pref_instructions,
                }
            ):
                full_response += token
                yield {"type": "token", "content": token}

            # 6. Update in-memory cache
            user_msg = Message(
                role="user", content=question, workspace_id=self.workspace_id, session_id=self.session_id
            )
            ai_msg = Message(
                role="assistant",
                content=full_response,
                workspace_id=self.workspace_id,
                sources=sources,
                session_id=self.session_id
            )

            self.cache.add(user_msg)
            self.cache.add(ai_msg)

        except Exception as e:
            logger.error(f"RAG stream error: {e}")
            yield {"type": "error", "content": str(e)}

    def clear_history(self) -> None:
        """Wipe conversation history for this workspace."""
        self.db.messages.clear_by_workspace(self.workspace_id)
        self.cache.clear()
        logger.info(f"Chat history cleared for workspace {self.workspace_id}")
