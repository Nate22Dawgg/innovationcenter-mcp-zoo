"""
Turquoise Health API client for hospital pricing data.

This module provides functions to interact with the Turquoise Health API
for searching hospital prices, comparing rates, and estimating cash prices.
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add common directory to path for error handling
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.http import get, CallOptions, call_upstream
    from common.errors import ApiError, ErrorCode, map_upstream_error
except ImportError:
    # Fallback if common module not available
    get = None
    CallOptions = None
    call_upstream = None
    ApiError = Exception
    ErrorCode = None
    map_upstream_error = None

try:
    from .cache import Cache
except ImportError:
    from cache import Cache


# Turquoise Health API base URL
API_BASE_URL = "https://api.turquoise.health"


class TurquoiseHealthClient:
    """Client for interacting with Turquoise Health API."""
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the Turquoise Health API client.
        
        Args:
            api_key: API key for authentication. If not provided, reads from TURQUOISE_API_KEY env var.
            use_cache: Whether to use caching (default: True)
        """
        self.api_key = api_key or os.getenv("TURQUOISE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Turquoise Health API key is required. "
                "Set TURQUOISE_API_KEY environment variable or pass api_key parameter. "
                "This is a required configuration - the service will not function without it."
            )
        
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Caching
        self.use_cache = use_cache
        self.cache = Cache() if use_cache else None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Turquoise Health API using the common HTTP wrapper.
        
        This method now uses the standardized HTTP wrapper from common/http.py which provides:
        - Automatic timeout handling (10s default, fail fast)
        - Retries with exponential backoff (only for idempotent GET requests)
        - Circuit breaker per upstream (tracks failure rate for "turquoise")
        - Standardized error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Maximum number of retry attempts (passed to wrapper)
        
        Returns:
            JSON response as dictionary
        
        Raises:
            ApiError: For API errors (handled by common/http wrapper)
        """
        # Use common HTTP wrapper if available, otherwise fallback to old implementation
        if get is None or call_upstream is None:
            # Fallback to old implementation
            return self._make_request_legacy(method, endpoint, params, max_retries)
        
        url = f"{self.base_url}{endpoint}"
        
        # Only GET requests are idempotent and allow retries
        allow_retries = (method.upper() == "GET")
        
        try:
            if method.upper() == "GET":
                response = get(
                    url=url,
                    upstream="turquoise",
                    timeout=10.0,  # Fail fast with 10s timeout
                    headers=self.headers,
                    params=params,
                    allow_retries=allow_retries,
                    max_retries=max_retries if allow_retries else 0,
                )
            else:
                # For non-GET requests, use CallOptions directly
                options = CallOptions(
                    method=method.upper(),
                    url=url,
                    upstream="turquoise",
                    timeout=10.0,
                    headers=self.headers,
                    params=params,
                    allow_retries=False,  # POST/PUT/DELETE are not idempotent
                )
                response = call_upstream(options)
            
            return response.json()
            
        except ApiError as e:
            # Re-raise ApiError as-is (already standardized)
            raise
        except Exception as e:
            # Wrap unexpected errors
            if ApiError and ErrorCode:
                raise ApiError(
                    message=f"Unexpected error: {str(e)}",
                    original_error=e,
                    code=ErrorCode.INTERNAL_ERROR,
                )
            raise
    
    def _make_request_legacy(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Legacy implementation for when common/http is not available.
        
        This is kept as a fallback for backward compatibility.
        """
        import requests
        
        url = f"{self.base_url}{endpoint}"
        session = requests.Session()
        session.headers.update(self.headers)
        
        for attempt in range(max_retries):
            try:
                response = session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds.")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception("Request timeout after retries")
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"API request failed: {str(e)}")
        
        raise Exception("Request failed after all retries")
    
    def search_procedure_price(
        self,
        cpt_code: str,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        zip_code: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for procedure prices by CPT code and location.
        
        Args:
            cpt_code: CPT or HCPCS procedure code (e.g., "99213")
            location: Location string (city, state or zip code)
            radius: Search radius in miles (default: 25)
            zip_code: ZIP code for location-based search
            state: US state code (2 letters)
        
        Returns:
            Dictionary with search results containing hospitals and prices
        """
        params = {
            "code": cpt_code
        }
        
        if zip_code:
            params["zip_code"] = zip_code
        elif location:
            params["location"] = location
        
        if state:
            params["state"] = state.upper()
        
        if radius:
            params["radius"] = radius
        
        # Check cache first
        if self.use_cache and self.cache:
            cached = self.cache.get("/v1/procedures/search", params)
            if cached:
                return cached
        
        try:
            response = self._make_request("GET", "/v1/procedures/search", params=params)
            result = self._normalize_search_response(response, cpt_code)
            
            # Cache result
            if self.use_cache and self.cache:
                self.cache.set("/v1/procedures/search", params, result)
            
            return result
        except (ApiError, Exception) as e:
            # If it's already a structured error, re-raise it
            if isinstance(e, ApiError):
                raise
            # Otherwise, map it to a structured error
            if map_upstream_error:
                raise map_upstream_error(e)
            raise Exception(f"Failed to search procedure prices: {str(e)}")
    
    def get_hospital_rates(
        self,
        hospital_id: str,
        cpt_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get hospital rate sheet for specific hospital and optional CPT codes.
        
        Args:
            hospital_id: Turquoise Health hospital identifier
            cpt_codes: Optional list of CPT codes to filter rates
        
        Returns:
            Dictionary with hospital information and rates
        """
        params = {}
        if cpt_codes:
            params["codes"] = ",".join(cpt_codes)
        
        # Check cache first
        cache_params = {"hospital_id": hospital_id, **params}
        if self.use_cache and self.cache:
            cached = self.cache.get(f"/v1/hospitals/{hospital_id}/rates", cache_params)
            if cached:
                return cached
        
        try:
            response = self._make_request(
                "GET",
                f"/v1/hospitals/{hospital_id}/rates",
                params=params
            )
            result = self._normalize_rates_response(response, hospital_id)
            
            # Cache result
            if self.use_cache and self.cache:
                self.cache.set(f"/v1/hospitals/{hospital_id}/rates", cache_params, result)
            
            return result
        except (ApiError, Exception) as e:
            # If it's already a structured error, re-raise it
            if isinstance(e, ApiError):
                raise
            # Otherwise, map it to a structured error
            if map_upstream_error:
                raise map_upstream_error(e)
            raise Exception(f"Failed to get hospital rates: {str(e)}")
    
    def compare_prices(
        self,
        cpt_code: str,
        location: str,
        limit: int = 10,
        zip_code: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare prices for a procedure across multiple facilities.
        
        Args:
            cpt_code: CPT or HCPCS procedure code
            location: Location string (city, state or zip code)
            limit: Maximum number of results to return (default: 10)
            zip_code: ZIP code for location-based search
            state: US state code (2 letters)
        
        Returns:
            Dictionary with ranked list of facilities by price
        """
        params = {
            "code": cpt_code,
            "limit": min(limit, 100)  # Cap at 100
        }
        
        if zip_code:
            params["zip_code"] = zip_code
        elif location:
            params["location"] = location
        
        if state:
            params["state"] = state.upper()
        
        # Check cache first
        if self.use_cache and self.cache:
            cached = self.cache.get("/v1/procedures/compare", params)
            if cached:
                return cached
        
        try:
            response = self._make_request("GET", "/v1/procedures/compare", params=params)
            result = self._normalize_compare_response(response, cpt_code)
            
            # Cache result
            if self.use_cache and self.cache:
                self.cache.set("/v1/procedures/compare", params, result)
            
            return result
        except (ApiError, Exception) as e:
            # If it's already a structured error, re-raise it
            if isinstance(e, ApiError):
                raise
            # Otherwise, map it to a structured error
            if map_upstream_error:
                raise map_upstream_error(e)
            raise Exception(f"Failed to compare prices: {str(e)}")
    
    def estimate_cash_price(
        self,
        cpt_code: str,
        location: str,
        zip_code: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate cash price range for a procedure in a location.
        
        Args:
            cpt_code: CPT or HCPCS procedure code
            location: Location string (city, state or zip code)
            zip_code: ZIP code for location-based search
            state: US state code (2 letters)
        
        Returns:
            Dictionary with estimated cash price range and statistics
        """
        params = {
            "code": cpt_code
        }
        
        if zip_code:
            params["zip_code"] = zip_code
        elif location:
            params["location"] = location
        
        if state:
            params["state"] = state.upper()
        
        # Check cache first
        if self.use_cache and self.cache:
            cached = self.cache.get("/v1/procedures/estimate", params)
            if cached:
                return cached
        
        try:
            response = self._make_request("GET", "/v1/procedures/estimate", params=params)
            result = self._normalize_estimate_response(response, cpt_code)
            
            # Cache result
            if self.use_cache and self.cache:
                self.cache.set("/v1/procedures/estimate", params, result)
            
            return result
        except (ApiError, Exception) as e:
            # If it's already a structured error, re-raise it
            if isinstance(e, ApiError):
                raise
            # Otherwise, map it to a structured error
            if map_upstream_error:
                raise map_upstream_error(e)
            raise Exception(f"Failed to estimate cash price: {str(e)}")
    
    def _normalize_search_response(self, response: Dict[str, Any], cpt_code: str) -> Dict[str, Any]:
        """Normalize API response to our schema format."""
        prices = []
        
        # Handle different possible response structures
        results = response.get("data", response.get("results", response.get("hospitals", [])))
        
        for item in results:
            hospital_info = item.get("hospital", item.get("facility", {}))
            pricing_info = item.get("pricing", item.get("price", {}))
            
            price_obj = {
                "hospital_id": hospital_info.get("id", hospital_info.get("hospital_id", "")),
                "hospital_name": hospital_info.get("name", hospital_info.get("hospital_name", "")),
                "address": {
                    "street": hospital_info.get("address", hospital_info.get("street", "")),
                    "city": hospital_info.get("city", ""),
                    "state": hospital_info.get("state", ""),
                    "zip_code": hospital_info.get("zip_code", hospital_info.get("zip", ""))
                },
                "procedure_code": cpt_code,
                "procedure_description": item.get("procedure_description", item.get("description", "")),
                "pricing": {
                    "cash_price": pricing_info.get("cash_price", pricing_info.get("cash", None)),
                    "insurance_price": pricing_info.get("insurance_price", pricing_info.get("negotiated", None)),
                    "medicare_price": pricing_info.get("medicare_price", pricing_info.get("medicare", None))
                },
                "year": item.get("year", datetime.now().year),
                "data_source": "Turquoise Health API"
            }
            prices.append(price_obj)
        
        return {
            "count": len(prices),
            "total": response.get("total", response.get("count", len(prices))),
            "prices": prices
        }
    
    def _normalize_rates_response(self, response: Dict[str, Any], hospital_id: str) -> Dict[str, Any]:
        """Normalize hospital rates response to our schema format."""
        hospital_info = response.get("hospital", response.get("facility", {}))
        rates = response.get("rates", response.get("data", []))
        
        prices = []
        for rate in rates:
            price_obj = {
                "hospital_id": hospital_id,
                "hospital_name": hospital_info.get("name", hospital_info.get("hospital_name", "")),
                "address": {
                    "street": hospital_info.get("address", hospital_info.get("street", "")),
                    "city": hospital_info.get("city", ""),
                    "state": hospital_info.get("state", ""),
                    "zip_code": hospital_info.get("zip_code", hospital_info.get("zip", ""))
                },
                "procedure_code": rate.get("code", rate.get("cpt_code", "")),
                "procedure_description": rate.get("description", rate.get("procedure_description", "")),
                "pricing": {
                    "cash_price": rate.get("cash_price", rate.get("cash", None)),
                    "insurance_price": rate.get("insurance_price", rate.get("negotiated", None)),
                    "medicare_price": rate.get("medicare_price", rate.get("medicare", None))
                },
                "year": rate.get("year", datetime.now().year),
                "data_source": "Turquoise Health API"
            }
            prices.append(price_obj)
        
        return {
            "hospital_id": hospital_id,
            "hospital_name": hospital_info.get("name", hospital_info.get("hospital_name", "")),
            "count": len(prices),
            "prices": prices
        }
    
    def _normalize_compare_response(self, response: Dict[str, Any], cpt_code: str) -> Dict[str, Any]:
        """Normalize price comparison response to our schema format."""
        results = response.get("data", response.get("results", response.get("comparisons", [])))
        
        comparisons = []
        for item in results:
            hospital_info = item.get("hospital", item.get("facility", {}))
            pricing_info = item.get("pricing", item.get("price", {}))
            
            comparison_obj = {
                "hospital_id": hospital_info.get("id", hospital_info.get("hospital_id", "")),
                "hospital_name": hospital_info.get("name", hospital_info.get("hospital_name", "")),
                "address": {
                    "street": hospital_info.get("address", hospital_info.get("street", "")),
                    "city": hospital_info.get("city", ""),
                    "state": hospital_info.get("state", ""),
                    "zip_code": hospital_info.get("zip_code", hospital_info.get("zip", ""))
                },
                "procedure_code": cpt_code,
                "procedure_description": item.get("procedure_description", item.get("description", "")),
                "pricing": {
                    "cash_price": pricing_info.get("cash_price", pricing_info.get("cash", None)),
                    "insurance_price": pricing_info.get("insurance_price", pricing_info.get("negotiated", None)),
                    "medicare_price": pricing_info.get("medicare_price", pricing_info.get("medicare", None))
                },
                "rank": item.get("rank", len(comparisons) + 1),
                "distance_miles": item.get("distance", item.get("distance_miles", None))
            }
            comparisons.append(comparison_obj)
        
        # Sort by cash price if available
        comparisons.sort(key=lambda x: (
            x["pricing"]["cash_price"] if x["pricing"]["cash_price"] else float('inf'),
            x["pricing"]["insurance_price"] if x["pricing"]["insurance_price"] else float('inf')
        ))
        
        return {
            "procedure_code": cpt_code,
            "count": len(comparisons),
            "comparisons": comparisons
        }
    
    def _normalize_estimate_response(self, response: Dict[str, Any], cpt_code: str) -> Dict[str, Any]:
        """Normalize cash price estimate response to our schema format."""
        stats = response.get("statistics", response.get("stats", response.get("estimate", {})))
        
        return {
            "procedure_code": cpt_code,
            "location": response.get("location", ""),
            "estimate": {
                "min_price": stats.get("min_price", stats.get("min", None)),
                "max_price": stats.get("max_price", stats.get("max", None)),
                "median_price": stats.get("median_price", stats.get("median", None)),
                "average_price": stats.get("average_price", stats.get("mean", None)),
                "sample_size": stats.get("sample_size", stats.get("count", 0))
            },
            "data_source": "Turquoise Health API",
            "year": response.get("year", datetime.now().year)
        }

