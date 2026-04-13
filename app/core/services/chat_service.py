from collections.abc import Generator
from typing import Any, cast

from app.core.cache import (
    cached_chroma_query,
    cached_get_embedding,
    cached_get_messages,
    get_cached_chroma_manager,
    get_cached_database_manager,
    get_cached_embedding_manager,
    get_llm_response_cache,
    invalidate_workspace_cache,
    text_hash,
)
from app.core.chroma import ChromaManager, EmbeddingManager
from app.core.config import AppConfig
from app.core.database import DatabaseManager
from app.core.exceptions import AppError, ChromaError, LLMError
from app.core.logger import logger
from app.core.models import Workspace
from app.core.rag import RAGChain


class ChatService:
    """
    ChatService orchestrates RAG interactions with caching support.

    It decouples the UI from the underlying RAG chain implementation
    and provides intelligent caching for embeddings and queries.
    """

    def __init__(
        self,
        db: DatabaseManager | None = None,
        chroma: ChromaManager | None = None,
        embedding: EmbeddingManager | None = None,
        config: AppConfig | None = None,
        use_cache: bool = True,
    ):
        """
        Initialize the chat service with optional caching.

        Args:
            db: Database manager (uses cached if None)
            chroma: Chroma manager (uses cached if None)
            embedding: Embedding manager (uses cached if None)
            config: Application configuration
            use_cache: Whether to use caching (default: True)
        """
        self.use_cache = use_cache
        from app.core.container import get_config
        self.config = config or get_config()

        # Use cached managers if not provided
        if db is None:
            self.db = get_cached_database_manager()
        else:
            self.db = db

        if chroma is None and use_cache:
            self.chroma = get_cached_chroma_manager()
        else:
            self.chroma = chroma

        if embedding is None and use_cache:
            # Default embedding manager - will be replaced by config
            self._default_embedding = get_cached_embedding_manager()
            self.embedding = self._default_embedding
        else:
            self.embedding = embedding

        self._llm_config: dict[str, object] = {}
        self._workspace_id: str | None = None

    def configure_embedding(
        self,
        use_huggingface: bool = False,
        ollama_model: str = "nomic-embed-text",
        ollama_url: str = "http://localhost:11434",
        hf_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        """
        Configure the embedding manager with specific settings.

        Args:
            use_huggingface: Whether to use HuggingFace embeddings
            ollama_model: Ollama model name
            ollama_url: Ollama server URL
            hf_model: HuggingFace model name
        """
        if self.use_cache:
            self.embedding = get_cached_embedding_manager(
                use_huggingface=use_huggingface,
                ollama_model=ollama_model,
                ollama_url=ollama_url,
                hf_model=hf_model,
            )
        else:
            self.embedding = EmbeddingManager(
                use_huggingface=use_huggingface,
                ollama_model=ollama_model,
                ollama_url=ollama_url,
                hf_model=hf_model,
            )
        logger.debug(
            f"Embedding manager configured: hf={use_huggingface}, model={ollama_model}"
        )

    def get_cached_embedding(self, text: str) -> list[float]:
        """
        Get embedding for text, using cache if enabled.

        Returns:
            List of floats representing the embedding vector
        """
        if self.embedding is None:
            raise AppError("Embedding manager not initialized")

        if not self.use_cache:
            emb: Any = self.embedding.get_query_embedding(text)
            return cast(list[float], emb)

        # Use cached embedding
        text_hash_key = text_hash(text)
        result: Any = cached_get_embedding(text_hash_key, text, self.embedding)
        return cast(list[float], result)

    def get_cached_chroma_query(
        self,
        workspace_id: str,
        workspace_name: str,
        query_embedding: list[float],
        n_results: int | None = None,
    ) -> dict[str, object]:
        """
        Perform cached ChromaDB similarity search.

        Args:
            workspace_id: Workspace ID
            workspace_name: Workspace name
            query_embedding: Query vector
            n_results: Number of results (uses config if None)

        Returns:
            Dict with documents, distances, and metadatas
        """
        n_results = n_results or self.config.DEFAULT_RETRIEVER_K
        if self.chroma is None:
             raise ChromaError("Chroma manager not initialized")

        if not self.use_cache:
            docs, distances, metadatas = self.chroma.query(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                query_embedding=query_embedding,
                n_results=n_results,
            )
            return {"documents": docs, "distances": distances, "metadatas": metadatas}

        # Create hash of query embedding for cache key
        import hashlib

        query_hash = hashlib.md5(str(query_embedding[:10]).encode()).hexdigest()[:16]

        return cached_chroma_query(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            query_hash=query_hash,
            n_results=n_results,
            _chroma_manager=self.chroma,
            _query_embedding=query_embedding,
        )

    def stream_response(
        self, question: str, workspace: Workspace, llm_config: dict[str, Any], session_id: str | None = None
    ) -> Generator[dict[str, Any], None, None]:
        """
        Get a streaming AI response for a question using RAG.

        Uses caching for embeddings and ChromaDB queries when enabled.

        Args:
            question: The user's query
            workspace: The active workspace object
            llm_config: Configuration for the LLM (model, api_key, etc.)

        Yields:
            Dict: RAG events (token, status, source, etc.)
        """
        try:
            # Check LLM response cache first
            llm_cache = None
            cache_key = ""
            if self.use_cache:
                llm_cache = get_llm_response_cache()
                cache_key = f"{workspace.id}_{text_hash(question)}"
                cached_response = llm_cache.get(cache_key)

                if cached_response:
                    logger.info(
                        f"LLM cache hit for question in workspace {workspace.id}"
                    )
                    yield {"type": "status", "content": "📦 Önbellekten yükleniyor..."}
                    yield {"type": "cached", "content": cached_response}
                    return

            # Configure embedding if settings changed
            embedding_config = cast(dict[str, object], llm_config.get("embedding", {}))
            if embedding_config:
                self.configure_embedding(
                    use_huggingface=cast(bool, embedding_config.get("use_huggingface", False)),
                    ollama_model=cast(str, embedding_config.get("model", "nomic-embed-text")),
                    ollama_url=cast(str, embedding_config.get(
                        "ollama_url", "http://localhost:11434"
                    )),
                    hf_model=cast(str, embedding_config.get(
                        "hf_model", "sentence-transformers/all-MiniLM-L6-v2"
                    )),
                )

            # Ensure managers are initialized
            if self.db is None or self.chroma is None or self.embedding is None:
                raise AppError("Sistem bileşenleri başlatılamadı (DB/Chroma/Embedding)")

            # Initialize RAG chain with required components
            rag_chain = RAGChain(
                db=self.db,
                chroma=self.chroma,
                embedding=self.embedding,
                llm_config=llm_config,
                workspace_id=workspace.id,
                session_id=session_id,
                config=self.config,
            )

            # Collect response for caching
            full_response = ""

            for event in rag_chain.stream_query(question=question):
                if event.get("type") == "token":
                    full_response += event.get("content", "")
                yield event

            # Cache the complete response
            if self.use_cache and full_response and llm_cache and cache_key:
                llm_cache.set(
                    cache_key, full_response, ttl=self.config.CHAT_CACHE_TTL
                )
                logger.debug(f"Cached LLM response for workspace {workspace.id}")

        except (LLMError, ChromaError, AppError) as e:
            logger.error(f"ChatService error: {e}")
            yield {"type": "error", "content": str(e)}
        except Exception as e:
            logger.critical(f"Unexpected error in ChatService: {e}")
            yield {
                "type": "error",
                "content": f"Beklenmedik bir hata oluştu: {str(e)}",
            }

    def get_chat_history(
        self, workspace_id: str, limit: int | None = None
    ) -> list[dict[str, object]]:
        """
        Get chat history for a workspace with caching.

        Args:
            workspace_id: Workspace ID
            limit: Maximum number of messages (uses config if None)

        Returns:
            List of message dictionaries
        """
        limit = limit or self.config.DEFAULT_CHAT_LIMIT
        if self.use_cache:
            return cast(list[dict[str, object]], cached_get_messages(workspace_id, limit))
        else:
            messages = self.db.messages.get_by_workspace(workspace_id, limit=limit)
            return [m.to_dict() if hasattr(m, "to_dict") else cast(dict[str, object], m) for m in messages]

    def clear_workspace_history(self, workspace_id: str) -> None:
        """
        Wipe chat history for a specific workspace and invalidate cache.

        Args:
            workspace_id: Workspace ID to clear
        """
        try:
            self.db.messages.clear_by_workspace(workspace_id)

            # Invalidate caches
            if self.use_cache:
                cached_get_messages.clear(workspace_id)
                invalidate_workspace_cache(workspace_id)

            logger.info(f"Chat history cleared for workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to clear history for workspace {workspace_id}: {e}")
            raise

    def get_workspace_stats(self, workspace_id: str) -> dict[str, object]:
        """
        Get statistics for a workspace with caching.

        Args:
            workspace_id: Workspace ID

        Returns:
            Dict with workspace statistics
        """
        workspace = self.db.workspaces.get_by_id(workspace_id)
        if not workspace:
            return {}

        messages = self.get_chat_history(workspace_id, limit=self.config.MAX_HISTORY_LIMIT)
        files_data = self.db.files.get_by_workspace(workspace_id)

        return {
            "workspace_id": workspace_id,
            "workspace_name": workspace.name,
            "file_count": len(files_data),
            "message_count": len(messages),
            "total_chunks": sum(f.chunk_count or 0 for f in files_data),
            "last_modified": workspace.last_modified.isoformat()
            if workspace.last_modified
            else None,
        }


def get_cached_chat_service(
    use_huggingface: bool = False,
    ollama_model: str = "nomic-embed-text",
    ollama_url: str = "http://localhost:11434",
    hf_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> ChatService:
    """
    Factory function to create a cached ChatService instance.

    Args:
        use_huggingface: Whether to use HuggingFace embeddings
        ollama_model: Ollama model name
        ollama_url: Ollama server URL
        hf_model: HuggingFace model name

    Returns:
        Configured ChatService instance with caching enabled
    """
    service = ChatService(use_cache=True)
    service.configure_embedding(
        use_huggingface=use_huggingface,
        ollama_model=ollama_model,
        ollama_url=ollama_url,
        hf_model=hf_model,
    )
    return service
