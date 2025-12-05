"""
Caching layer for real estate API responses.

Uses SQLite to cache API responses with different TTLs based on data type:
- County assessor data: 365 days (changes annually)
- GIS data: 30 days (changes infrequently)
- Market trends: 7 days (update weekly)
- Recent sales: 1 day (update daily)
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class Cache:
    """SQLite-based cache for real estate API responses with configurable TTL."""
    
    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize cache.
        
        Args:
            cache_file: Path to SQLite cache file (default: cache.db in server directory)
        """
        if cache_file is None:
            cache_file = str(Path(__file__).parent / "cache.db")
        
        self.cache_file = cache_file
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database and create cache table if needed."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_type ON cache(data_type)
        """)
        conn.commit()
        conn.close()
    
    def _make_key(self, source: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from source, endpoint and parameters."""
        key_data = {
            "source": source,
            "endpoint": endpoint,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _get_ttl_hours(self, data_type: str) -> int:
        """Get TTL in hours based on data type."""
        ttl_map = {
            "assessor": 365 * 24,  # 1 year
            "gis": 30 * 24,        # 30 days
            "market_trends": 7 * 24,  # 7 days
            "recent_sales": 24,    # 1 day
            "property_lookup": 7 * 24,  # 7 days
            "default": 24          # 1 day default
        }
        return ttl_map.get(data_type, ttl_map["default"])
    
    def get(self, source: str, endpoint: str, params: Dict[str, Any], data_type: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.
        
        Args:
            source: Data source name (e.g., "batchdata", "county_assessor")
            endpoint: API endpoint path
            params: Request parameters
            data_type: Type of data (affects TTL)
        
        Returns:
            Cached response dictionary or None if not found/expired
        """
        key = self._make_key(source, endpoint, params)
        
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
    
    def set(self, source: str, endpoint: str, params: Dict[str, Any], value: Dict[str, Any], data_type: str = "default"):
        """
        Cache a response.
        
        Args:
            source: Data source name
            endpoint: API endpoint path
            params: Request parameters
            value: Response value to cache
            data_type: Type of data (affects TTL)
        """
        key = self._make_key(source, endpoint, params)
        value_str = json.dumps(value)
        created_at = datetime.now()
        ttl_hours = self._get_ttl_hours(data_type)
        expires_at = created_at + timedelta(hours=ttl_hours)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, value, data_type, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value_str, data_type, created_at.isoformat(), expires_at.isoformat()))
        
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
    
    def clear_by_type(self, data_type: str):
        """Clear all cache entries of a specific type."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE data_type = ?", (data_type,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

