"""
Example upstream API client.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename ExampleClient to YourClient
3. Implement actual HTTP calls to your upstream API
4. Add proper error handling using common.errors.map_upstream_error
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from common.http import CallOptions, get, post
from common.errors import map_upstream_error, ApiError
from common.logging import get_logger

logger = get_logger(__name__)


class ExampleClient:
    """
    Example upstream API client.
    
    This demonstrates:
    - Using the shared HTTP wrapper (common.http)
    - Handling upstream errors with map_upstream_error
    - Optional caching integration (can use common.cache.build_cache_key)
    
    Replace this with a real client when you create a server from this template.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def ping(self) -> Dict[str, Any]:
        """
        Example method that demonstrates client usage with error handling.
        
        This shows how to:
        - Use the shared HTTP wrapper
        - Handle errors with map_upstream_error
        - Return structured responses
        
        Returns:
            Dictionary with status information
        
        Raises:
            ApiError: If the API call fails
        """
        try:
            # Use the shared HTTP wrapper for consistent error handling
            response = get(
                url=f"{self.base_url}/ping",
                upstream="example",  # Used for circuit breaker per upstream
                timeout=10.0,
                headers=self._headers
            )
            
            # Parse response
            data = response.json()
            
            logger.info("Successfully pinged example API")
            return {
                "status": "ok",
                "data": data
            }
            
        except Exception as e:
            # Map upstream errors to standardized MCP errors
            mcp_error = map_upstream_error(e)
            logger.error(f"Failed to ping example API: {mcp_error.message}")
            raise mcp_error

    def get_data(self, resource_id: str) -> Dict[str, Any]:
        """
        Example method for fetching data from the API.
        
        This demonstrates a more complex use case with error handling.
        
        Args:
            resource_id: ID of the resource to fetch
        
        Returns:
            Dictionary with resource data
        
        Raises:
            ApiError: If the API call fails
        """
        try:
            response = get(
                url=f"{self.base_url}/data/{resource_id}",
                upstream="example",
                timeout=10.0,
                headers=self._headers
            )
            
            data = response.json()
            
            logger.info(f"Successfully fetched data for resource {resource_id}")
            return data
            
        except Exception as e:
            mcp_error = map_upstream_error(e)
            logger.error(f"Failed to fetch data for resource {resource_id}: {mcp_error.message}")
            raise mcp_error
    
    # Optional: Add caching support using common.cache
    # Example cached method (uncomment and customize as needed):
    # 
    # def get_data_cached(self, resource_id: str, ttl_seconds: int = 300) -> Dict[str, Any]:
    #     """
    #     Cached version of get_data() that checks cache before making API call.
    #     
    #     Args:
    #         resource_id: ID of the resource to fetch
    #         ttl_seconds: Cache TTL in seconds (default: 5 minutes)
    #     
    #     Returns:
    #         Dictionary with resource data (from cache or API)
    #     """
    #     from common.cache import get_cache, build_cache_key
    #     
    #     cache = get_cache()
    #     cache_key = build_cache_key("example-server", "get_data", {"resource_id": resource_id})
    #     
    #     # Check cache first
    #     cached = cache.get(cache_key)
    #     if cached is not None:
    #         logger.info(f"Cache hit for resource_id: {resource_id}")
    #         return cached
    #     
    #     # Cache miss - fetch from API
    #     logger.info(f"Cache miss for resource_id: {resource_id}, fetching from API")
    #     data = self.get_data(resource_id)
    #     
    #     # Store in cache
    #     cache.set(cache_key, data, ttl_seconds)
    #     logger.info(f"Cached data for resource_id: {resource_id} (TTL: {ttl_seconds}s)")
    #     return data
