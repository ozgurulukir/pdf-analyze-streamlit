"""Chroma vector store manager with Ollama/HuggingFace embeddings."""
import re
from typing import List, Optional, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
import streamlit as st

from app.core.models import FileMetadata, ChunkMetadata
from app.core.config import AppConfig


class ChromaManager:
    """Manages Chroma collections for workspaces."""

    def __init__(self, persist_directory: str = "data/chroma"):
        self.persist_directory = persist_directory
        self._client = None

    @property
    def client(self):
        """Get or create Chroma client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize workspace name for collection naming."""
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        return sanitized.lower()[:50]

    def get_collection_name(self, workspace_id: str, workspace_name: str) -> str:
        """Generate a unique collection name for a workspace."""
        sanitized = self.sanitize_name(workspace_name)
        return f"ws_{workspace_id[:8]}_{sanitized}"

    def get_or_create_collection(self, workspace_id: str, workspace_name: str):
        """Get or create a Chroma collection for a workspace."""
        collection_name = self.get_collection_name(workspace_id, workspace_name)
        
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"workspace_id": workspace_id, "workspace_name": workspace_name}
            )
        
        return collection

    def get_collection(self, workspace_id: str, workspace_name: str):
        """Get an existing collection."""
        collection_name = self.get_collection_name(workspace_id, workspace_name)
        try:
            return self.client.get_collection(name=collection_name)
        except Exception:
            return None

    def delete_collection(self, workspace_id: str, workspace_name: str):
        """Delete a workspace's collection."""
        collection_name = self.get_collection_name(workspace_id, workspace_name)
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass

    def add_chunks(
        self,
        workspace_id: str,
        workspace_name: str,
        file_id: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ) -> List[str]:
        """Add chunks to a workspace's collection."""
        collection = self.get_or_create_collection(workspace_id, workspace_name)
        
        # Generate deterministic IDs
        ids = [f"{workspace_id}_{file_id}_{i}" for i in range(len(chunks))]
        
        metadatas = [
            {
                "workspace_id": workspace_id,
                "file_id": file_id,
                "chunk_index": i,
                "text_preview": chunk[:100]
            }
            for i, chunk in enumerate(chunks)
        ]
        
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        return ids

    def query(
        self,
        workspace_id: str,
        workspace_name: str,
        query_embedding: List[float],
        n_results: int = 4,
        where: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[List[str]], List[List[float]], List[Dict]]:
        """Query the workspace collection."""
        collection = self.get_collection(workspace_id, workspace_name)
        
        if collection is None:
            return [], [], []
        
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

    def delete_file_chunks(self, workspace_id: str, workspace_name: str, file_id: str):
        """Delete all chunks associated with a file."""
        collection = self.get_collection(workspace_id, workspace_name)
        
        if collection is None:
            return
        
        try:
            results = collection.get(where={"file_id": file_id})
            if results and results.get("ids"):
                collection.delete(ids=results["ids"])
        except Exception:
            pass

    def get_chunk_count(self, workspace_id: str, workspace_name: str) -> int:
        """Get the total number of chunks in a workspace."""
        collection = self.get_collection(workspace_id, workspace_name)
        
        if collection is None:
            return 0
        
        try:
            return collection.count()
        except Exception:
            return 0

    def delete_workspace_data(self, workspace_id: str, workspace_name: str):
        """Delete all data for a workspace."""
        self.delete_collection(workspace_id, workspace_name)


class EmbeddingManager:
    """Manages text embeddings - supports Ollama and HuggingFace."""

    def __init__(
        self,
        use_huggingface: bool = False,
        ollama_model: str = "nomic-embed-text",
        ollama_url: str = "http://localhost:11434",
        hf_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.use_huggingface = use_huggingface
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        self.hf_model = hf_model

    def get_embeddings_model(self):
        """Get the LangChain embeddings model instance."""
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

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        model = self.get_embeddings_model()
        return model.embed_documents(texts)

    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query."""
        model = self.get_embeddings_model()
        return model.embed_query(query)


class ChunkManager:
    """Manages text chunking."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        return splitter.split_text(text)

    def chunk_document(self, document) -> List[str]:
        """Chunk a LangChain document."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        return splitter.split_documents([document])
