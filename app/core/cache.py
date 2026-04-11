"""Caching layer with Streamlit integration for improved performance."""

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, TypeVar

import streamlit as st

from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


# ===================
# Cache Entry & LRU Cache
# ===================


@dataclass
class CacheEntry:
    """Represents a cache entry with expiration."""

    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache implementation.

    Features:
    - Maximum size limit
    - TTL (Time To Live) for entries
    - Thread-safe operations
    - Statistics tracking
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize the LRU cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats["hits"] += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1

            ttl = ttl if ttl is not None else self._default_ttl
            now = datetime.now()

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
            )

            self._cache[key] = entry

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": round(hit_rate, 3),
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
            }


# ===================
# Global Cache Instances
# ===================

_message_cache: Optional[LRUCache] = None
_embedding_cache: Optional[LRUCache] = None
_llm_response_cache: Optional[LRUCache] = None
_query_cache: Optional[LRUCache] = None


def get_message_cache() -> LRUCache:
    """Get the global message cache (TTL: 1 hour)."""
    global _message_cache
    if _message_cache is None:
        _message_cache = LRUCache(max_size=500, default_ttl=3600)
    return _message_cache


def get_embedding_cache() -> LRUCache:
    """Get the global embedding cache (TTL: 24 hours)."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = LRUCache(max_size=1000, default_ttl=86400)
    return _embedding_cache


def get_llm_response_cache() -> LRUCache:
    """Get the global LLM response cache (TTL: 30 minutes)."""
    global _llm_response_cache
    if _llm_response_cache is None:
        _llm_response_cache = LRUCache(max_size=200, default_ttl=1800)
    return _llm_response_cache


def get_query_cache() -> LRUCache:
    """Get the global database query cache (TTL: 5 minutes)."""
    global _query_cache
    if _query_cache is None:
        _query_cache = LRUCache(max_size=300, default_ttl=300)
    return _query_cache


# ===================
# Cache Decorators
# ===================


def cached(
    cache: LRUCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
):
    """
    Decorator to cache function results in LRU cache.

    Args:
        cache: Cache instance to use
        key_func: Function to generate cache key from args
        ttl: Time-to-live for cached results
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = json.dumps(
                    {"args": str(args), "kwargs": str(kwargs)}, sort_keys=True
                )
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")

            return result

        return wrapper

    return decorator


# ===================
# Streamlit Cache Integration
# ===================


@st.cache_resource
def get_cached_database_manager():
    """
    Get cached DatabaseManager instance (singleton via Streamlit).
    Use this for resource-heavy objects that should be created once.
    """
    from app.core.database import DatabaseManager

    logger.debug("Creating cached DatabaseManager instance")
    return DatabaseManager()


@st.cache_resource
def get_cached_chroma_manager(_config: Dict[str, Any] = None):
    """
    Get cached ChromaManager instance (singleton via Streamlit).

    Args:
        _config: Configuration dict (underscore prefix prevents hashing issues)
    """
    from app.core.chroma import ChromaManager

    logger.debug("Creating cached ChromaManager instance")
    persist_dir = _config.get("chroma_path") if _config else None
    return ChromaManager(persist_directory=persist_dir)


@st.cache_resource
def get_cached_embedding_manager(
    use_huggingface: bool = False,
    ollama_model: str = "nomic-embed-text",
    ollama_url: str = "http://localhost:11434",
    hf_model: str = "sentence-transformers/all-MiniLM-L6-v2",
):
    """
    Get cached EmbeddingManager instance (singleton via Streamlit).
    """
    from app.core.chroma import EmbeddingManager

    logger.debug("Creating cached EmbeddingManager instance")
    return EmbeddingManager(
        use_huggingface=use_huggingface,
        ollama_model=ollama_model,
        ollama_url=ollama_url,
        hf_model=hf_model,
    )


# ===================
# Data Caching with Streamlit
# ===================


@st.cache_data(ttl=300, max_entries=100)
def cached_get_workspaces() -> List[Dict[str, Any]]:
    """
    Get all workspaces (cached for 5 minutes).
    Returns list of workspace dicts for better serialization.
    """
    from app.core.database import DatabaseManager

    db = DatabaseManager()
    workspaces = db.get_workspaces()
    return [w.to_dict() if hasattr(w, "to_dict") else w for w in workspaces]


@st.cache_data(ttl=60, max_entries=50)
def cached_get_workspace_files(workspace_id: str) -> List[Dict[str, Any]]:
    """
    Get files for a workspace (cached for 1 minute).

    Args:
        workspace_id: Workspace ID to get files for
    """
    from app.core.database import DatabaseManager

    db = DatabaseManager()
    files = db.get_files(workspace_id)
    return [f.to_dict() if hasattr(f, "to_dict") else f for f in files]


@st.cache_data(ttl=120, max_entries=30)
def cached_get_messages(workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get chat messages for a workspace (cached for 2 minutes).

    Args:
        workspace_id: Workspace ID
        limit: Maximum number of messages
    """
    from app.core.database import DatabaseManager

    db = DatabaseManager()
    messages = db.get_messages(workspace_id, limit=limit)
    return [m.to_dict() if hasattr(m, "to_dict") else m for m in messages]


@st.cache_data(ttl=3600, max_entries=500)
def cached_get_embedding(
    text_hash: str, text: str, _embedding_manager: Any
) -> List[float]:
    """
    Get embedding for text (cached for 1 hour).

    Args:
        text_hash: Hash of the text (for cache key)
        text: Actual text to embed
        _embedding_manager: EmbeddingManager instance (not hashed)
    """
    return _embedding_manager.get_query_embedding(text)


@st.cache_data(ttl=1800, max_entries=100)
def cached_chroma_query(
    workspace_id: str,
    workspace_name: str,
    query_hash: str,
    n_results: int,
    _chroma_manager: Any,
    _query_embedding: List[float],
) -> Dict[str, Any]:
    """
    Cached ChromaDB similarity search (30 minutes TTL).

    Args:
        workspace_id: Workspace ID
        workspace_name: Workspace name
        query_hash: Hash of the query for cache key
        n_results: Number of results
        _chroma_manager: ChromaManager (not hashed)
        _query_embedding: Query embedding (not hashed, use query_hash instead)
    """
    docs, distances, metadatas = _chroma_manager.query(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        query_embedding=_query_embedding,
        n_results=n_results,
    )
    return {"documents": docs, "distances": distances, "metadatas": metadatas}


# ===================
# Cache Invalidation Helpers
# ===================


def invalidate_workspace_cache(workspace_id: str) -> None:
    """
    Invalidate all cache entries related to a workspace.

    Args:
        workspace_id: Workspace ID to invalidate
    """
    # Clear Streamlit cache for specific functions
    cached_get_workspaces.clear()
    cached_get_workspace_files.clear(workspace_id)
    cached_get_messages.clear(workspace_id)

    # Clear LRU caches
    get_message_cache().clear()
    get_query_cache().clear()

    logger.info(f"Cache invalidated for workspace: {workspace_id}")


def invalidate_file_cache(workspace_id: str, file_id: str = None) -> None:
    """
    Invalidate file-related cache entries.

    Args:
        workspace_id: Workspace ID
        file_id: Optional specific file ID
    """
    cached_get_workspace_files.clear(workspace_id)
    get_query_cache().clear()

    if file_id:
        logger.info(f"Cache invalidated for file: {file_id}")
    else:
        logger.info(f"File cache invalidated for workspace: {workspace_id}")


def invalidate_embedding_cache() -> None:
    """Clear all embedding caches."""
    get_embedding_cache().clear()
    cached_get_embedding.clear()
    logger.info("Embedding cache cleared")


def invalidate_llm_cache() -> None:
    """Clear LLM response cache."""
    get_llm_response_cache().clear()
    logger.info("LLM response cache cleared")


# ===================
# Utility Functions
# ===================


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def text_hash(text: str) -> str:
    """Generate hash for text content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def clear_all_caches() -> Dict[str, Dict[str, Any]]:
    """
    Clear all application caches.

    Returns:
        Statistics for each cleared cache
    """
    stats = {}

    # Clear LRU caches
    for name, get_cache in [
        ("message_cache", get_message_cache),
        ("embedding_cache", get_embedding_cache),
        ("llm_response_cache", get_llm_response_cache),
        ("query_cache", get_query_cache),
    ]:
        cache = get_cache()
        stats[name] = cache.get_stats()
        cache.clear()

    # Clear Streamlit caches
    cached_get_workspaces.clear()
    cached_get_workspace_files.clear()
    cached_get_messages.clear()
    cached_get_embedding.clear()
    cached_chroma_query.clear()

    stats["streamlit_caches"] = {"cleared": True}

    logger.info("All caches cleared")
    return stats


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches."""
    return {
        "message_cache": get_message_cache().get_stats(),
        "embedding_cache": get_embedding_cache().get_stats(),
        "llm_response_cache": get_llm_response_cache().get_stats(),
        "query_cache": get_query_cache().get_stats(),
    }


# ===================
# Cache Statistics UI Helper
# ===================


def render_cache_stats() -> None:
    """Render cache statistics in Streamlit (for admin/debug)."""
    import streamlit as st

    st.subheader("📊 Önbellek İstatistikleri")

    stats = get_cache_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Mesaj Cache",
            f"{stats['message_cache']['size']}/{stats['message_cache']['max_size']}",
        )
        st.caption(f"Hit Rate: {stats['message_cache']['hit_rate']:.1%}")

    with col2:
        st.metric(
            "Embedding Cache",
            f"{stats['embedding_cache']['size']}/{stats['embedding_cache']['max_size']}",
        )
        st.caption(f"Hit Rate: {stats['embedding_cache']['hit_rate']:.1%}")

    with col3:
        st.metric(
            "LLM Cache",
            f"{stats['llm_response_cache']['size']}/{stats['llm_response_cache']['max_size']}",
        )
        st.caption(f"Hit Rate: {stats['llm_response_cache']['hit_rate']:.1%}")

    with col4:
        st.metric(
            "Query Cache",
            f"{stats['query_cache']['size']}/{stats['query_cache']['max_size']}",
        )
        st.caption(f"Hit Rate: {stats['query_cache']['hit_rate']:.1%}")

    if st.button("🗑️ Tüm Önbellekleri Temizle"):
        clear_all_caches()
        st.success("Tüm önbellekler temizlendi!")
        st.rerun()
