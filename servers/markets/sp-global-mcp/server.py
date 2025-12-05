#!/usr/bin/env python3
"""
S&P Global MCP Server

MCP server for accessing S&P Global Market Intelligence data including:
- S&P Capital IQ company data and search
- Company fundamentals
- Earnings transcripts

Built by: Kensho (S&P Global's AI Innovation Hub)
Official Partnership: Anthropic + S&P Global (July 2025)

⚠️ ENTERPRISE LICENSE REQUIRED: This server requires an active S&P Global Market Intelligence subscription.
Access is provided through S&P Global Market Intelligence API.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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

# Import S&P Global API client
from sp_global_client import SPGlobalClient


# Initialize S&P Global client
_client: Optional[SPGlobalClient] = None


def get_client() -> SPGlobalClient:
    """Get or create S&P Global API client."""
    global _client
    if _client is None:
        api_key = os.getenv("SP_GLOBAL_API_KEY")
        if not api_key:
            raise ValueError(
                "SP_GLOBAL_API_KEY environment variable is required. "
                "Please set your S&P Global Market Intelligence API key."
            )
        _client = SPGlobalClient(api_key=api_key)
    return _client


# Tool implementations
async def sp_global_search_companies(
    query: str,
    country: Optional[str] = None,
    sector: Optional[str] = None,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """
    Search for companies using S&P Capital IQ.
    
    Args:
        query: Company name, ticker, or CIQ identifier to search for
        country: Filter by country code (ISO 3166-1 alpha-2, e.g., "US", "GB")
        sector: Filter by industry sector (e.g., "Technology", "Healthcare")
        limit: Maximum number of results to return (default: 20, max: 100)
    
    Returns:
        Dictionary with list of companies matching the search criteria
    """
    try:
        client = get_client()
        result = client.search_companies(
            query=query,
            country=country,
            sector=sector,
            limit=limit or 20
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "count": 0,
            "companies": []
        }


async def sp_global_get_fundamentals(
    company_id: str,
    period_type: str = "Annual",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get company fundamentals from S&P Capital IQ.
    
    Args:
        company_id: S&P Capital IQ company identifier (CIQ ID)
        period_type: Period type - "Annual" or "Quarterly" (default: "Annual")
        start_date: Start date for data range (ISO 8601 format: YYYY-MM-DD)
        end_date: End date for data range (ISO 8601 format: YYYY-MM-DD)
        metrics: List of specific financial metrics to retrieve (if None, returns all available)
    
    Returns:
        Dictionary with company fundamentals data
    """
    try:
        client = get_client()
        result = client.get_fundamentals(
            company_id=company_id,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "company_id": company_id,
            "fundamentals": {}
        }


async def sp_global_get_earnings_transcripts(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 10
) -> Dict[str, Any]:
    """
    Get earnings call transcripts for a company.
    
    Args:
        company_id: S&P Capital IQ company identifier (CIQ ID)
        start_date: Start date for transcript search (ISO 8601 format: YYYY-MM-DD)
        end_date: End date for transcript search (ISO 8601 format: YYYY-MM-DD)
        limit: Maximum number of transcripts to return (default: 10, max: 50)
    
    Returns:
        Dictionary with earnings call transcripts
    """
    try:
        client = get_client()
        result = client.get_earnings_transcripts(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit or 10
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "company_id": company_id,
            "transcripts": []
        }


async def sp_global_get_company_profile(
    company_id: str
) -> Dict[str, Any]:
    """
    Get comprehensive company profile from S&P Capital IQ.
    
    Args:
        company_id: S&P Capital IQ company identifier (CIQ ID)
    
    Returns:
        Dictionary with comprehensive company profile data
    """
    try:
        client = get_client()
        result = client.get_company_profile(company_id=company_id)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "company_id": company_id,
            "profile": {}
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("sp-global-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="sp_global_search_companies",
                description="Search for companies using S&P Capital IQ by name, ticker, or CIQ ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Company name, ticker symbol, or CIQ identifier to search for"
                        },
                        "country": {
                            "type": "string",
                            "description": "Filter by country code (ISO 3166-1 alpha-2, e.g., 'US', 'GB')",
                            "pattern": "^[A-Z]{2}$"
                        },
                        "sector": {
                            "type": "string",
                            "description": "Filter by industry sector (e.g., 'Technology', 'Healthcare', 'Financial Services')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sp_global_get_fundamentals",
                description="Get company fundamentals data from S&P Capital IQ (financial statements, ratios, metrics)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "S&P Capital IQ company identifier (CIQ ID)"
                        },
                        "period_type": {
                            "type": "string",
                            "enum": ["Annual", "Quarterly"],
                            "default": "Annual",
                            "description": "Period type for financial data"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Start date for data range (ISO 8601 format: YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "description": "End date for data range (ISO 8601 format: YYYY-MM-DD)"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of specific financial metrics to retrieve (if empty, returns all available)"
                        }
                    },
                    "required": ["company_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sp_global_get_earnings_transcripts",
                description="Get earnings call transcripts for a company from S&P Capital IQ",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "S&P Capital IQ company identifier (CIQ ID)"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Start date for transcript search (ISO 8601 format: YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "description": "End date for transcript search (ISO 8601 format: YYYY-MM-DD)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of transcripts to return",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        }
                    },
                    "required": ["company_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sp_global_get_company_profile",
                description="Get comprehensive company profile from S&P Capital IQ including company information, executives, ownership, and more",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "S&P Capital IQ company identifier (CIQ ID)"
                        }
                    },
                    "required": ["company_id"],
                    "additionalProperties": False
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "sp_global_search_companies":
                result = await sp_global_search_companies(**arguments)
            elif name == "sp_global_get_fundamentals":
                result = await sp_global_get_fundamentals(**arguments)
            elif name == "sp_global_get_earnings_transcripts":
                result = await sp_global_get_earnings_transcripts(**arguments)
            elif name == "sp_global_get_company_profile":
                result = await sp_global_get_company_profile(**arguments)
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
        
        parser = argparse.ArgumentParser(description="S&P Global MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "search_companies", "get_fundamentals", "get_transcripts", "get_profile"
        ])
        parser.add_argument("--query", help="Search query (for search_companies)")
        parser.add_argument("--company_id", help="Company CIQ ID")
        parser.add_argument("--country", help="Country code filter")
        parser.add_argument("--sector", help="Sector filter")
        parser.add_argument("--limit", type=int, default=20, help="Result limit")
        parser.add_argument("--period_type", default="Annual", choices=["Annual", "Quarterly"], help="Period type")
        parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
        parser.add_argument("--metrics", nargs="+", help="List of metrics to retrieve")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search_companies":
                result = await sp_global_search_companies(
                    query=args.query,
                    country=args.country,
                    sector=args.sector,
                    limit=args.limit
                )
            elif args.tool == "get_fundamentals":
                result = await sp_global_get_fundamentals(
                    company_id=args.company_id,
                    period_type=args.period_type,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    metrics=args.metrics
                )
            elif args.tool == "get_transcripts":
                result = await sp_global_get_earnings_transcripts(
                    company_id=args.company_id,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    limit=args.limit
                )
            elif args.tool == "get_profile":
                result = await sp_global_get_company_profile(company_id=args.company_id)
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

