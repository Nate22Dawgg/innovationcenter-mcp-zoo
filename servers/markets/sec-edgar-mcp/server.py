#!/usr/bin/env python3
"""
SEC EDGAR MCP Server

MCP server for accessing SEC EDGAR filings, company data, and financial information.
Uses free SEC EDGAR API (data.sec.gov) - no authentication required.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import configuration
from config import load_config, SecEdgarConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import DCAP for tool discovery (https://github.com/boorich/dcap)
from common.dcap import (
    register_tools_with_dcap,
    ToolMetadata,
    ToolSignature,
    DCAP_ENABLED,
)

# Import standardized error handling
try:
    from common.errors import (
        McpError,
        map_upstream_error,
        format_error_response,
        ErrorCode,
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    McpError = Exception
    map_upstream_error = None
    format_error_response = None
    ErrorCode = None

from sec_edgar_client import (
    search_company_cik,
    search_company_filings,
    get_filings_by_cik,
    get_filing_content,
    get_company_submissions,
    search_filings_by_keyword,
    extract_financial_data,
    get_company_ticker_info
)

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


# Tool implementations
async def sec_search_company(
    query: str,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """
    Search for companies by name or ticker symbol.
    
    Args:
        query: Company name or ticker symbol
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with list of matching companies
    """
    try:
        # First try to get ticker info if it looks like a ticker
        ticker_info = None
        if len(query) <= 5 and query.isupper():
            ticker_info = get_company_ticker_info(query)
        
        # Search by CIK/name
        cik = search_company_cik(query)
        
        results = []
        if ticker_info:
            results.append({
                "cik": ticker_info.get("cik", ""),
                "ticker": ticker_info.get("ticker", query),
                "name": ticker_info.get("title", ""),
                "exchange": ticker_info.get("exchange", "")
            })
        
        if cik and not ticker_info:
            # Get company info from submissions
            submissions = get_company_submissions(cik)
            if submissions:
                company_info = submissions.get("name", query)
                results.append({
                    "cik": cik,
                    "name": company_info,
                    "ticker": submissions.get("tickers", [""])[0] if submissions.get("tickers") else ""
                })
        
        return {
            "query": query,
            "count": len(results),
            "companies": results[:limit or 20]
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "query": query,
            "count": 0,
            "companies": []
        }


async def sec_get_company_filings(
    company_name: Optional[str] = None,
    cik: Optional[str] = None,
    form_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 50
) -> Dict[str, Any]:
    """
    Get company filings by name or CIK with optional filters.
    
    Args:
        company_name: Company name (alternative to CIK)
        cik: Company CIK (10-digit zero-padded)
        form_type: Form type filter (e.g., "10-K", "10-Q", "8-K", "S-1")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of filings to return
    
    Returns:
        Dictionary with list of filings
    """
    try:
        # Get CIK if company name provided
        if company_name and not cik:
            cik = search_company_cik(company_name)
            if not cik:
                return {
                    "error": f"Company '{company_name}' not found",
                    "count": 0,
                    "filings": []
                }
        
        if not cik:
            return {
                "error": "Either company_name or cik must be provided",
                "count": 0,
                "filings": []
            }
        
        # Get filings
        filings = get_filings_by_cik(cik, form_type=form_type, limit=limit or 50)
        
        # Filter by date if provided
        if start_date or end_date:
            filtered = []
            for filing in filings:
                filing_date = filing.get("filing_date", "")
                if start_date and filing_date < start_date:
                    continue
                if end_date and filing_date > end_date:
                    continue
                filtered.append(filing)
            filings = filtered
        
        return {
            "cik": cik,
            "company_name": company_name,
            "form_type": form_type,
            "count": len(filings),
            "filings": filings
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "count": 0,
            "filings": []
        }


async def sec_get_filing_content(
    cik: str,
    accession_number: str,
    extract_financials: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Get content of a specific filing.
    
    Args:
        cik: Company CIK (10-digit zero-padded)
        accession_number: Filing accession number (e.g., "0001234567-24-000001")
        extract_financials: Whether to extract financial data from filing
    
    Returns:
        Dictionary with filing content and metadata
    """
    try:
        filing = get_filing_content(cik, accession_number)
        
        if not filing:
            return {
                "error": "Filing not found",
                "cik": cik,
                "accession_number": accession_number
            }
        
        result = {
            "cik": cik,
            "accession_number": accession_number,
            "content_length": filing.get("content_length", 0),
            "url": filing.get("url", ""),
            "content_preview": filing.get("content", "")[:5000] if filing.get("content") else ""  # First 5000 chars
        }
        
        # Extract financials if requested
        if extract_financials:
            financials = extract_financial_data(filing)
            result["financial_data"] = financials
        
        return result
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "cik": cik,
            "accession_number": accession_number
        }


async def sec_search_filings(
    keyword: str,
    form_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """
    Search filings by keyword across all companies.
    
    Note: This is a simplified search. Full-text search requires downloading
    and parsing filing content, which can be slow.
    
    Args:
        keyword: Keyword to search for
        form_type: Optional form type filter
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of results
    
    Returns:
        Dictionary with matching filings
    """
    try:
        results = search_filings_by_keyword(
            keyword,
            form_type=form_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit or 20
        )
        
        return {
            "keyword": keyword,
            "form_type": form_type,
            "count": len(results),
            "filings": results
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "keyword": keyword,
            "count": 0,
            "filings": []
        }


async def sec_get_company_info(
    company_name: Optional[str] = None,
    cik: Optional[str] = None,
    ticker: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get comprehensive company information including submissions index.
    
    Args:
        company_name: Company name
        cik: Company CIK
        ticker: Ticker symbol
    
    Returns:
        Dictionary with company information
    """
    try:
        # Get CIK from various inputs
        if ticker:
            ticker_info = get_company_ticker_info(ticker)
            if ticker_info:
                cik = ticker_info.get("cik", "")
        
        if company_name and not cik:
            cik = search_company_cik(company_name)
        
        if not cik:
            return {
                "error": "Could not find company. Provide company_name, cik, or ticker.",
                "company_name": company_name,
                "cik": cik,
                "ticker": ticker
            }
        
        # Get submissions
        submissions = get_company_submissions(cik)
        
        return {
            "cik": cik,
            "company_name": submissions.get("name", company_name or ""),
            "ticker": submissions.get("tickers", [ticker or ""])[0] if submissions.get("tickers") else (ticker or ""),
            "sic": submissions.get("sic", ""),
            "sic_description": submissions.get("sicDescription", ""),
            "exchanges": submissions.get("exchanges", []),
            "filing_count": len(submissions.get("filings", {}).get("recent", {}).get("form", [])) if submissions.get("filings") else 0,
            "submissions": submissions
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "company_name": company_name,
            "cik": cik,
            "ticker": ticker
        }


async def sec_extract_financials(
    cik: str,
    accession_number: str
) -> Dict[str, Any]:
    """
    Extract financial data from a filing (10-K, 10-Q, etc.).
    
    Args:
        cik: Company CIK
        accession_number: Filing accession number
    
    Returns:
        Dictionary with extracted financial data
    """
    try:
        filing = get_filing_content(cik, accession_number)
        
        if not filing:
            return {
                "error": "Filing not found",
                "cik": cik,
                "accession_number": accession_number
            }
        
        financials = extract_financial_data(filing)
        
        return {
            "cik": cik,
            "accession_number": accession_number,
            "financial_data": financials,
            "extraction_method": "pattern_matching",
            "note": "Financial extraction uses pattern matching. For comprehensive XBRL data, consider parsing XBRL files directly."
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "cik": cik,
            "accession_number": accession_number
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("sec-edgar-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="sec_search_company",
                description="Search for companies by name or ticker symbol",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Company name or ticker symbol (e.g., 'Apple', 'AAPL')"
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
                name="sec_get_company_filings",
                description="Get company filings by name or CIK with optional filters (form type, date range)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name (alternative to CIK)"
                        },
                        "cik": {
                            "type": "string",
                            "description": "Company CIK (10-digit zero-padded)"
                        },
                        "form_type": {
                            "type": "string",
                            "description": "Form type filter (e.g., '10-K', '10-Q', '8-K', 'S-1', 'DEF 14A')"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date filter (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date filter (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of filings to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50
                        }
                    },
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sec_get_filing_content",
                description="Get content of a specific filing by CIK and accession number",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cik": {
                            "type": "string",
                            "description": "Company CIK (10-digit zero-padded)"
                        },
                        "accession_number": {
                            "type": "string",
                            "description": "Filing accession number (e.g., '0001234567-24-000001')"
                        },
                        "extract_financials": {
                            "type": "boolean",
                            "description": "Whether to extract financial data from filing",
                            "default": False
                        }
                    },
                    "required": ["cik", "accession_number"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sec_search_filings",
                description="Search filings by keyword across all companies (simplified search)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in filings"
                        },
                        "form_type": {
                            "type": "string",
                            "description": "Optional form type filter"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date filter (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date filter (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20
                        }
                    },
                    "required": ["keyword"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sec_get_company_info",
                description="Get comprehensive company information including submissions index",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name"
                        },
                        "cik": {
                            "type": "string",
                            "description": "Company CIK (10-digit zero-padded)"
                        },
                        "ticker": {
                            "type": "string",
                            "description": "Ticker symbol"
                        }
                    },
                    "additionalProperties": False
                }
            ),
            Tool(
                name="sec_extract_financials",
                description="Extract financial data from a filing (10-K, 10-Q, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cik": {
                            "type": "string",
                            "description": "Company CIK (10-digit zero-padded)"
                        },
                        "accession_number": {
                            "type": "string",
                            "description": "Filing accession number"
                        }
                    },
                    "required": ["cik", "accession_number"],
                    "additionalProperties": False
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "sec_search_company":
                result = await sec_search_company(**arguments)
            elif name == "sec_get_company_filings":
                result = await sec_get_company_filings(**arguments)
            elif name == "sec_get_filing_content":
                result = await sec_get_filing_content(**arguments)
            elif name == "sec_search_filings":
                result = await sec_search_filings(**arguments)
            elif name == "sec_get_company_info":
                result = await sec_get_company_info(**arguments)
            elif name == "sec_extract_financials":
                result = await sec_extract_financials(**arguments)
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
    
    # DCAP v3.1 Tool Metadata for semantic discovery
    DCAP_TOOLS = [
        ToolMetadata(
            name="sec_search_company",
            description="Search for companies by name or ticker symbol",
            triggers=["SEC company", "find company CIK", "ticker lookup", "company search"],
            signature=ToolSignature(input="Query", output="Maybe<CompanyList>", cost=0)
        ),
        ToolMetadata(
            name="sec_get_company_filings",
            description="Get company filings by name or CIK with optional filters",
            triggers=["SEC filings", "10-K", "10-Q", "8-K", "company filings", "annual report"],
            signature=ToolSignature(input="FilingsQuery", output="Maybe<FilingsList>", cost=0)
        ),
        ToolMetadata(
            name="sec_get_filing_content",
            description="Get content of a specific SEC filing",
            triggers=["filing content", "SEC document", "read filing"],
            signature=ToolSignature(input="FilingRef", output="Maybe<FilingContent>", cost=0)
        ),
        ToolMetadata(
            name="sec_search_filings",
            description="Search filings by keyword across all companies",
            triggers=["search filings", "SEC keyword search", "filing search"],
            signature=ToolSignature(input="KeywordQuery", output="Maybe<FilingsList>", cost=0)
        ),
        ToolMetadata(
            name="sec_get_company_info",
            description="Get comprehensive company information including submissions index",
            triggers=["company info", "SEC company data", "company submissions"],
            signature=ToolSignature(input="CompanyRef", output="Maybe<CompanyInfo>", cost=0)
        ),
        ToolMetadata(
            name="sec_extract_financials",
            description="Extract financial data from a filing (10-K, 10-Q)",
            triggers=["extract financials", "financial data", "SEC financials", "earnings data"],
            signature=ToolSignature(input="FilingRef", output="Maybe<Financials>", cost=0)
        ),
    ]

    async def main():
        """Run the MCP server."""
        # Load and validate configuration (fail-fast by default)
        try:
            config = load_config()
            validate_config_or_raise(config, fail_fast=True)
        except ConfigValidationError as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Register tools with DCAP for dynamic discovery
        if DCAP_ENABLED:
            registered = register_tools_with_dcap(
                server_id="sec-edgar-mcp",
                tools=DCAP_TOOLS,
                base_command="python servers/markets/sec-edgar-mcp/server.py"
            )
            print(f"DCAP: Registered {registered} tools with relay", file=sys.stderr)
        
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
        
        parser = argparse.ArgumentParser(description="SEC EDGAR MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "search_company", "get_filings", "get_content", "search_filings",
            "get_company_info", "extract_financials"
        ])
        parser.add_argument("--query", help="Search query")
        parser.add_argument("--company_name", help="Company name")
        parser.add_argument("--cik", help="Company CIK")
        parser.add_argument("--ticker", help="Ticker symbol")
        parser.add_argument("--form_type", help="Form type")
        parser.add_argument("--accession_number", help="Accession number")
        parser.add_argument("--keyword", help="Search keyword")
        parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
        parser.add_argument("--limit", type=int, default=20, help="Result limit")
        parser.add_argument("--extract_financials", action="store_true", help="Extract financials")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search_company":
                result = await sec_search_company(query=args.query, limit=args.limit)
            elif args.tool == "get_filings":
                result = await sec_get_company_filings(
                    company_name=args.company_name,
                    cik=args.cik,
                    form_type=args.form_type,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    limit=args.limit
                )
            elif args.tool == "get_content":
                result = await sec_get_filing_content(
                    cik=args.cik,
                    accession_number=args.accession_number,
                    extract_financials=args.extract_financials
                )
            elif args.tool == "search_filings":
                result = await sec_search_filings(
                    keyword=args.keyword,
                    form_type=args.form_type,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    limit=args.limit
                )
            elif args.tool == "get_company_info":
                result = await sec_get_company_info(
                    company_name=args.company_name,
                    cik=args.cik,
                    ticker=args.ticker
                )
            elif args.tool == "extract_financials":
                result = await sec_extract_financials(
                    cik=args.cik,
                    accession_number=args.accession_number
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

