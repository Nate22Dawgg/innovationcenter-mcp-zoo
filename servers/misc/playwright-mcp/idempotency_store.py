"""
Idempotency store for Playwright MCP write tools.

Stores completed actions by idempotency key to prevent duplicate executions.
Uses in-memory storage with optional cache integration.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import sys
from pathlib import Path

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import Cache, get_cache


@dataclass
class IdempotencyRecord:
    """Record of a completed action for idempotency checking."""
    
    idempotency_key: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    completed_at: float  # Unix timestamp
    execution_id: str  # Unique ID for this execution


class IdempotencyStore:
    """
    Store for tracking completed actions by idempotency key.
    
    Prevents duplicate execution of write operations when the same
    idempotency_key is used with identical parameters.
    """
    
    def __init__(self, cache: Optional[Cache] = None, ttl_seconds: int = 86400 * 7):
        """
        Initialize idempotency store.
        
        Args:
            cache: Optional cache instance (uses global cache if not provided)
            ttl_seconds: Time to live for idempotency records (default: 7 days)
        """
        self._cache = cache or get_cache()
        self._ttl_seconds = ttl_seconds
        self._in_memory_store: Dict[str, IdempotencyRecord] = {}
    
    def _build_key(self, idempotency_key: str, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Build a cache key from idempotency key, tool name, and parameters.
        
        Args:
            idempotency_key: User-provided idempotency key
            tool_name: Name of the tool
            parameters: Tool parameters (normalized)
            
        Returns:
            Cache key string
        """
        # Normalize parameters by sorting keys and converting to JSON
        normalized_params = json.dumps(parameters, sort_keys=True, default=str)
        params_hash = hashlib.sha256(normalized_params.encode()).hexdigest()[:16]
        
        # Build key: idempotency:tool:key:hash
        return f"idempotency:{tool_name}:{idempotency_key}:{params_hash}"
    
    def get(self, idempotency_key: str, tool_name: str, parameters: Dict[str, Any]) -> Optional[IdempotencyRecord]:
        """
        Get a previously completed action by idempotency key.
        
        Args:
            idempotency_key: User-provided idempotency key
            tool_name: Name of the tool
            parameters: Tool parameters
            
        Returns:
            IdempotencyRecord if found, None otherwise
        """
        key = self._build_key(idempotency_key, tool_name, parameters)
        
        # Check in-memory store first
        if key in self._in_memory_store:
            record = self._in_memory_store[key]
            # Check if expired
            if time.time() < (record.completed_at + self._ttl_seconds):
                return record
            else:
                # Remove expired record
                del self._in_memory_store[key]
        
        # Check cache
        cached = self._cache.get(key)
        if cached:
            try:
                # Reconstruct record from cached data
                record = IdempotencyRecord(**cached)
                # Check if expired
                if time.time() < (record.completed_at + self._ttl_seconds):
                    # Store in memory for faster access
                    self._in_memory_store[key] = record
                    return record
            except (TypeError, KeyError):
                # Invalid cached data, ignore
                pass
        
        return None
    
    def store(self, idempotency_key: str, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any], execution_id: str) -> None:
        """
        Store a completed action for idempotency checking.
        
        Args:
            idempotency_key: User-provided idempotency key
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Result of the action
            execution_id: Unique ID for this execution
        """
        key = self._build_key(idempotency_key, tool_name, parameters)
        
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            completed_at=time.time(),
            execution_id=execution_id
        )
        
        # Store in memory
        self._in_memory_store[key] = record
        
        # Store in cache (convert dataclass to dict for caching)
        record_dict = {
            "idempotency_key": record.idempotency_key,
            "tool_name": record.tool_name,
            "parameters": record.parameters,
            "result": record.result,
            "completed_at": record.completed_at,
            "execution_id": record.execution_id
        }
        self._cache.set(key, record_dict, ttl_seconds=self._ttl_seconds)
    
    def clear(self) -> None:
        """Clear all idempotency records."""
        self._in_memory_store.clear()
        # Note: Cache clearing would require cache implementation support


# Global idempotency store instance
_global_store: Optional[IdempotencyStore] = None


def get_idempotency_store() -> IdempotencyStore:
    """
    Get the global idempotency store instance.
    
    Returns:
        Global IdempotencyStore instance (singleton)
    """
    global _global_store
    if _global_store is None:
        _global_store = IdempotencyStore()
    return _global_store
