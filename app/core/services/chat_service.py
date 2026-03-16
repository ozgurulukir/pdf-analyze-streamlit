"""Service layer for chat and RAG operations."""
from typing import Dict, Any, Generator, Optional, List
from app.core.rag import RAGChain
from app.core.models import Workspace
from app.core.database import DatabaseManager
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.logger import logger
from app.core.exceptions import LLMError, ChromaError


class ChatService:
    """
    ChatService orchestrates RAG interactions.
    
    It decouples the UI from the underlying RAG chain implementation.
    """
    
    def __init__(
        self, 
        db: DatabaseManager, 
        chroma: ChromaManager, 
        embedding: EmbeddingManager
    ):
        """
        Initialize the chat service.
        
        Args:
            db: Database manager for persistence
            chroma: Chroma manager for vector retrieval
            embedding: Embedding manager for text vectorization
        """
        self.db = db
        self.chroma = chroma
        self.embedding = embedding

    def stream_response(
        self,
        question: str,
        workspace: Workspace,
        llm_config: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get a streaming AI response for a question using RAG.
        
        Args:
            question: The user's query
            workspace: The active workspace object
            llm_config: Configuration for the LLM (model, api_key, etc.)
            
        Yields:
            Dict: RAG events (token, status, source, etc.)
        """
        try:
            # Initialize RAG chain with required components
            rag_chain = RAGChain(
                db=self.db,
                chroma=self.chroma,
                embedding=self.embedding,
                llm_config=llm_config,
                workspace_id=workspace.id
            )
            
            yield from rag_chain.stream_query(question=question)
            
        except (LLMError, ChromaError) as e:
            logger.error(f"ChatService error: {e}")
            yield {"type": "error", "content": str(e)}
        except Exception as e:
            logger.critical(f"Unexpected error in ChatService: {e}")
            yield {"type": "error", "content": "Kritik bir hata oluştu. Lütfen sistem loglarını kontrol edin."}

    def clear_workspace_history(self, workspace_id: str) -> None:
        """
        Wipe chat history for a specific workspace.
        """
        try:
            self.db.clear_messages(workspace_id)
            logger.info(f"Chat history cleared for workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to clear history for workspace {workspace_id}: {e}")
            raise
