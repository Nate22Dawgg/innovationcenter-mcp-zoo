"""
Tests for cache module.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from common.cache import (
    Cache,
    CacheEntry,
    get_cache,
    build_cache_key,
    build_cache_key_simple,
)


class TestCacheEntry:
    """Test CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a CacheEntry."""
        entry = CacheEntry(value="test", expires_at=1000.0)

        assert entry.value == "test"
        assert entry.expires_at == 1000.0


class TestCache:
    """Test Cache class."""

    def test_cache_initialization(self):
        """Test cache starts empty."""
        cache = Cache()

        assert cache.size() == 0
        assert cache.size_active() == 0

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"

        cache.set("key2", {"nested": "data"}, ttl_seconds=60)
        assert cache.get("key2") == {"nested": "data"}

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = Cache()

        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=1)
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Entry should be expired and removed
        assert cache.get("key1") is None
        assert cache.size() == 0

    def test_delete(self):
        """Test deleting a key."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Test deleting a key that doesn't exist (should not error)."""
        cache = Cache()

        # Should not raise an error
        cache.delete("nonexistent")

    def test_clear(self):
        """Test clearing all entries."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self):
        """Test cleanup_expired removes expired entries."""
        cache = Cache()

        # Add entries with different TTLs
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.size() == 2

        # Wait for key1 to expire
        time.sleep(1.1)

        # Cleanup should remove expired entries
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.size() == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_size(self):
        """Test size() returns total entries including expired."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.size() == 2

        # Wait for key1 to expire
        time.sleep(1.1)

        # size() still counts expired entries
        assert cache.size() == 2

    def test_size_active(self):
        """Test size_active() returns only non-expired entries."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.size_active() == 2

        # Wait for key1 to expire
        time.sleep(1.1)

        # size_active() only counts non-expired entries
        assert cache.size_active() == 1

    def test_overwrite_value(self):
        """Test overwriting a value updates it."""
        cache = Cache()

        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"

        cache.set("key1", "value2", ttl_seconds=60)
        assert cache.get("key1") == "value2"

    def test_different_types(self):
        """Test caching different types of values."""
        cache = Cache()

        cache.set("str", "string", ttl_seconds=60)
        cache.set("int", 42, ttl_seconds=60)
        cache.set("float", 3.14, ttl_seconds=60)
        cache.set("bool", True, ttl_seconds=60)
        cache.set("list", [1, 2, 3], ttl_seconds=60)
        cache.set("dict", {"key": "value"}, ttl_seconds=60)
        cache.set("none", None, ttl_seconds=60)

        assert cache.get("str") == "string"
        assert cache.get("int") == 42
        assert cache.get("float") == 3.14
        assert cache.get("bool") is True
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"key": "value"}
        assert cache.get("none") is None


class TestGetCache:
    """Test get_cache() singleton function."""

    def test_get_cache_returns_singleton(self):
        """Test that get_cache() returns the same instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    def test_get_cache_set_and_get(self):
        """Test using the global cache instance."""
        cache = get_cache()
        cache.clear()  # Start fresh

        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"


class TestBuildCacheKey:
    """Test cache key building functions."""

    def test_build_cache_key(self):
        """Test building cache key from server, tool, and args."""
        key = build_cache_key(
            server_name="test_server",
            tool_name="test_tool",
            args={"param1": "value1", "param2": "value2"},
        )

        assert isinstance(key, str)
        assert key.startswith("test_server:test_tool:")
        assert len(key) > len("test_server:test_tool:")

    def test_build_cache_key_normalized(self):
        """Test that cache keys are normalized (same args = same key)."""
        args1 = {"param1": "value1", "param2": "value2"}
        args2 = {"param2": "value2", "param1": "value1"}  # Different order

        key1 = build_cache_key("server", "tool", args1)
        key2 = build_cache_key("server", "tool", args2)

        # Should produce the same key despite different order
        assert key1 == key2

    def test_build_cache_key_different_args(self):
        """Test that different args produce different keys."""
        args1 = {"param1": "value1"}
        args2 = {"param1": "value2"}

        key1 = build_cache_key("server", "tool", args1)
        key2 = build_cache_key("server", "tool", args2)

        # Should produce different keys
        assert key1 != key2

    def test_build_cache_key_different_tools(self):
        """Test that different tools produce different keys."""
        args = {"param1": "value1"}

        key1 = build_cache_key("server", "tool1", args)
        key2 = build_cache_key("server", "tool2", args)

        # Should produce different keys
        assert key1 != key2

    def test_build_cache_key_simple(self):
        """Test building simple cache key from parts."""
        key = build_cache_key_simple("part1", "part2", "part3")

        assert key == "part1:part2:part3"

    def test_build_cache_key_simple_empty(self):
        """Test building cache key with no parts."""
        key = build_cache_key_simple()

        assert key == ""

    def test_build_cache_key_simple_single(self):
        """Test building cache key with single part."""
        key = build_cache_key_simple("single")

        assert key == "single"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
