"""
Data source router for intelligently routing queries to the best data source.

Prioritizes free sources over paid sources, and local sources over remote sources.
Falls back to BatchData.io if free sources fail or aren't available.
"""

from typing import Dict, Any, Optional, Tuple
from batchdata_client import BatchDataClient
from county_assessor_client import CountyAssessorClient
from gis_client import GISClient
from redfin_client import RedfinClient


class DataSourceRouter:
    """Routes queries to appropriate data sources."""
    
    def __init__(self, cache=None):
        """
        Initialize data source router.
        
        Args:
            cache: Optional cache instance (from common.cache.get_cache())
        """
        self.cache = cache
        self.batchdata_client = None  # Lazy initialization (requires API key)
        self.county_assessor_client = CountyAssessorClient(cache)
        self.gis_client = GISClient(cache)
        self.redfin_client = RedfinClient(cache)
    
    def _get_batchdata_client(self) -> Optional[BatchDataClient]:
        """Get BatchData client (lazy initialization)."""
        if self.batchdata_client is None:
            try:
                self.batchdata_client = BatchDataClient(cache=self.cache)
            except ValueError:
                # API key not available
                pass
        return self.batchdata_client
    
    def get_tax_records(self, address: str, county: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tax records - tries county assessor first, falls back to BatchData.
        
        Args:
            address: Property address
            county: County name (optional, will try to infer)
            state: State abbreviation (optional, will try to infer)
        
        Returns:
            Tax records dictionary
        """
        # Try county assessor first (free)
        if county and state:
            result = self.county_assessor_client.get_tax_records(address, county, state)
            if "error" not in result or "not yet supported" not in result.get("error", ""):
                return result
        
        # Fall back to BatchData (paid)
        batchdata = self._get_batchdata_client()
        if batchdata:
            try:
                # Parse address to extract components
                parts = address.split(",")
                if len(parts) >= 3:
                    street = parts[0].strip()
                    city = parts[1].strip()
                    state_zip = parts[2].strip().split()
                    state_code = state_zip[0] if state_zip else state
                    zip_code = state_zip[1] if len(state_zip) > 1 else None
                    
                    property_data = batchdata.lookup_property(
                        street=street,
                        city=city,
                        state=state_code or state,
                        zip_code=zip_code
                    )
                    
                    # Extract tax-related data from property lookup
                    return {
                        "address": address,
                        "source": "batchdata",
                        "tax_records": property_data.get("tax", {}),
                        "assessment": property_data.get("assessment", {}),
                        "property_data": property_data
                    }
            except Exception as e:
                return {"error": str(e), "source": "batchdata"}
        
        return {
            "error": "Unable to retrieve tax records - no available data sources",
            "address": address
        }
    
    def get_parcel_info(self, address: str, county: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Get parcel information - tries GIS first, falls back to BatchData.
        
        Args:
            address: Property address
            county: County name (optional)
            state: State abbreviation (optional)
        
        Returns:
            Parcel information dictionary
        """
        # Try GIS first (free)
        if county and state:
            result = self.gis_client.get_parcel_info(address, county, state)
            if "error" not in result or "not yet supported" not in result.get("error", ""):
                return result
        
        # Fall back to BatchData
        batchdata = self._get_batchdata_client()
        if batchdata:
            try:
                parts = address.split(",")
                if len(parts) >= 3:
                    street = parts[0].strip()
                    city = parts[1].strip()
                    state_zip = parts[2].strip().split()
                    state_code = state_zip[0] if state_zip else state
                    zip_code = state_zip[1] if len(state_zip) > 1 else None
                    
                    property_data = batchdata.lookup_property(
                        street=street,
                        city=city,
                        state=state_code or state,
                        zip_code=zip_code
                    )
                    
                    return {
                        "address": address,
                        "source": "batchdata",
                        "parcel_id": property_data.get("apn"),
                        "parcel_info": property_data
                    }
            except Exception as e:
                return {"error": str(e), "source": "batchdata"}
        
        return {
            "error": "Unable to retrieve parcel info - no available data sources",
            "address": address
        }
    
    def get_property_lookup(self, address: str, county: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Lookup property - uses BatchData (primary source for comprehensive data).
        
        Args:
            address: Property address
            county: County name (optional)
            state: State abbreviation (optional)
        
        Returns:
            Property data dictionary
        """
        batchdata = self._get_batchdata_client()
        if batchdata:
            try:
                parts = address.split(",")
                if len(parts) >= 3:
                    street = parts[0].strip()
                    city = parts[1].strip()
                    state_zip = parts[2].strip().split()
                    state_code = state_zip[0] if state_zip else state
                    zip_code = state_zip[1] if len(state_zip) > 1 else None
                    
                    return batchdata.lookup_property(
                        street=street,
                        city=city,
                        state=state_code or state,
                        zip_code=zip_code
                    )
            except Exception as e:
                return {"error": str(e), "source": "batchdata"}
        
        return {
            "error": "BatchData.io API key required for property lookup",
            "address": address
        }
    
    def get_market_trends(self, zip_code: Optional[str] = None, city: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market trends - uses Redfin (free source).
        
        Args:
            zip_code: ZIP code (preferred)
            city: City name (if no ZIP)
            state: State abbreviation
        
        Returns:
            Market trends dictionary
        """
        if zip_code:
            return self.redfin_client.get_market_trends(zip_code)
        elif city and state:
            return self.redfin_client.get_neighborhood_stats(city, state)
        else:
            return {
                "error": "Either zip_code or city+state required for market trends"
            }
    
    def search_recent_sales(self, zip_code: str, days: int = 90, limit: int = 10) -> Dict[str, Any]:
        """
        Search for recent sales - uses Redfin first, falls back to BatchData.
        
        Args:
            zip_code: ZIP code
            days: Number of days to look back
            limit: Maximum number of results
        
        Returns:
            Recent sales data
        """
        # Try Redfin first (free)
        result = self.redfin_client.search_recent_sales(zip_code, days, limit)
        if result.get("status") != "stub" or result.get("count", 0) > 0:
            return result
        
        # Fall back to BatchData
        batchdata = self._get_batchdata_client()
        if batchdata:
            try:
                # Use BatchData property search with filters
                search_result = batchdata.search_properties(
                    query=zip_code,
                    take=limit
                )
                
                return {
                    "zip_code": zip_code,
                    "source": "batchdata",
                    "recent_sales": search_result.get("properties", []),
                    "count": len(search_result.get("properties", []))
                }
            except Exception as e:
                return {"error": str(e), "source": "batchdata"}
        
        return result  # Return Redfin stub result

