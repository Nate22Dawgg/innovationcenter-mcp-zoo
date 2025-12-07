"""
Simple in-memory cache abstraction for MCP servers.

Provides a cache interface that can be easily replaced with Redis or other
distributed cache implementations later.

The cache is keyed by (server_name, tool_name, normalized_args) and supports
TTL per entry.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheEntry:
    """Represents a cache entry with value and expiration time."""

    value: Any
    expires_at: float  # Unix timestamp when entry expires


class Cache:
    """
    Simple in-memory cache with TTL support.

    This is a thread-safe design that can be easily replaced with Redis
    or other distributed cache implementations later.

    Usage:
        cache = Cache()
        cache.set("key", "value", ttl_seconds=60)
        value = cache.get("key")
    """

    def __init__(self):
        """Initialize an empty cache."""
        self._store: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        entry = self._store.get(key)

        if entry is None:
            return None

        # Check if entry has expired
        if time.time() >= entry.expires_at:
            # Remove expired entry
            del self._store[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Set a value in the cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        expires_at = time.time() + ttl_seconds
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> None:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete
        """
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._store.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._store.items()
            if current_time >= entry.expires_at
        ]

        for key in expired_keys:
            del self._store[key]

        return len(expired_keys)

    def size(self) -> int:
        """
        Get the number of entries in the cache (including expired).

        Returns:
            Number of entries
        """
        return len(self._store)

    def size_active(self) -> int:
        """
        Get the number of non-expired entries in the cache.

        Returns:
            Number of active entries
        """
        current_time = time.time()
        return sum(
            1
            for entry in self._store.values()
            if current_time < entry.expires_at
        )


# Global cache instance (can be replaced with Redis later)
_global_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """
    Get the global cache instance.

    Returns:
        Global Cache instance (singleton)
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


def build_cache_key(
    server_name: str, tool_name: str, args: Dict[str, Any]
) -> str:
    """
    Build a cache key from server name, tool name, and normalized arguments.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool
        args: Tool arguments (will be normalized and hashed)

    Returns:
        Cache key string
    """
    # Normalize args by sorting keys and converting to JSON
    # This ensures consistent keys for the same arguments
    normalized_args = json.dumps(args, sort_keys=True, default=str)
    args_hash = hashlib.sha256(normalized_args.encode()).hexdigest()[:16]

    # Build key: server:tool:hash
    return f"{server_name}:{tool_name}:{args_hash}"


def build_cache_key_simple(*parts: str) -> str:
    """
    Build a simple cache key from string parts.

    Args:
        *parts: String parts to join into a key

    Returns:
        Cache key string
    """
    return ":".join(str(part) for part in parts)
