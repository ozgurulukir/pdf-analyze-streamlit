"""RAG chain and QA functionality with custom LLM support."""
from typing import List, Optional, Dict, Any, Tuple
import streamlit as st

from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.models import Message, QAPair, UserPreferences
from app.core.database import DatabaseManager
from app.core.config import AppConfig


def create_llm(
    base_url: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    streaming: bool = True
):
    """Create OpenAI-compatible LLM."""
    from langchain_openai import ChatOpenAI
    
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        streaming=streaming,
        max_tokens=4096
    )


def get_settings_from_session():
    """Get settings from Streamlit session state."""
    return {
        "base_url": st.session_state.get("llm_base_url", "https://ollama.com/v1"),
        "api_key": st.session_state.get("llm_api_key", "ollama"),
        "model": st.session_state.get("llm_model", "deepseek-v2:671b"),
        "temperature": st.session_state.get("llm_temperature", 0.3),
        "use_huggingface": st.session_state.get("use_huggingface", False),
        "embed_model": st.session_state.get("embed_model", "nomic-embed-text"),
        "ollama_url": st.session_state.get("ollama_url", "http://localhost:11434"),
        "hf_embed_model": st.session_state.get("hf_embed_model", "sentence-transformers/all-MiniLM-L6-v2"),
        "chunk_size": st.session_state.get("chunk_size", 1000),
        "chunk_overlap": st.session_state.get("chunk_overlap", 200),
    }


class RAGChain:
    """Retrieval-Augmented Generation chain."""

    def __init__(
        self,
        config: AppConfig = None,
        base_url: str = None,
        api_key: str = None,
        model: str = None,
        temperature: float = 0.3
    ):
        self.config = config or AppConfig()
        
        # Get settings from session state if available, otherwise use config/params
        session_settings = get_settings_from_session()
        
        # LLM settings - prefer session state
        self.base_url = base_url or session_settings["base_url"]
        self.api_key = api_key or session_settings["api_key"]
        self.model = model or session_settings["model"]
        self.temperature = temperature or session_settings["temperature"]
        
        # Embedding settings from session
        self.use_huggingface = session_settings["use_huggingface"]
        self.embed_model = session_settings["embed_model"]
        self.ollama_url = session_settings["ollama_url"]
        self.hf_embed_model = session_settings["hf_embed_model"]
        
        # Chroma manager
        self.chroma_manager = ChromaManager()

    def query(
        self,
        question: str,
        workspace_id: str,
        workspace_name: str,
        preferences: UserPreferences = None,
        k: int = 4
    ) -> Tuple[str, List[str]]:
        """Query the RAG system using LCEL chain."""
        
        # Get embeddings model
        embedding_manager = EmbeddingManager(
            use_huggingface=self.use_huggingface,
            ollama_model=self.embed_model,
            ollama_url=self.ollama_url,
            hf_model=self.hf_embed_model
        )
        
        # Get vectorstore via langchain-chroma
        from langchain_chroma import Chroma
        vectorstore = Chroma(
            client=self.chroma_manager.client,
            collection_name=self.chroma_manager.get_collection_name(workspace_id, workspace_name),
            embedding_function=embedding_manager.get_embeddings_model()
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Create LLM
        llm = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            streaming=True
        )
        
        # Build prompt
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser

        template = """Sen profesyonel bir belge analiz asistanısın. 
Aşağıdaki belgelerden alınan bağlamı kullanarak soruyu en doğru ve anlaşılır şekilde cevapla.

Kurallar:
1. Sadece verilen bağlamdaki bilgileri kullan. Bağlam dışına çıkma.
2. Eğer cevap belgelerde yoksa, "Verilen belgelerde bu konuyla ilgili bilgi bulamadım" de.
3. Cevaplarını her zaman Türkçe ver.
4. Kaynaklara atıfta bulun (örn. "Belgede belirtildiği üzere...").
5. Dürüst ol, eksik bilgi varsa belirt.

Bağlam:
{context}

Soru: {question}

Cevap:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # LCEL Chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        try:
            # For streaming support in Streamlit, we might need to handle this differently
            # but for a standard call:
            answer = rag_chain.invoke(question)
            
            # Get supporting docs for sources
            docs = retriever.invoke(question)
            sources = list(set(doc.metadata.get("source", "Bilinmeyen") for doc in docs))
            
            return answer, sources
        except Exception as e:
            return f"Sorgu sırasında bir hata oluştu: {str(e)}", []


class PreferenceManager:
    """Manages user preferences for responses."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_preferences(self) -> UserPreferences:
        """Get current preferences."""
        return self.db.get_preferences()

    def adjust_preference(self, tag: str, delta: float):
        """Adjust a preference weight."""
        prefs = self.db.get_preferences()
        prefs.adjust_weight(tag, delta)
        self.db.save_preferences(prefs)


class MessageCache:
    """LRU cache for chat messages."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._messages: List[Message] = []

    def add(self, message: Message):
        """Add a message to cache."""
        self._messages.append(message)
        
        if len(self._messages) > self.max_size:
            excess = len(self._messages) - self.max_size
            for i in range(excess):
                if i < len(self._messages):
                    self._messages[i].is_summarized = True
            
            self._messages = self._messages[excess:]

    def get_all(self) -> List[Message]:
        return self._messages

    def get_recent(self, n: int = 10) -> List[Message]:
        return self._messages[-n:]

    def clear(self):
        self._messages.clear()


class QAManager:
    """Manages Q&A pairs and dashboard."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_qa_pair(
        self,
        workspace_id: str,
        file_ids: List[str],
        question: str,
        answer: str
    ) -> QAPair:
        """Create a new Q&A pair."""
        qa = QAPair(
            workspace_id=workspace_id,
            file_ids=file_ids,
            question=question,
            answer=answer
        )
        return self.db.create_qa_pair(qa)

    def get_qa_pairs(self, workspace_id: Optional[str] = None) -> List[QAPair]:
        return self.db.get_qa_pairs(workspace_id)

    def like(self, qa_id: str):
        qa_pairs = self.db.get_qa_pairs()
        for qa in qa_pairs:
            if qa.id == qa_id:
                qa.likes += 1
                self.db.update_qa_votes(qa_id, qa.likes, qa.dislikes)
                break

    def dislike(self, qa_id: str):
        qa_pairs = self.db.get_qa_pairs()
        for qa in qa_pairs:
            if qa.id == qa_id:
                qa.dislikes += 1
                self.db.update_qa_votes(qa_id, qa.likes, qa.dislikes)
                break
