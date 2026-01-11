"""
S&P Global Market Intelligence API Client

This module provides a client interface for accessing S&P Global Market Intelligence data.
This is a stub implementation that demonstrates the expected API structure.

⚠️ ENTERPRISE LICENSE REQUIRED: This requires an active S&P Global Market Intelligence subscription.
The actual API endpoints and authentication methods will depend on your specific S&P Global subscription.

For official API documentation and access:
- Contact S&P Global Market Intelligence support
- Visit: https://www.spglobal.com/marketintelligence/en/solutions/capital-iq
- GitHub: Available through S&P Global Market Intelligence (contact for access)
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.http import get, post, CallOptions, call_upstream
from common.errors import ApiError, map_upstream_error
from common.cache import get_cache, build_cache_key


class SPGlobalClient:
    """
    Client for S&P Global Market Intelligence API.
    
    This client provides access to:
    - S&P Capital IQ company search and data
    - Company fundamentals (financial statements, ratios)
    - Earnings call transcripts
    
    Note: This is a framework implementation. Replace with actual S&P Global API integration
    based on your subscription and API documentation.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize S&P Global API client.
        
        Args:
            api_key: S&P Global Market Intelligence API key
            base_url: Base URL for API (defaults to S&P Global API endpoint)
        """
        self.api_key = api_key or os.getenv("SP_GLOBAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SP_GLOBAL_API_KEY environment variable is required. "
                "This is a required configuration - the service will not function without it. "
                "Please set SP_GLOBAL_API_KEY in your environment or configuration. "
                "Contact S&P Global Market Intelligence support for API access."
            )
        
        # Default base URL - replace with actual S&P Global API endpoint
        self.base_url = base_url or os.getenv(
            "SP_GLOBAL_API_URL",
            "https://api.spglobal.com/marketintelligence/v1"
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to S&P Global API using common HTTP wrapper.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
        
        Returns:
            JSON response as dictionary
        
        Raises:
            ApiError: For API errors (handled by common/http wrapper)
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = get(
                    url=url,
                    upstream="sp_global",
                    timeout=10.0,
                    headers=self.headers,
                    params=params,
                    allow_retries=True
                )
            elif method.upper() == "POST":
                options = CallOptions(
                    method="POST",
                    url=url,
                    upstream="sp_global",
                    timeout=10.0,
                    headers=self.headers,
                    params=params,
                    json=data,
                    allow_retries=False  # POST is not idempotent
                )
                response = call_upstream(options)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response.json()
        
        except ApiError as e:
            # Re-raise ApiError as-is (already standardized)
            raise
        except Exception as e:
            # Map unexpected errors to structured errors
            mapped_error = map_upstream_error(e)
            if mapped_error:
                raise mapped_error
            raise ApiError(
                message=f"S&P Global API request failed: {str(e)}",
                original_error=e
            )
    
    def search_companies(
        self,
        query: str,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for companies using S&P Capital IQ.
        
        Args:
            query: Company name, ticker, or CIQ identifier
            country: Filter by country code (ISO 3166-1 alpha-2)
            sector: Filter by industry sector
            limit: Maximum number of results
        
        Returns:
            Dictionary with search results
        """
        params = {
            "q": query,
            "limit": min(limit, 100)  # Cap at 100
        }
        
        if country:
            params["country"] = country
        if sector:
            params["sector"] = sector
        
        # TODO: Replace with actual S&P Global API endpoint
        # Example endpoint structure (verify with S&P Global documentation):
        # response = self._make_request("/companies/search", params=params)
        
        # Stub implementation - replace with actual API call
        return {
            "count": 0,
            "companies": [],
            "query": query,
            "note": "This is a stub implementation. Replace with actual S&P Global API integration."
        }
    
    def get_fundamentals(
        self,
        company_id: str,
        period_type: str = "Annual",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get company fundamentals data.
        
        Args:
            company_id: S&P Capital IQ company identifier (CIQ ID)
            period_type: "Annual" or "Quarterly"
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            metrics: List of specific metrics to retrieve
        
        Returns:
            Dictionary with fundamentals data
        """
        params = {
            "periodType": period_type
        }
        
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if metrics:
            params["metrics"] = ",".join(metrics)
        
        # TODO: Replace with actual S&P Global API endpoint
        # Example endpoint structure (verify with S&P Global documentation):
        # response = self._make_request(f"/companies/{company_id}/fundamentals", params=params)
        
        # Stub implementation - replace with actual API call
        return {
            "company_id": company_id,
            "period_type": period_type,
            "fundamentals": {},
            "note": "This is a stub implementation. Replace with actual S&P Global API integration."
        }
    
    def get_earnings_transcripts(
        self,
        company_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get earnings call transcripts.
        
        Args:
            company_id: S&P Capital IQ company identifier (CIQ ID)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of transcripts
        
        Returns:
            Dictionary with transcripts data
        """
        params = {
            "limit": min(limit, 50)  # Cap at 50
        }
        
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        # TODO: Replace with actual S&P Global API endpoint
        # Example endpoint structure (verify with S&P Global documentation):
        # response = self._make_request(f"/companies/{company_id}/transcripts", params=params)
        
        # Stub implementation - replace with actual API call
        return {
            "company_id": company_id,
            "transcripts": [],
            "count": 0,
            "note": "This is a stub implementation. Replace with actual S&P Global API integration."
        }
    
    def get_company_profile(self, company_id: str) -> Dict[str, Any]:
        """
        Get comprehensive company profile.
        
        Args:
            company_id: S&P Capital IQ company identifier (CIQ ID)
        
        Returns:
            Dictionary with company profile data
        """
        # Check cache first (24 hour TTL for company profiles - update daily)
        cache = get_cache()
        cache_key = build_cache_key(
            server_name="sp-global-mcp",
            tool_name="get_company_profile",
            args={"company_id": company_id}
        )
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # TODO: Replace with actual S&P Global API endpoint
        # Example endpoint structure (verify with S&P Global documentation):
        # response = self._make_request(f"/companies/{company_id}/profile")
        
        # Stub implementation - replace with actual API call
        result = {
            "company_id": company_id,
            "profile": {},
            "note": "This is a stub implementation. Replace with actual S&P Global API integration."
        }
        
        # Cache result with 24 hour TTL (company profiles update daily)
        cache.set(cache_key, result, ttl_seconds=24 * 60 * 60)
        
        return result

