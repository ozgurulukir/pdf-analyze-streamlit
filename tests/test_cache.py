"""Unit tests for caching layer."""
import pytest
import time
from datetime import datetime, timedelta

from app.core.cache import (
    LRUCache,
    CacheEntry,
    get_message_cache,
    get_embedding_cache,
    get_llm_response_cache,
    cached,
    clear_all_caches,
    get_cache_stats,
)


class TestCacheEntry:
    """Tests for CacheEntry."""
    
    def test_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test-key",
            value="test-value",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert entry.key == "test-key"
        assert entry.value == "test-value"
        assert entry.is_expired() is False
    
    def test_entry_expiration(self):
        """Test entry expiration check."""
        entry = CacheEntry(
            key="test-key",
            value="test-value",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert entry.is_expired() is True


class TestLRUCache:
    """Tests for LRUCache."""
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = LRUCache(max_size=100)
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_get_nonexistent(self):
        """Test getting non-existent key."""
        cache = LRUCache()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3)
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = LRUCache(max_size=100, default_ttl=1)  # 1 second TTL
        
        cache.set("key1", "value1", ttl=1)
        
        # Should exist immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired now
        assert cache.get("key1") is None
    
    def test_delete(self):
        """Test delete operation."""
        cache = LRUCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None
        
        # Delete non-existent
        result = cache.delete("nonexistent")
        assert result is False
    
    def test_clear(self):
        """Test clear operation."""
        cache = LRUCache()
        
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        
        cache.clear()
        
        assert len(cache) == 0
        assert cache.get("a") is None
    
    def test_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10)
        
        # Miss
        cache.get("nonexistent")
        
        # Set and hit
        cache.set("key1", "value1")
        cache.get("key1")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["max_size"] == 10
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = LRUCache()
        
        # Add entries with different TTLs
        cache.set("short", "value1", ttl=1)
        cache.set("long", "value2", ttl=3600)
        
        # Wait for short to expire
        time.sleep(1.5)
        
        # Cleanup
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("short") is None
        assert cache.get("long") == "value2"
    
    def test_contains(self):
        """Test __contains__ operator."""
        cache = LRUCache()
        
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "nonexistent" not in cache


class TestCachedDecorator:
    """Tests for @cached decorator."""
    
    def test_caches_result(self):
        """Test that decorator caches results."""
        cache = LRUCache()
        call_count = 0
        
        @cached(cache)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (should use cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented
    
    def test_different_args_different_cache(self):
        """Test that different arguments use different cache keys."""
        cache = LRUCache()
        call_count = 0
        
        @cached(cache)
        def func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = func(5)
        result2 = func(10)
        
        assert result1 == 10
        assert result2 == 20
        assert call_count == 2
    
    def test_custom_key_function(self):
        """Test custom key function."""
        cache = LRUCache()
        
        def key_func(user_id, action):
            return f"{user_id}:{action}"
        
        @cached(cache, key_func=key_func)
        def user_action(user_id, action):
            return f"{user_id} did {action}"
        
        result = user_action("user1", "login")
        assert result == "user1 did login"


class TestGlobalCaches:
    """Tests for global cache instances."""
    
    def test_get_message_cache(self):
        """Test message cache singleton."""
        cache1 = get_message_cache()
        cache2 = get_message_cache()
        
        assert cache1 is cache2
    
    def test_get_embedding_cache(self):
        """Test embedding cache singleton."""
        cache1 = get_embedding_cache()
        cache2 = get_embedding_cache()
        
        assert cache1 is cache2
    
    def test_get_llm_response_cache(self):
        """Test LLM response cache singleton."""
        cache1 = get_llm_response_cache()
        cache2 = get_llm_response_cache()
        
        assert cache1 is cache2
    
    def test_clear_all_caches(self):
        """Test clearing all caches."""
        # Add data to all caches
        get_message_cache().set("test", "value")
        get_embedding_cache().set("test", "value")
        get_llm_response_cache().set("test", "value")
        
        # Clear all
        result = clear_all_caches()
        
        assert all(r["cleared"] for r in result.values())
    
    def test_get_cache_stats(self):
        """Test getting stats for all caches."""
        stats = get_cache_stats()
        
        assert "message_cache" in stats
        assert "embedding_cache" in stats
        assert "llm_response_cache" in stats
