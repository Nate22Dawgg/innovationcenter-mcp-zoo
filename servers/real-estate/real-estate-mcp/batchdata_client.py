"""
BatchData.io API client for property and address data.

Wraps the BatchData.io API to provide property lookup and address enrichment.
Requires BATCHDATA_API_KEY environment variable.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.http import post, CallOptions, call_upstream
from common.errors import ApiError, map_upstream_error
from common.cache import get_cache, build_cache_key


class BatchDataClient:
    """Client for BatchData.io API."""
    
    BASE_URL = "https://api.batchdata.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None, cache=None):
        """
        Initialize BatchData client.
        
        Args:
            api_key: BatchData.io API key (defaults to BATCHDATA_API_KEY env var)
            cache: Optional cache instance (from common.cache.get_cache())
        """
        self.api_key = api_key or os.getenv("BATCHDATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BATCHDATA_API_KEY environment variable is required. "
                "This is a required configuration - the service will not function without it. "
                "Please set BATCHDATA_API_KEY in your environment or configuration."
            )
        
        self.cache = cache or get_cache()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, data: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """Make API request with optional caching."""
        # TTL: 7 days for property lookup data (conservative default)
        ttl_seconds = 7 * 24 * 60 * 60
        
        # Check cache
        if use_cache and self.cache:
            cache_key = build_cache_key(
                server_name="real-estate-mcp",
                tool_name=f"batchdata_{endpoint.replace('/', '_')}",
                args={"endpoint": endpoint, "data": data}
            )
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Make request using common HTTP wrapper
        url = f"{self.BASE_URL}{endpoint}"
        try:
            options = CallOptions(
                method="POST",
                url=url,
                upstream="batchdata",
                timeout=30.0,
                headers=self.headers,
                json=data,
                allow_retries=False  # POST is not idempotent
            )
            response = call_upstream(options)
            result = response.json()
        except ApiError as e:
            # Re-raise ApiError as-is (already standardized)
            raise
        except Exception as e:
            # Map unexpected errors to structured errors
            mapped_error = map_upstream_error(e)
            if mapped_error:
                raise mapped_error
            raise ApiError(
                message=f"BatchData API error: {str(e)}",
                original_error=e
            )
        
        # Cache result with 7 day TTL (property lookup data changes infrequently)
        if use_cache and self.cache:
            cache_key = build_cache_key(
                server_name="real-estate-mcp",
                tool_name=f"batchdata_{endpoint.replace('/', '_')}",
                args={"endpoint": endpoint, "data": data}
            )
            self.cache.set(cache_key, result, ttl_seconds=ttl_seconds)
        
        return result
    
    def lookup_property(
        self,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        county: Optional[str] = None,
        apn: Optional[str] = None,
        skip_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Lookup property by address or APN.
        
        Args:
            street: Street address
            city: City name
            state: State name or abbreviation
            zip_code: ZIP code
            county: County name (for APN lookup)
            apn: Assessor Parcel Number
            skip_trace: Include skip trace data
        
        Returns:
            Property data dictionary
        """
        request_data = {"requests": []}
        
        if apn and county:
            request_data["requests"].append({
                "address": {"county": county, "state": state},
                "apn": apn
            })
        elif street:
            request_data["requests"].append({
                "address": {
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }
            })
        else:
            raise ValueError("Either provide street address details or APN with county")
        
        if skip_trace:
            request_data["options"] = {"skipTrace": True}
        
        return self._make_request("/property/lookup/sync", request_data)
    
    def verify_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str
    ) -> Dict[str, Any]:
        """
        Verify and standardize address using USPS verification.
        
        Args:
            street: Street address
            city: City name
            state: State name or abbreviation
            zip_code: ZIP code
        
        Returns:
            Verified address data
        """
        request_data = {
            "requests": [{
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code
            }]
        }
        
        return self._make_request("/address/verify", request_data)
    
    def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Convert address to latitude/longitude coordinates.
        
        Args:
            address: Full address string
        
        Returns:
            Geocoding result with coordinates
        """
        request_data = {"requests": [{"address": address}]}
        
        return self._make_request("/address/geocode", request_data, use_cache=True)
    
    def search_properties(
        self,
        query: Optional[str] = None,
        comp_street: Optional[str] = None,
        comp_city: Optional[str] = None,
        comp_state: Optional[str] = None,
        comp_zip: Optional[str] = None,
        min_estimated_value: Optional[float] = None,
        max_estimated_value: Optional[float] = None,
        property_type: Optional[str] = None,
        distance_miles: Optional[float] = None,
        skip: int = 0,
        take: int = 10
    ) -> Dict[str, Any]:
        """
        Search for properties with filters.
        
        Args:
            query: Location query (city, state, etc.)
            comp_street: Comparison property street address
            comp_city: Comparison property city
            comp_state: Comparison property state
            comp_zip: Comparison property ZIP
            min_estimated_value: Minimum estimated property value
            max_estimated_value: Maximum estimated property value
            property_type: Property type (e.g., "Single Family")
            distance_miles: Distance in miles for comparison
            skip: Number of results to skip
            take: Number of results to return
        
        Returns:
            Search results
        """
        search_criteria = {}
        options = {"skip": skip, "take": take}
        
        if query:
            search_criteria["query"] = query
        
        if comp_street:
            search_criteria["compAddress"] = {
                "street": comp_street,
                "city": comp_city,
                "state": comp_state,
                "zip": comp_zip
            }
        
        if min_estimated_value or max_estimated_value:
            search_criteria["valuation"] = {"estimatedValue": {}}
            if min_estimated_value:
                search_criteria["valuation"]["estimatedValue"]["min"] = min_estimated_value
            if max_estimated_value:
                search_criteria["valuation"]["estimatedValue"]["max"] = max_estimated_value
        
        if property_type:
            search_criteria["general"] = {"propertyTypeDetail": {"equals": property_type}}
        
        if distance_miles:
            options["useDistance"] = True
            options["distanceMiles"] = distance_miles
        
        request_data = {
            "searchCriteria": search_criteria,
            "options": options
        }
        
        return self._make_request("/property/search/sync", request_data)

