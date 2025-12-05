"""
Caching layer for biotech markets API responses.

Uses SQLite to cache API responses for 24 hours to reduce API calls and improve performance.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class Cache:
    """Simple SQLite-based cache for API responses."""
    
    def __init__(self, cache_file: Optional[str] = None, ttl_hours: int = 24):
        """
        Initialize cache.
        
        Args:
            cache_file: Path to SQLite cache file (default: cache.db in server directory)
            ttl_hours: Time-to-live for cached entries in hours (default: 24)
        """
        if cache_file is None:
            cache_file = str(Path(__file__).parent / "cache.db")
        
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database and create cache table if needed."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        """)
        conn.commit()
        conn.close()
    
    def _make_key(self, source: str, params: Dict[str, Any]) -> str:
        """Generate cache key from source and parameters."""
        key_data = {
            "source": source,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, source: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.
        
        Args:
            source: API source identifier (e.g., "clinical_trials", "sec_edgar")
            params: Request parameters
        
        Returns:
            Cached response dictionary or None if not found/expired
        """
        key = self._make_key(source, params)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, expires_at FROM cache
            WHERE key = ? AND expires_at > ?
        """, (key, datetime.now().isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            value_str, expires_at = row
            return json.loads(value_str)
        
        return None
    
    def set(self, source: str, params: Dict[str, Any], value: Dict[str, Any], ttl_hours: Optional[int] = None):
        """
        Cache a response.
        
        Args:
            source: API source identifier
            params: Request parameters
            value: Response value to cache
            ttl_hours: Optional TTL in hours (overrides default if provided)
        """
        key = self._make_key(source, params)
        value_str = json.dumps(value)
        created_at = datetime.now()
        ttl = ttl_hours if ttl_hours is not None else self.ttl_hours
        expires_at = created_at + timedelta(hours=ttl)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (key, value_str, created_at.isoformat(), expires_at.isoformat()))
        
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        """Remove expired cache entries."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE expires_at <= ?", (datetime.now().isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_all(self):
        """Clear all cache entries."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache")
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

