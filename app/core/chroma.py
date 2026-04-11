"""Chroma vector store manager with Ollama/HuggingFace embeddings."""
import re
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from app.core.config import AppConfig
from app.core.exceptions import ChromaError
from app.core.logger import logger


class ChromaManager:
    """
    Manages ChromaDB collections for semantic search.

    Responsible for collection lifecycle (create, get, delete),
    chunk ingestion, and similarity querying.
    """

    def __init__(self, persist_directory: str | None = None):
        """
        Initialize the Chroma manager.

        Args:
            persist_directory: Local path to store the vector database
        """
        if persist_directory is None:
            persist_directory = AppConfig().CHROMA_PERSIST_DIR
        self.persist_directory = persist_directory
        self._client: chromadb.PersistentClient | None = None

    @property
    def client(self) -> chromadb.PersistentClient:
        """
        Get or initialize the persistent Chroma client.

        Returns:
            chromadb.PersistentClient: The initialized client
        """
        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            except Exception as e:
                logger.error(f"Failed to initialize Chroma client: {e}")
                raise ChromaError(f"Chroma client initialization failed: {e}")
        return self._client

    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize workspace name for Chroma collection naming requirements.

        Rules: 3-63 chars, alphanumeric, underscore or hyphen.

        Args:
            name: The raw workspace name

        Returns:
            str: Sanitized collection name segment
        """
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        # Ensure it complies with length and character requirements
        return sanitized.lower()[:50]

    def get_collection_name(self, workspace_id: str, workspace_name: str) -> str:
        """
        Generate a unique and compliant collection name for a workspace.

        Args:
            workspace_id: Unique ID of the workspace
            workspace_name: Human-readable name of the workspace

        Returns:
            str: Prefixed and sanitized collection name
        """
        sanitized = self.sanitize_name(workspace_name)
        return f"ws_{workspace_id[:8]}_{sanitized}"

    def get_or_create_collection(self, workspace_id: str, workspace_name: str) -> Collection:
        """
        Retrieve existing or create new collection for a workspace.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace

        Returns:
            Collection: The Chroma collection object

        Raises:
            ChromaError: If creation or retrieval fails
        """
        collection_name = collection_name = collection_name = self.get_collection_name(workspace_id, workspace_name)

        try:
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"workspace_id": workspace_id, "workspace_name": workspace_name}
            )
        except Exception as e:
            logger.error(f"Failed to get/create collection {collection_name}: {e}")
            raise ChromaError(f"Collection operation failed: {e}")

    def get_collection(self, workspace_id: str, workspace_name: str) -> Collection | None:
        """
        Retrieve an existing collection without creating it.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace

        Returns:
            Optional[Collection]: The collection if it exists, else None
        """
        collection_name = collection_name = collection_name = self.get_collection_name(workspace_id, workspace_name)
        try:
            return self.client.get_collection(name=collection_name)
        except Exception:
            return None

    def delete_collection(self, workspace_id: str, workspace_name: str) -> None:
        """
        Delete a workspace's vector collection.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace

        Raises:
            ChromaError: If deletion fails for reasons other than non-existence
        """
        collection_name = collection_name = collection_name = self.get_collection_name(workspace_id, workspace_name)
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted vector collection: {collection_name}")
        except Exception as e:
            # If it doesn't exist, we don't care. Otherwise log it.
            if "does not exist" not in str(e).lower():
                logger.warning(f"Failed to delete collection {collection_name}: {e}")

    def add_chunks(
        self,
        workspace_id: str,
        workspace_name: str,
        file_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
        source: str | None = None
    ) -> list[str]:
        """
        Add text chunks and their embeddings to the workspace collection.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace
            file_id: ID of the source file
            chunks: List of text content snippets
            embeddings: Corresponding vector embeddings
            source: Human-readable source description

        Returns:
            List[str]: The generated IDs for the indexed chunks

        Raises:
            ChromaError: If ingestion fails
        """
        collection = self.get_or_create_collection(workspace_id, workspace_name)

        # Generate deterministic IDs
        ids = [f"{workspace_id}_{file_id}_{i}" for i in range(len(chunks))]

        metadatas = [
            {
                "workspace_id": workspace_id,
                "file_id": file_id,
                "chunk_index": i,
                "text_preview": chunk[:100],
                "source": source or "Bilinmeyen"
            }
            for i, chunk in enumerate(chunks)
        ]

        try:
            collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"[Chroma] Added {len(chunks)} chunks to collection {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Failed to add chunks to Chroma for file {file_id}: {e}")
            raise ChromaError(f"Data ingestion failed: {e}")

    def query(
        self,
        workspace_id: str,
        workspace_name: str,
        query_embedding: list[float],
        n_results: int = 4,
        where: dict[str, Any] | None = None
    ) -> tuple[list[str], list[float], list[dict[str, Any]]]:
        """
        Perform a similarity search in the workspace collection.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace
            query_embedding: Vector embedding of the query
            n_results: Number of nearest neighbors to return
            where: Metadata filter dictionary

        Returns:
            Tuple containing (documents, distances, metadatas)
        """
        collection_name = self.get_collection_name(workspace_id, workspace_name)
        logger.info(f"[Chroma] Looking for collection: {collection_name}")

        # List all available collections
        try:
            all_collections = self.client.list_collections()
            logger.info(f"[Chroma] Available collections: {[c.name for c in all_collections]}")
        except Exception as e:
            logger.error(f"[Chroma] Failed to list collections: {e}")

        collection = self.get_collection(workspace_id, workspace_name)

        if collection is None:
            logger.warning(f"[Chroma] Collection not found: {collection_name}")
            return [], [], []

        logger.info(f"[Chroma] Collection found: {collection_name}, count: {collection.count()}")

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "distances", "metadatas"]
            )

            return (
                results.get("documents", [[]])[0],
                results.get("distances", [[]])[0],
                results.get("metadatas", [[]])[0]
            )
        except Exception as e:
            logger.error(f"Query failed for workspace {workspace_id}: {e}")
            return [], [], []

    def delete_file_chunks(self, workspace_id: str, workspace_name: str, file_id: str) -> None:
        """
        Remove all vectors associated with a specific file.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace
            file_id: ID of the file whose chunks should be removed
        """
        collection = self.get_collection(workspace_id, workspace_name)

        if collection is None:
            return

        try:
            results = collection.get(where={"file_id": file_id})
            if results and results.get("ids"):
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for file {file_id}")
        except Exception as e:
            logger.warning(f"Failed to delete chunks for file {file_id}: {e}")

    def get_chunk_count(self, workspace_id: str, workspace_name: str) -> int:
        """
        Get the current size of the workspace collection.

        Args:
            workspace_id: ID of the workspace
            workspace_name: Name of the workspace

        Returns:
            int: Number of items in the collection
        """
        collection = self.get_collection(workspace_id, workspace_name)

        if collection is None:
            return 0

        try:
            return collection.count()
        except Exception:
            return 0

    def delete_workspace_data(self, workspace_id: str, workspace_name: str) -> None:
        """
        Clean up all vector data for a workspace.

        Args:
            workspace_id: Workspace ID
            workspace_name: Workspace Name
        """
        self.delete_collection(workspace_id, workspace_name)

    def hard_reset(self) -> bool:
        """
        Wipe the entire vector database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.reset()
            logger.critical("Vector store hard reset performed")
            return True
        except Exception as e:
            logger.error(f"Hard reset failed: {e}")
            return False


class EmbeddingManager:
    """
    Manages generation of text embeddings using various providers.

    Supports Local Ollama and HuggingFace models.
    """

    def __init__(
        self,
        use_huggingface: bool = False,
        ollama_model: str = "nomic-embed-text",
        ollama_url: str = "http://localhost:11434",
        hf_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the embedding manager.
        """
        self.use_huggingface = use_huggingface
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        self.hf_model = hf_model

    def get_embeddings_model(self) -> Any:
        """
        Initialize and return the appropriate LangChain embedding instance.

        Returns:
            The embedding model instance
        """
        try:
            if self.use_huggingface:
                from langchain_huggingface import HuggingFaceEmbeddings
                return HuggingFaceEmbeddings(
                    model_name=self.hf_model,
                    model_kwargs={'device': 'cpu'}
                )
            else:
                from langchain_ollama import OllamaEmbeddings
                return OllamaEmbeddings(
                    model=self.ollama_model,
                    base_url=self.ollama_url
                )
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise ChromaError(f"Embedding initialization failed: {e}")

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of documents.

        Args:
            texts: List of strings to encode

        Returns:
            List of vectors
        """
        model = self.get_embeddings_model()
        return model.embed_documents(texts)

    def get_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a single search query.

        Args:
            query: The user query string

        Returns:
            The query vector
        """
        model = self.get_embeddings_model()
        return model.embed_query(query)


class ChunkManager:
    """
    Handles text splitting and semantic chunking strategies.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the chunk manager with size and overlap.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """
        Split a block of text into smaller context windows.

        Prioritizes splitting at paragraphs, then sentences, then whitespace.

        Args:
            text: The raw source text

        Returns:
            List[str]: List of text chunks
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )

        return splitter.split_text(text)

    def chunk_document(self, document: Any) -> list[Any]:
        """
        Split a LangChain document object into multiple documents.

        Args:
            document: A LangChain Document object

        Returns:
            List: List of fragmented Document objects
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )

        return splitter.split_documents([document])
