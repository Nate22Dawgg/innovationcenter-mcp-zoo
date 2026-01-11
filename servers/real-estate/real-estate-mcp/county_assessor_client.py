"""
County Assessor API client for property tax records.

Provides access to county assessor data for property tax records and assessments.
Each county has different API formats - this client handles variations.
"""

import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import get_cache, build_cache_key


class CountyAssessorClient:
    """Client for county assessor APIs."""
    
    def __init__(self, cache=None):
        """
        Initialize county assessor client.
        
        Args:
            cache: Optional cache instance (from common.cache.get_cache())
        """
        self.cache = cache or get_cache()
        self.counties_config = self._load_counties_config()
    
    def _load_counties_config(self) -> Dict[str, Any]:
        """Load county configuration."""
        config_path = Path(__file__).parent / "config" / "counties.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _get_county_config(self, county: str, state: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific county."""
        county_lower = county.lower()
        state_upper = state.upper()
        
        # Try to find matching county
        for key, config in self.counties_config.items():
            if state_upper == config.get("state", "").upper():
                counties_list = [c.lower() for c in config.get("counties", [])]
                if county_lower in counties_list:
                    return config
        
        return None
    
    def get_tax_records(self, address: str, county: str, state: str) -> Dict[str, Any]:
        """
        Get property tax records for an address.
        
        Args:
            address: Property address
            county: County name
            state: State abbreviation
        
        Returns:
            Tax records dictionary
        """
        config = self._get_county_config(county, state)
        if not config:
            return {
                "error": f"County {county}, {state} not yet supported",
                "supported_counties": list(self.counties_config.keys())
            }
        
        # Check cache (365 day TTL for assessor data - changes annually)
        cache_key = {"address": address, "county": county, "state": state}
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_tax_records",
                args=cache_key
            )
            cached = self.cache.get(cache_key_str)
            if cached:
                return cached
        
        # For now, return a stub response indicating county-specific implementation needed
        # In production, this would call county-specific APIs
        result = {
            "address": address,
            "county": county,
            "state": state,
            "status": "stub",
            "note": f"County assessor API for {county}, {state} needs implementation",
            "api_info": config.get("assessor_api", {}),
            "tax_records": None,
            "assessment": None,
            "tax_history": None
        }
        
        # Cache result with 365 day TTL (assessor data changes annually)
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_tax_records",
                args=cache_key
            )
            self.cache.set(cache_key_str, result, ttl_seconds=365 * 24 * 60 * 60)
        
        return result
    
    def get_property_assessment(self, parcel_id: str, county: str, state: str) -> Dict[str, Any]:
        """
        Get property assessment data by parcel ID.
        
        Args:
            parcel_id: Assessor Parcel Number (APN)
            county: County name
            state: State abbreviation
        
        Returns:
            Assessment data dictionary
        """
        config = self._get_county_config(county, state)
        if not config:
            return {
                "error": f"County {county}, {state} not yet supported"
            }
        
        # Check cache (365 day TTL for assessor data)
        cache_key = {"parcel_id": parcel_id, "county": county, "state": state}
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_property_assessment",
                args=cache_key
            )
            cached = self.cache.get(cache_key_str)
            if cached:
                return cached
        
        # Stub implementation
        result = {
            "parcel_id": parcel_id,
            "county": county,
            "state": state,
            "status": "stub",
            "note": f"Property assessment API for {county}, {state} needs implementation",
            "assessment": None,
            "assessed_value": None,
            "tax_year": None
        }
        
        # Cache with 365 day TTL
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_property_assessment",
                args=cache_key
            )
            self.cache.set(cache_key_str, result, ttl_seconds=365 * 24 * 60 * 60)
        
        return result
    
    def get_tax_history(self, parcel_id: str, county: str, state: str, years: int = 5) -> Dict[str, Any]:
        """
        Get tax payment history for a property.
        
        Args:
            parcel_id: Assessor Parcel Number
            county: County name
            state: State abbreviation
            years: Number of years of history to retrieve
        
        Returns:
            Tax history dictionary
        """
        config = self._get_county_config(county, state)
        if not config:
            return {
                "error": f"County {county}, {state} not yet supported"
            }
        
        # Check cache (365 day TTL for assessor data)
        cache_key = {"parcel_id": parcel_id, "county": county, "state": state, "years": years}
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_tax_history",
                args=cache_key
            )
            cached = self.cache.get(cache_key_str)
            if cached:
                return cached
        
        # Stub implementation
        result = {
            "parcel_id": parcel_id,
            "county": county,
            "state": state,
            "years": years,
            "status": "stub",
            "note": f"Tax history API for {county}, {state} needs implementation",
            "tax_history": []
        }
        
        # Cache with 365 day TTL
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_tax_history",
                args=cache_key
            )
            self.cache.set(cache_key_str, result, ttl_seconds=365 * 24 * 60 * 60)
        
        return result

