"""Caching layer for improved performance."""
import time
import hashlib
import json
from typing import Any, Optional, Callable, TypeVar, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
from threading import Lock

from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


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
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
    
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
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats["hits"] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]
            
            # Evict oldest if at capacity
            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            # Calculate expiration
            ttl = ttl if ttl is not None else self._default_ttl
            now = datetime.now()
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl)
            )
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            self._stats["expirations"] += len(expired_keys)
            return len(expired_keys)
    
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
                "expirations": self._stats["expirations"]
            }
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """Get number of entries."""
        return len(self._cache)


# ===================
# Cache Instances
# ===================

# Global cache instances
_message_cache: Optional[LRUCache] = None
_embedding_cache: Optional[LRUCache] = None
_llm_response_cache: Optional[LRUCache] = None


def get_message_cache() -> LRUCache:
    """Get the global message cache."""
    global _message_cache
    if _message_cache is None:
        _message_cache = LRUCache(max_size=500, default_ttl=3600)
    return _message_cache


def get_embedding_cache() -> LRUCache:
    """Get the global embedding cache."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = LRUCache(max_size=1000, default_ttl=86400)  # 24 hours
    return _embedding_cache


def get_llm_response_cache() -> LRUCache:
    """Get the global LLM response cache."""
    global _llm_response_cache
    if _llm_response_cache is None:
        _llm_response_cache = LRUCache(max_size=200, default_ttl=1800)  # 30 minutes
    return _llm_response_cache


# ===================
# Cache Decorators
# ===================

def cached(
    cache: LRUCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
):
    """
    Decorator to cache function results.
    
    Args:
        cache: Cache instance to use
        key_func: Function to generate cache key from args
        ttl: Time-to-live for cached results
        
    Usage:
        @cached(get_embedding_cache())
        def get_embedding(text: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Compute value
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


# ===================
# Utility Functions
# ===================

def clear_all_caches() -> Dict[str, Dict[str, Any]]:
    """
    Clear all application caches.
    
    Returns:
        Statistics for each cleared cache
    """
    stats = {}
    
    for name, cache in [
        ("message_cache", get_message_cache()),
        ("embedding_cache", get_embedding_cache()),
        ("llm_response_cache", get_llm_response_cache()),
    ]:
        cache.clear()
        stats[name] = {"cleared": True}
    
    return stats


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches."""
    return {
        "message_cache": get_message_cache().get_stats(),
        "embedding_cache": get_embedding_cache().get_stats(),
        "llm_response_cache": get_llm_response_cache().get_stats(),
    }
