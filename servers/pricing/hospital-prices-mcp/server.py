#!/usr/bin/env python3
"""
Hospital Pricing MCP Server

MCP server for accessing hospital price transparency data via Turquoise Health API.
Provides tools for searching, comparing, and estimating hospital procedure prices.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from turquoise_client import TurquoiseHealthClient

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


# Initialize Turquoise Health client
_client: Optional[TurquoiseHealthClient] = None


def get_client() -> TurquoiseHealthClient:
    """Get or create Turquoise Health API client."""
    global _client
    if _client is None:
        _client = TurquoiseHealthClient()
    return _client


# Tool implementations
async def hospital_prices_search_procedure(
    cpt_code: str,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    zip_code: Optional[str] = None,
    state: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search for hospital procedure prices by CPT code and location.
    
    Args:
        cpt_code: CPT or HCPCS procedure code (e.g., "99213")
        location: Location string (city, state or zip code)
        radius: Search radius in miles (default: 25)
        zip_code: ZIP code for location-based search
        state: US state code (2 letters)
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with search results containing hospitals and prices
    """
    try:
        client = get_client()
        result = client.search_procedure_price(
            cpt_code=cpt_code,
            location=location,
            radius=radius,
            zip_code=zip_code,
            state=state
        )
        
        # Apply limit if specified
        if limit and limit > 0:
            result["prices"] = result["prices"][:limit]
            result["count"] = len(result["prices"])
        
        return result
    except Exception as e:
        return {
            "error": str(e),
            "count": 0,
            "total": 0,
            "prices": []
        }


async def hospital_prices_get_rates(
    hospital_id: str,
    cpt_codes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get hospital rate sheet for a specific hospital and optional CPT codes.
    
    Args:
        hospital_id: Turquoise Health hospital identifier
        cpt_codes: Optional list of CPT codes to filter rates
    
    Returns:
        Dictionary with hospital information and rates
    """
    try:
        client = get_client()
        result = client.get_hospital_rates(
            hospital_id=hospital_id,
            cpt_codes=cpt_codes
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "hospital_id": hospital_id,
            "count": 0,
            "prices": []
        }


async def hospital_prices_compare(
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
    try:
        client = get_client()
        result = client.compare_prices(
            cpt_code=cpt_code,
            location=location,
            limit=limit,
            zip_code=zip_code,
            state=state
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "procedure_code": cpt_code,
            "count": 0,
            "comparisons": []
        }


async def hospital_prices_estimate_cash(
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
    try:
        client = get_client()
        result = client.estimate_cash_price(
            cpt_code=cpt_code,
            location=location,
            zip_code=zip_code,
            state=state
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "procedure_code": cpt_code,
            "location": location,
            "estimate": {}
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("hospital-pricing-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="hospital_prices_search_procedure",
                description="Search for hospital procedure prices by CPT code and location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code (e.g., '99213')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in miles (default: 25)",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 200
                        }
                    },
                    "required": ["cpt_code"]
                }
            ),
            Tool(
                name="hospital_prices_get_rates",
                description="Get hospital rate sheet for a specific hospital and optional CPT codes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hospital_id": {
                            "type": "string",
                            "description": "Turquoise Health hospital identifier"
                        },
                        "cpt_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of CPT codes to filter rates"
                        }
                    },
                    "required": ["hospital_id"]
                }
            ),
            Tool(
                name="hospital_prices_compare",
                description="Compare prices for a procedure across multiple facilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        }
                    },
                    "required": ["cpt_code", "location"]
                }
            ),
            Tool(
                name="hospital_prices_estimate_cash",
                description="Estimate cash price range for a procedure in a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        }
                    },
                    "required": ["cpt_code", "location"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "hospital_prices_search_procedure":
                result = await hospital_prices_search_procedure(**arguments)
            elif name == "hospital_prices_get_rates":
                result = await hospital_prices_get_rates(**arguments)
            elif name == "hospital_prices_compare":
                result = await hospital_prices_compare(**arguments)
            elif name == "hospital_prices_estimate_cash":
                result = await hospital_prices_estimate_cash(**arguments)
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
        
        parser = argparse.ArgumentParser(description="Hospital Pricing MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "search", "get_rates", "compare", "estimate"
        ])
        parser.add_argument("--cpt_code", help="CPT code")
        parser.add_argument("--location", help="Location")
        parser.add_argument("--hospital_id", help="Hospital ID")
        parser.add_argument("--radius", type=int, help="Radius in miles")
        parser.add_argument("--limit", type=int, default=10, help="Result limit")
        parser.add_argument("--zip_code", help="ZIP code")
        parser.add_argument("--state", help="State code")
        parser.add_argument("--cpt_codes", nargs="+", help="List of CPT codes")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search":
                result = await hospital_prices_search_procedure(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    radius=args.radius,
                    zip_code=args.zip_code,
                    state=args.state,
                    limit=args.limit
                )
            elif args.tool == "get_rates":
                result = await hospital_prices_get_rates(
                    hospital_id=args.hospital_id,
                    cpt_codes=args.cpt_codes
                )
            elif args.tool == "compare":
                result = await hospital_prices_compare(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    limit=args.limit,
                    zip_code=args.zip_code,
                    state=args.state
                )
            elif args.tool == "estimate":
                result = await hospital_prices_estimate_cash(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    zip_code=args.zip_code,
                    state=args.state
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

