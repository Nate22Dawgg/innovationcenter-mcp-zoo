#!/usr/bin/env python3
"""
Biotech Markets MCP Server

MCP server for biotech private markets, venture funding rounds, drug pipeline tracking,
and preclinical/clinical analytics. Integrates ClinicalTrials.gov, SEC EDGAR, and PubMed APIs.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from company_aggregator import get_profile, search_companies
from clinical_trials_client import get_pipeline_drugs, get_target_exposure
from sec_edgar_client import get_ipo_filings, get_investors_from_filings
from cache import Cache
from yfinance_client import get_timeseries as _get_timeseries

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


# Initialize cache
_cache = Cache()


# Tool implementations
async def biotech_search_companies(
    therapeutic_area: Optional[str] = None,
    stage: Optional[str] = None,
    location: Optional[str] = None,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """
    Search for biotech companies by therapeutic area, stage, and location.
    
    Args:
        therapeutic_area: Therapeutic area (e.g., "oncology", "diabetes")
        stage: Development stage (e.g., "Phase 3", "Phase 2")
        location: Geographic location
        limit: Maximum number of companies to return
    
    Returns:
        Dictionary with list of companies matching criteria
    """
    try:
        companies = search_companies(
            therapeutic_area=therapeutic_area,
            stage=stage,
            location=location,
            limit=limit or 20
        )
        
        return {
            "count": len(companies),
            "companies": companies,
            "filters": {
                "therapeutic_area": therapeutic_area,
                "stage": stage,
                "location": location
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "count": 0,
            "companies": []
        }


async def biotech_get_company_profile(company_name: str) -> Dict[str, Any]:
    """
    Get unified company profile aggregating data from all sources.
    
    Args:
        company_name: Company name (e.g., "Moderna", "Pfizer")
    
    Returns:
        Unified company profile with pipeline, financials, trials, etc.
    """
    try:
        profile = get_profile(company_name, use_cache=True)
        return profile
    except Exception as e:
        return {
            "error": str(e),
            "company_name": company_name
        }


async def biotech_get_funding_rounds(company_name: str) -> Dict[str, Any]:
    """
    Get funding rounds history for a company.
    
    Note: Free sources (SEC EDGAR) provide limited funding data. For comprehensive
    funding information, paid sources like Crunchbase are recommended.
    
    Args:
        company_name: Company name
    
    Returns:
        Dictionary with funding rounds (may be limited with free sources)
    """
    try:
        # Get IPO filings (S-1) which contain funding information
        ipo_filings = get_ipo_filings(company_name)
        
        # Note: Full funding round extraction requires parsing S-1 documents
        # This is a simplified version that returns filing references
        
        return {
            "company_name": company_name,
            "funding_rounds": [
                {
                    "type": "IPO",
                    "filing_date": filing.get("filing_date", ""),
                    "form_type": filing.get("form_type", ""),
                    "accession_number": filing.get("accession_number", ""),
                    "note": "Full funding details available in S-1 filing. Parse filing content for detailed information."
                }
                for filing in ipo_filings
            ],
            "data_source": "SEC EDGAR (free)",
            "limitation": "Free sources provide limited funding data. For comprehensive funding rounds, consider integrating Crunchbase API (paid).",
            "count": len(ipo_filings)
        }
    except Exception as e:
        return {
            "error": str(e),
            "company_name": company_name,
            "funding_rounds": []
        }


async def biotech_get_pipeline_drugs(company_name: str) -> Dict[str, Any]:
    """
    Get pipeline drugs for a company from clinical trials.
    
    Args:
        company_name: Company name
    
    Returns:
        Dictionary with list of drugs in pipeline with phases
    """
    try:
        pipeline = get_pipeline_drugs(company_name)
        
        return {
            "company_name": company_name,
            "pipeline_count": len(pipeline),
            "drugs": pipeline,
            "data_source": "ClinicalTrials.gov"
        }
    except Exception as e:
        return {
            "error": str(e),
            "company_name": company_name,
            "pipeline_count": 0,
            "drugs": []
        }


async def biotech_get_investors(company_name: str) -> Dict[str, Any]:
    """
    Get investors/backers for a company.
    
    Note: Free sources (SEC EDGAR) provide limited investor data. For comprehensive
    investor information, paid sources like Crunchbase are recommended.
    
    Args:
        company_name: Company name
    
    Returns:
        Dictionary with investor information (may be limited with free sources)
    """
    try:
        investors = get_investors_from_filings(company_name)
        
        return {
            "company_name": company_name,
            "investors": investors,
            "data_source": "SEC EDGAR (free)",
            "limitation": "Free sources provide limited investor data. Full investor extraction requires parsing SEC filings (proxy statements, S-1). For comprehensive investor data, consider integrating Crunchbase API (paid).",
            "count": len(investors)
        }
    except Exception as e:
        return {
            "error": str(e),
            "company_name": company_name,
            "investors": []
        }


async def biotech_analyze_target_exposure(target: str) -> Dict[str, Any]:
    """
    Analyze target exposure - companies working on a specific target.
    
    Args:
        target: Target name or identifier (e.g., "PD-1", "HER2", "EGFR")
    
    Returns:
        Dictionary with companies working on target, trial phases, competitive landscape
    """
    try:
        exposure = get_target_exposure(target)
        
        # Calculate statistics
        total_trials = sum(comp["trial_count"] for comp in exposure)
        phase_distribution = {}
        
        for comp in exposure:
            for phase in comp.get("phases", []):
                phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        return {
            "target": target,
            "company_count": len(exposure),
            "total_trials": total_trials,
            "companies": exposure,
            "phase_distribution": phase_distribution,
            "data_source": "ClinicalTrials.gov"
        }
    except Exception as e:
        return {
            "error": str(e),
            "target": target,
            "company_count": 0,
            "companies": []
        }


async def markets_get_timeseries(
    symbol: str,
    interval: Optional[str] = "daily",
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get time series stock data for a biotech ticker symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., "MRNA", "BNTX", "GILD")
        interval: Data interval - "daily", "weekly", or "monthly" (default: "daily")
        period: Time period - "1m", "3m", "6m", "1y", "5y" (optional if start_date provided)
        start_date: Start date in YYYY-MM-DD format (optional, overrides period)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
    
    Returns:
        Dictionary with time series data including OHLCV
    """
    try:
        # Build cache parameters
        cache_params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "period": period,
            "start_date": start_date,
            "end_date": end_date
        }
        
        # Check cache first
        cached_result = _cache.get("markets_timeseries", cache_params)
        if cached_result:
            cached_result["metadata"]["cache_status"] = "cached"
            return cached_result
        
        # Determine if this is recent data (last 7 days) or historical
        from datetime import datetime
        is_recent = False
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
                is_recent = (end_dt - start_dt).days <= 7
            except (ValueError, TypeError):
                pass
        elif period in ["1m"]:
            is_recent = True
        
        # Fetch fresh data
        result = _get_timeseries(
            symbol=symbol,
            interval=interval or "daily",
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # Add cache status
        if "metadata" in result:
            result["metadata"]["cache_status"] = "fresh"
        else:
            result["metadata"] = {"cache_status": "fresh"}
        
        # Cache with appropriate TTL (7 days for historical, 1 hour for recent)
        if "error" not in result:
            ttl_hours = 1 if is_recent else 168  # 1 hour for recent, 7 days (168 hours) for historical
            _cache.set("markets_timeseries", cache_params, result, ttl_hours=ttl_hours)
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "count": 0,
            "data": []
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("biotech-markets-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="biotech_search_companies",
                description="Search for biotech companies by therapeutic area, stage, and location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "therapeutic_area": {
                            "type": "string",
                            "description": "Therapeutic area (e.g., 'oncology', 'diabetes')"
                        },
                        "stage": {
                            "type": "string",
                            "description": "Development stage (e.g., 'Phase 3', 'Phase 2')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Geographic location"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of companies to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 20
                        }
                    },
                    "additionalProperties": False
                }
            ),
            Tool(
                name="biotech_get_company_profile",
                description="Get unified company profile aggregating data from ClinicalTrials.gov, SEC EDGAR, and PubMed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name (e.g., 'Moderna', 'Pfizer')"
                        }
                    },
                    "required": ["company_name"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="biotech_get_funding_rounds",
                description="Get funding rounds history for a company (limited with free sources)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name"
                        }
                    },
                    "required": ["company_name"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="biotech_get_pipeline_drugs",
                description="Get pipeline drugs for a company from clinical trials",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name"
                        }
                    },
                    "required": ["company_name"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="biotech_get_investors",
                description="Get investors/backers for a company (limited with free sources)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name"
                        }
                    },
                    "required": ["company_name"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="biotech_analyze_target_exposure",
                description="Analyze target exposure - companies working on a specific target (e.g., 'PD-1', 'HER2')",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Target name or identifier (e.g., 'PD-1', 'HER2', 'EGFR')"
                        }
                    },
                    "required": ["target"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="markets.get_timeseries",
                description="Retrieve historical price data for financial instruments (stocks, bonds, commodities) with OHLCV data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Financial instrument symbol (ticker) for biotech stocks",
                            "pattern": "^[A-Z0-9.-]+$"
                        },
                        "interval": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "default": "daily",
                            "description": "Data interval: daily, weekly, or monthly"
                        },
                        "period": {
                            "type": "string",
                            "enum": ["1m", "3m", "6m", "1y", "5y"],
                            "description": "Time period: 1m (1 month), 3m (3 months), 6m (6 months), 1y (1 year), 5y (5 years)"
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Optional start date for time series (ISO 8601 format: YYYY-MM-DD). If provided, overrides period parameter."
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Optional end date for time series (ISO 8601 format: YYYY-MM-DD). Defaults to today if not provided."
                        }
                    },
                    "required": ["symbol"],
                    "additionalProperties": False
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "biotech_search_companies":
                result = await biotech_search_companies(**arguments)
            elif name == "biotech_get_company_profile":
                result = await biotech_get_company_profile(**arguments)
            elif name == "biotech_get_funding_rounds":
                result = await biotech_get_funding_rounds(**arguments)
            elif name == "biotech_get_pipeline_drugs":
                result = await biotech_get_pipeline_drugs(**arguments)
            elif name == "biotech_get_investors":
                result = await biotech_get_investors(**arguments)
            elif name == "biotech_analyze_target_exposure":
                result = await biotech_analyze_target_exposure(**arguments)
            elif name == "markets.get_timeseries":
                result = await markets_get_timeseries(**arguments)
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
        
        parser = argparse.ArgumentParser(description="Biotech Markets MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "search_companies", "get_profile", "get_funding", "get_pipeline",
            "get_investors", "analyze_target", "get_timeseries"
        ])
        parser.add_argument("--company_name", help="Company name")
        parser.add_argument("--therapeutic_area", help="Therapeutic area")
        parser.add_argument("--stage", help="Development stage")
        parser.add_argument("--location", help="Location")
        parser.add_argument("--target", help="Target name")
        parser.add_argument("--limit", type=int, default=20, help="Result limit")
        parser.add_argument("--symbol", help="Stock ticker symbol for timeseries")
        parser.add_argument("--interval", help="Data interval: daily, weekly, or monthly", default="daily")
        parser.add_argument("--period", help="Time period: 1m, 3m, 6m, 1y, 5y")
        parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search_companies":
                result = await biotech_search_companies(
                    therapeutic_area=args.therapeutic_area,
                    stage=args.stage,
                    location=args.location,
                    limit=args.limit
                )
            elif args.tool == "get_profile":
                result = await biotech_get_company_profile(company_name=args.company_name)
            elif args.tool == "get_funding":
                result = await biotech_get_funding_rounds(company_name=args.company_name)
            elif args.tool == "get_pipeline":
                result = await biotech_get_pipeline_drugs(company_name=args.company_name)
            elif args.tool == "get_investors":
                result = await biotech_get_investors(company_name=args.company_name)
            elif args.tool == "analyze_target":
                result = await biotech_analyze_target_exposure(target=args.target)
            elif args.tool == "get_timeseries":
                result = await markets_get_timeseries(
                    symbol=args.symbol,
                    interval=args.interval,
                    period=args.period,
                    start_date=args.start_date,
                    end_date=args.end_date
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

