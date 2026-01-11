"""
GIS (Geographic Information System) client for parcel information.

Provides access to county GIS APIs for parcel maps and property boundaries.
Most counties use ArcGIS REST APIs with standard formats.
"""

import json
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.http import get
from common.errors import ApiError, map_upstream_error
from common.cache import get_cache, build_cache_key


class GISClient:
    """Client for county GIS APIs."""
    
    def __init__(self, cache=None):
        """
        Initialize GIS client.
        
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
        
        for key, config in self.counties_config.items():
            if state_upper == config.get("state", "").upper():
                counties_list = [c.lower() for c in config.get("counties", [])]
                if county_lower in counties_list:
                    return config
        
        return None
    
    def _query_arcgis(self, base_url: str, layer: str, where_clause: str, out_fields: str = "*") -> Dict[str, Any]:
        """Query ArcGIS REST API using common HTTP wrapper."""
        url = f"{base_url}/{layer}/query"
        params = {
            "where": where_clause,
            "outFields": out_fields,
            "f": "json",
            "returnGeometry": "true"
        }
        
        try:
            response = get(
                url=url,
                upstream="arcgis",
                timeout=30.0,
                params=params
            )
            return response.json()
        except ApiError as e:
            # Re-raise ApiError as-is (already standardized)
            raise
        except Exception as e:
            # Map unexpected errors to structured errors
            mapped_error = map_upstream_error(e)
            if mapped_error:
                raise mapped_error
            return {"error": str(e), "status": "error"}
    
    def get_parcel_info(self, address: str, county: str, state: str) -> Dict[str, Any]:
        """
        Get parcel information for an address.
        
        Args:
            address: Property address
            county: County name
            state: State abbreviation
        
        Returns:
            Parcel information dictionary
        """
        config = self._get_county_config(county, state)
        if not config:
            return {
                "error": f"County {county}, {state} not yet supported",
                "supported_counties": list(self.counties_config.keys())
            }
        
        # Check cache (30 day TTL for GIS data - changes infrequently)
        cache_key = {"address": address, "county": county, "state": state}
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_parcel_info",
                args=cache_key
            )
            cached = self.cache.get(cache_key_str)
            if cached:
                return cached
        
        gis_config = config.get("gis_api", {})
        if gis_config.get("type") == "arcgis":
            base_url = gis_config.get("base_url", "")
            layer = gis_config.get("parcel_layer", "Parcels")
            
            # Try to query by address (format varies by county)
            # This is a simplified query - real implementation would need county-specific address parsing
            where_clause = f"ADDRESS LIKE '%{address.split(',')[0]}%'"
            
            result = self._query_arcgis(base_url, layer, where_clause)
            
            if "error" not in result and result.get("features"):
                parcel_data = {
                    "address": address,
                    "county": county,
                    "state": state,
                    "status": "success",
                    "parcel_id": result["features"][0].get("attributes", {}).get("PARCEL_ID"),
                    "geometry": result["features"][0].get("geometry"),
                    "attributes": result["features"][0].get("attributes", {})
                }
            else:
                parcel_data = {
                    "address": address,
                    "county": county,
                    "state": state,
                    "status": "not_found",
                    "note": "Parcel not found or GIS API query failed",
                    "api_info": gis_config
                }
        else:
            parcel_data = {
                "address": address,
                "county": county,
                "state": state,
                "status": "stub",
                "note": f"GIS API for {county}, {state} needs implementation",
                "api_info": gis_config
            }
        
        # Cache result with 30 day TTL (GIS data changes infrequently)
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_parcel_info",
                args=cache_key
            )
            self.cache.set(cache_key_str, parcel_data, ttl_seconds=30 * 24 * 60 * 60)
        
        return parcel_data
    
    def get_parcel_map(self, parcel_id: str, county: str, state: str) -> Dict[str, Any]:
        """
        Get parcel map/boundary data by parcel ID.
        
        Args:
            parcel_id: Assessor Parcel Number
            county: County name
            state: State abbreviation
        
        Returns:
            Parcel map data with geometry
        """
        config = self._get_county_config(county, state)
        if not config:
            return {
                "error": f"County {county}, {state} not yet supported"
            }
        
        # Check cache (30 day TTL for GIS data)
        cache_key = {"parcel_id": parcel_id, "county": county, "state": state}
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_parcel_map",
                args=cache_key
            )
            cached = self.cache.get(cache_key_str)
            if cached:
                return cached
        
        gis_config = config.get("gis_api", {})
        if gis_config.get("type") == "arcgis":
            base_url = gis_config.get("base_url", "")
            layer = gis_config.get("parcel_layer", "Parcels")
            
            where_clause = f"PARCEL_ID = '{parcel_id}'"
            result = self._query_arcgis(base_url, layer, where_clause)
            
            if "error" not in result and result.get("features"):
                map_data = {
                    "parcel_id": parcel_id,
                    "county": county,
                    "state": state,
                    "status": "success",
                    "geometry": result["features"][0].get("geometry"),
                    "attributes": result["features"][0].get("attributes", {})
                }
            else:
                map_data = {
                    "parcel_id": parcel_id,
                    "county": county,
                    "state": state,
                    "status": "not_found",
                    "note": "Parcel map not found"
                }
        else:
            map_data = {
                "parcel_id": parcel_id,
                "county": county,
                "state": state,
                "status": "stub",
                "note": f"Parcel map API for {county}, {state} needs implementation"
            }
        
        # Cache with 30 day TTL
        if self.cache:
            cache_key_str = build_cache_key(
                server_name="real-estate-mcp",
                tool_name="get_parcel_map",
                args=cache_key
            )
            self.cache.set(cache_key_str, map_data, ttl_seconds=30 * 24 * 60 * 60)
        
        return map_data
    
    def search_parcels_by_criteria(self, criteria: Dict[str, Any], county: str, state: str) -> List[Dict[str, Any]]:
        """
        Search parcels by criteria (e.g., property type, value range).
        
        Args:
            criteria: Search criteria dictionary
            county: County name
            state: State abbreviation
        
        Returns:
            List of matching parcels
        """
        config = self._get_county_config(county, state)
        if not config:
            return []
        
        # Build where clause from criteria
        where_parts = []
        if "min_value" in criteria:
            where_parts.append(f"ASSESSED_VALUE >= {criteria['min_value']}")
        if "max_value" in criteria:
            where_parts.append(f"ASSESSED_VALUE <= {criteria['max_value']}")
        if "property_type" in criteria:
            where_parts.append(f"PROPERTY_TYPE = '{criteria['property_type']}'")
        
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        
        gis_config = config.get("gis_api", {})
        if gis_config.get("type") == "arcgis":
            base_url = gis_config.get("base_url", "")
            layer = gis_config.get("parcel_layer", "Parcels")
            
            result = self._query_arcgis(base_url, layer, where_clause)
            
            if "error" not in result and result.get("features"):
                return [
                    {
                        "parcel_id": feat.get("attributes", {}).get("PARCEL_ID"),
                        "attributes": feat.get("attributes", {}),
                        "geometry": feat.get("geometry")
                    }
                    for feat in result.get("features", [])
                ]
        
        return []

