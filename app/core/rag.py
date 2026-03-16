"""RAG orchestration with LangChain, Ollama, and ChromaDB."""
import json
import collections
from typing import List, Optional, Dict, Any, Generator, Tuple, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.models import Message, QAPair, UserPreferences
from app.core.database import DatabaseManager
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.exceptions import LLMError, ChromaError
from app.core.logger import logger
from app.core.config import AppConfig


def create_llm(
    base_url: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    streaming: bool = False
) -> ChatOpenAI:
    """
    Standalone helper to create a LangChain LLM instance.
    Useful for connection testing or external orchestration.
    """
    try:
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            streaming=streaming
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


class MessageCache:
    """Thread-safe LRU cache for chat history using deque for O(1) operations."""

    def __init__(self, max_size: int = 100):
        """
        Initialize the message cache.
        
        Args:
            max_size: Maximum number of messages to keep in memory.
        """
        self.max_size = max_size
        self.messages: collections.deque = collections.deque(maxlen=max_size)

    def add(self, message: Message) -> None:
        """Add a message to the cache."""
        self.messages.append(message)

    def get_all(self) -> List[Message]:
        """Return all cached messages in chronological order."""
        return list(self.messages)

    def clear(self) -> None:
        """Wipe the cache."""
        self.messages.clear()

    def to_langchain(self) -> List[Any]:
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

    def save_qa(self, workspace_id: str, question: str, answer: str, file_ids: List[str]) -> QAPair:
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
            answer=answer
        )
        return self.db.create_qa_pair(qa)

    def get_workspace_qa(self, workspace_id: str) -> List[QAPair]:
        """Fetch all QA pairs for a workspace."""
        return self.db.get_qa_pairs(workspace_id)

    def like(self, qa_id: str) -> None:
        """
        Increment likes for a QA pair.
        
        Args:
            qa_id: Unique ID of the QA pair
        """
        try:
            qa_list = self.db.get_qa_pairs()
            target = next((q for q in qa_list if q.id == qa_id), None)
            if target:
                self.db.update_qa_votes(qa_id, target.likes + 1, target.dislikes)
        except Exception as e:
            logger.error(f"Failed to like QA {qa_id}: {e}")

    def dislike(self, qa_id: str) -> None:
        """
        Increment dislikes for a QA pair.
        
        Args:
            qa_id: Unique ID of the QA pair
        """
        try:
            qa_list = self.db.get_qa_pairs()
            target = next((q for q in qa_list if q.id == qa_id), None)
            if target:
                self.db.update_qa_votes(qa_id, target.likes, target.dislikes + 1)
        except Exception as e:
            logger.error(f"Failed to dislike QA {qa_id}: {e}")


class RAGChain:
    """Orchestrates the Retrieval-Augmented Generation pipeline."""

    def __init__(
        self,
        db: DatabaseManager,
        chroma: ChromaManager,
        embedding: EmbeddingManager,
        llm_config: Dict[str, Any],
        workspace_id: str
    ):
        """
        Initialize the RAG chain.
        """
        self.db = db
        self.chroma = chroma
        self.embedding = embedding
        self.llm_config = llm_config
        self.workspace_id = workspace_id
        
        # Load workspace metadata
        self.workspace = self.db.get_workspace(workspace_id)
        if not self.workspace:
            raise ChromaError(f"Workspace {workspace_id} not found in database.")
            
        self.cache = MessageCache()
        self._load_history()

    def _load_history(self) -> None:
        """Populate the message cache from database history."""
        messages = self.db.get_messages(self.workspace_id, limit=50)
        for msg in messages:
            self.cache.add(msg)

    def _get_llm(self, streaming: bool = False):
        config = AppConfig()
        
        try:
            return ChatOpenAI(
                api_key=self.llm_config.get("api_key", config.OLLAMA_API_KEY),
                base_url=self.llm_config.get("base_url", config.LLM_BASE_URL),
                model=self.llm_config.get("model", config.LLM_MODEL),
                temperature=self.llm_config.get("temperature", config.LLM_TEMPERATURE),
                streaming=streaming
            )
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            raise LLMError(f"Failed to start LLM: {e}")

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
            
        return " ".join(instructions) if instructions else "Bağlama dayalı yardımcı bir yanıt ver."

    def stream_query(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Execute RAG query and yield tokens in a stream.
        
        Yields:
            Dict: Stream events like 'status', 'token', 'source', 'error'
        """
        try:
            yield {"type": "status", "content": "🔍 Dökümanlar taranıyor..."}
            
            # DEBUG: Log collection info
            collection_name = self.chroma.get_collection_name(self.workspace_id, self.workspace.name)
            logger.info(f"[RAG] Collection name: {collection_name}")
            
            # 1. Similarity Search
            query_vec = self.embedding.get_query_embedding(question)
            logger.info(f"[RAG] Query embedding generated, length: {len(query_vec)}")
            
            docs, distances, metadatas = self.chroma.query(
                self.workspace_id, self.workspace.name, query_vec, n_results=5
            )
            
            # DEBUG: Log query results
            logger.info(f"[RAG] Query returned {len(docs)} documents")
            if distances:
                logger.info(f"[RAG] Distances: {distances}")
            
            if not docs:
                yield {"type": "status", "content": "⚠️ Bağlam bulunamadı, genel bilgi kullanılıyor..."}
                context_text = "Seçili dökümanlarda bu konuyla ilgili bilgi bulunamadı."
            else:
                context_text = "\n\n".join(docs)
                
            # 2. Extract sources
            sources = list(set([m.get("source", "Bilinmeyen") for m in metadatas]))
            if sources:
                yield {"type": "sources", "content": sources}

            # 3. Pull preferences
            prefs = self.db.get_preferences()
            pref_instructions = self._format_prefs(prefs)

            # 4. Prepare Chain
            llm = self._get_llm(streaming=True)
            prompt = ChatPromptTemplate.from_messages([
                ("system", PromptTemplates.SYSTEM_IDENTITY),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", PromptTemplates.RAG_CONTEXT_TEMPLATE)
            ])
            
            chain = prompt | llm | StrOutputParser()
            
            # 5. Execute Stream
            history = self.cache.to_langchain()
            full_response = ""
            
            yield {"type": "status", "content": "🧠 Yanıt oluşturuluyor..."}
            
            for token in chain.stream({
                "chat_history": history,
                "context": context_text,
                "question": question,
                "preferences": pref_instructions
            }):
                full_response += token
                yield {"type": "token", "content": token}

            # 6. Save interactions
            user_msg = Message(role="user", content=question, workspace_id=self.workspace_id)
            ai_msg = Message(role="assistant", content=full_response, 
                             workspace_id=self.workspace_id, sources=sources)
            
            self.db.add_message(user_msg)
            self.db.add_message(ai_msg)
            self.cache.add(user_msg)
            self.cache.add(ai_msg)
            
        except Exception as e:
            logger.error(f"RAG stream error: {e}")
            yield {"type": "error", "content": str(e)}

    def clear_history(self) -> None:
        """Wipe conversation history for this workspace."""
        self.db.clear_messages(self.workspace_id)
        self.cache.clear()
        logger.info(f"Chat history cleared for workspace {self.workspace_id}")
