#!/usr/bin/env python3
"""
Real Estate MCP Server

Extended MCP server for real estate data with multiple data sources:
- BatchData.io (paid, comprehensive)
- County Assessor APIs (free, property tax records)
- GIS APIs (free, parcel information)
- Redfin Data Center (free, market trends)

Provides tools for property lookup, tax records, parcel info, market trends, and recent sales.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading and common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data_source_router import DataSourceRouter
from cache import Cache
from config import load_config, RealEstateConfig
from common.config import validate_config_or_raise, ConfigValidationError
from common.errors import ErrorCode
from common.logging import get_logger
from investment_analysis import generate_property_investment_brief, compare_properties

logger = get_logger(__name__)

# Try to import MCP SDK - fallback to basic implementation if not available
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    # Fallback: create minimal MCP-like interface
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not found. Install with: pip install mcp", file=sys.stderr)


# Load schemas
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


# Initialize router and cache
_cache: Optional[Cache] = None
_router: Optional[DataSourceRouter] = None
_config: Optional[RealEstateConfig] = None
_config_error_payload: Optional[Dict[str, Any]] = None


def get_config() -> RealEstateConfig:
    """Get or load server configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_router() -> DataSourceRouter:
    """Get or create data source router."""
    global _router
    if _router is None:
        global _cache
        if _cache is None:
            _cache = Cache()
        _router = DataSourceRouter(cache=_cache)
    return _router


# Tool implementations
async def real_estate_property_lookup(
    address: str,
    county: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lookup property by address using BatchData.io API.
    
    Args:
        address: Full property address (e.g., "123 Main St, New York, NY 10001")
        county: County name (optional, helps with routing)
        state: State abbreviation (optional, helps with routing)
    
    Returns:
        Dictionary with comprehensive property data
    """
    try:
        router = get_router()
        result = router.get_property_lookup(address, county, state)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "address": address
        }


async def real_estate_address_enrichment(
    partial_address: str
) -> Dict[str, Any]:
    """
    Enrich and verify a partial address using BatchData.io API.
    
    Args:
        partial_address: Partial or incomplete address
    
    Returns:
        Dictionary with verified and enriched address data
    """
    try:
        router = get_router()
        batchdata = router._get_batchdata_client()
        if batchdata:
            # Try autocomplete first
            # Note: BatchData autocomplete API format may differ
            # For now, use geocode as fallback
            result = batchdata.geocode_address(partial_address)
            return {
                "original": partial_address,
                "enriched": result,
                "source": "batchdata"
            }
        else:
            return {
                "error": "BatchData.io API key required for address enrichment",
                "original": partial_address
            }
    except Exception as e:
        return {
            "error": str(e),
            "original": partial_address
        }


async def real_estate_get_tax_records(
    address: str,
    county: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get property tax records for an address.
    Tries county assessor APIs first (free), falls back to BatchData.io.
    
    Args:
        address: Property address
        county: County name (required for county assessor lookup)
        state: State abbreviation (required for county assessor lookup)
    
    Returns:
        Dictionary with tax records and assessment data
    """
    try:
        router = get_router()
        result = router.get_tax_records(address, county, state)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "address": address
        }


async def real_estate_get_parcel_info(
    address: str,
    county: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get parcel information for an address.
    Tries GIS APIs first (free), falls back to BatchData.io.
    
    Args:
        address: Property address
        county: County name (required for GIS lookup)
        state: State abbreviation (required for GIS lookup)
    
    Returns:
        Dictionary with parcel ID, boundaries, and GIS data
    """
    try:
        router = get_router()
        result = router.get_parcel_info(address, county, state)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "address": address
        }


async def real_estate_search_recent_sales(
    zip_code: str,
    days: int = 90,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for recent property sales in a ZIP code.
    Uses Redfin Data Center (free) or BatchData.io as fallback.
    
    Args:
        zip_code: ZIP code to search
        days: Number of days to look back (default: 90)
        limit: Maximum number of results (default: 10)
    
    Returns:
        Dictionary with recent sales data
    """
    try:
        router = get_router()
        result = router.search_recent_sales(zip_code, days, limit)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "zip_code": zip_code
        }


async def real_estate_get_market_trends(
    zip_code: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get market trends for a location.
    Uses Redfin Data Center (free).
    
    Args:
        zip_code: ZIP code (preferred)
        city: City name (if no ZIP code)
        state: State abbreviation (required if using city)
    
    Returns:
        Dictionary with market trends and statistics
    """
    try:
        router = get_router()
        result = router.get_market_trends(zip_code, city, state)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "zip_code": zip_code,
            "city": city,
            "state": state
        }


async def real_estate_generate_property_investment_brief(
    address: str,
    property_id: Optional[str] = None,
    county: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive investment brief for a property.
    
    Aggregates data from multiple sources:
    - Property lookup
    - Tax records
    - Recent sales
    - Market trends
    
    Produces investment metrics including yield estimates, IRR heuristics, and red flags.
    
    Args:
        address: Property address or property ID
        property_id: Optional property ID (APN or other identifier)
        county: County name (optional, helps with routing)
        state: State abbreviation (optional, helps with routing)
    
    Returns:
        PropertyInvestmentBrief dictionary
    """
    try:
        router = get_router()
        result = await generate_property_investment_brief(
            address=address,
            property_id=property_id,
            county=county,
            state=state,
            router=router
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "address": address
        }


async def real_estate_compare_properties(
    properties: List[str],
    county: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare multiple properties side-by-side for investment analysis.
    
    Args:
        properties: List of property addresses or property IDs (2-10 properties)
        county: County name (optional, if all properties are in same county)
        state: State abbreviation (optional, if all properties are in same state)
    
    Returns:
        PropertyComparison dictionary with per-property metrics and summary
    """
    try:
        if len(properties) < 2:
            return {
                "error": "At least 2 properties required for comparison",
                "properties": properties
            }
        if len(properties) > 10:
            return {
                "error": "Maximum 10 properties allowed for comparison",
                "properties": properties
            }
        
        router = get_router()
        result = await compare_properties(
            properties=properties,
            county=county,
            state=state,
            router=router
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "properties": properties
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("real-estate-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="real_estate_property_lookup",
                description="Lookup comprehensive property data by address using BatchData.io API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Full property address (e.g., '123 Main St, New York, NY 10001')"
                        },
                        "county": {
                            "type": "string",
                            "description": "County name (optional, helps with routing)"
                        },
                        "state": {
                            "type": "string",
                            "description": "State abbreviation (optional, helps with routing)"
                        }
                    },
                    "required": ["address"]
                }
            ),
            Tool(
                name="real_estate_address_enrichment",
                description="Enrich and verify a partial address using BatchData.io API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "partial_address": {
                            "type": "string",
                            "description": "Partial or incomplete address"
                        }
                    },
                    "required": ["partial_address"]
                }
            ),
            Tool(
                name="real_estate_get_tax_records",
                description="Get property tax records for an address. Tries county assessor APIs first (free), falls back to BatchData.io",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Property address"
                        },
                        "county": {
                            "type": "string",
                            "description": "County name (required for county assessor lookup)"
                        },
                        "state": {
                            "type": "string",
                            "description": "State abbreviation (required for county assessor lookup)"
                        }
                    },
                    "required": ["address"]
                }
            ),
            Tool(
                name="real_estate_get_parcel_info",
                description="Get parcel information for an address. Tries GIS APIs first (free), falls back to BatchData.io",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Property address"
                        },
                        "county": {
                            "type": "string",
                            "description": "County name (required for GIS lookup)"
                        },
                        "state": {
                            "type": "string",
                            "description": "State abbreviation (required for GIS lookup)"
                        }
                    },
                    "required": ["address"]
                }
            ),
            Tool(
                name="real_estate_search_recent_sales",
                description="Search for recent property sales in a ZIP code. Uses Redfin Data Center (free) or BatchData.io as fallback",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code to search"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 90)",
                            "default": 90,
                            "minimum": 1,
                            "maximum": 365
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["zip_code"]
                }
            ),
            Tool(
                name="real_estate_get_market_trends",
                description="Get market trends for a location. Uses Redfin Data Center (free)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code (preferred)"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name (if no ZIP code)"
                        },
                        "state": {
                            "type": "string",
                            "description": "State abbreviation (required if using city)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="real_estate_generate_property_investment_brief",
                description="Generate a comprehensive investment brief for a property. Aggregates property data, tax records, recent sales, and market trends to produce investment metrics including yield estimates, IRR heuristics, and red flags.",
                inputSchema=brief_input_schema
            ),
            Tool(
                name="real_estate_compare_properties",
                description="Compare multiple properties side-by-side for investment analysis. Provides per-property metrics and summary recommendations to help choose the best investment.",
                inputSchema=compare_input_schema
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            # Check for configuration errors (fail-soft behavior)
            if _config_error_payload and name in [
                "real_estate_property_lookup",
                "real_estate_address_enrichment",
                "real_estate_generate_property_investment_brief"
            ]:
                # These tools may require BatchData API key
                return [TextContent(
                    type="text",
                    text=json.dumps(_config_error_payload, indent=2)
                )]
            
            if name == "real_estate_property_lookup":
                result = await real_estate_property_lookup(**arguments)
            elif name == "real_estate_address_enrichment":
                result = await real_estate_address_enrichment(**arguments)
            elif name == "real_estate_get_tax_records":
                result = await real_estate_get_tax_records(**arguments)
            elif name == "real_estate_get_parcel_info":
                result = await real_estate_get_parcel_info(**arguments)
            elif name == "real_estate_search_recent_sales":
                result = await real_estate_search_recent_sales(**arguments)
            elif name == "real_estate_get_market_trends":
                result = await real_estate_get_market_trends(**arguments)
            elif name == "real_estate_generate_property_investment_brief":
                result = await real_estate_generate_property_investment_brief(**arguments)
            elif name == "real_estate_compare_properties":
                result = await real_estate_compare_properties(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    async def main():
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    if __name__ == "__main__":
        asyncio.run(main())

else:
    # Fallback: Simple CLI interface for testing
    async def main():
        """Simple CLI interface for testing."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Real Estate MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "property_lookup", "address_enrichment", "get_tax_records",
            "get_parcel_info", "search_recent_sales", "get_market_trends"
        ])
        parser.add_argument("--address", help="Property address")
        parser.add_argument("--partial_address", help="Partial address")
        parser.add_argument("--county", help="County name")
        parser.add_argument("--state", help="State abbreviation")
        parser.add_argument("--zip_code", help="ZIP code")
        parser.add_argument("--city", help="City name")
        parser.add_argument("--days", type=int, default=90, help="Days to look back")
        parser.add_argument("--limit", type=int, default=10, help="Result limit")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "property_lookup":
                result = await real_estate_property_lookup(
                    address=args.address,
                    county=args.county,
                    state=args.state
                )
            elif args.tool == "address_enrichment":
                result = await real_estate_address_enrichment(
                    partial_address=args.partial_address
                )
            elif args.tool == "get_tax_records":
                result = await real_estate_get_tax_records(
                    address=args.address,
                    county=args.county,
                    state=args.state
                )
            elif args.tool == "get_parcel_info":
                result = await real_estate_get_parcel_info(
                    address=args.address,
                    county=args.county,
                    state=args.state
                )
            elif args.tool == "search_recent_sales":
                result = await real_estate_search_recent_sales(
                    zip_code=args.zip_code,
                    days=args.days,
                    limit=args.limit
                )
            elif args.tool == "get_market_trends":
                result = await real_estate_get_market_trends(
                    zip_code=args.zip_code,
                    city=args.city,
                    state=args.state
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

