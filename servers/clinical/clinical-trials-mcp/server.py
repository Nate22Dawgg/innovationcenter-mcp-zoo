#!/usr/bin/env python3
"""
Clinical Trials MCP Server

MCP server for searching and retrieving clinical trials data from ClinicalTrials.gov.
Provides tools for searching trials by condition, intervention, location, and other criteria,
and retrieving detailed information about specific trials.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current directory to path for importing clinical_trials_api
sys.path.insert(0, str(Path(__file__).parent))

# Import the clinical trials API
from clinical_trials_api import (
    search_trials,
    get_trial_detail
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


# Load schemas
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


# Tool implementations
async def clinical_trials_search(
    condition: Optional[str] = None,
    intervention: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    study_type: Optional[str] = None,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Search for clinical trials by condition, intervention, location, and other criteria.
    
    Args:
        condition: Medical condition or disease to search for
        intervention: Intervention type (drug, device, procedure, etc.)
        location: Geographic location (country, state, or city)
        status: Trial recruitment status
        phase: Clinical trial phase
        study_type: Type of study
        limit: Maximum number of results to return (1-100, default: 20)
        offset: Number of results to skip for pagination (default: 0)
    
    Returns:
        Dictionary with search results containing total, count, offset, and trials list
    """
    try:
        # Build params dict, filtering out None values
        params = {}
        if condition:
            params["condition"] = condition
        if intervention:
            params["intervention"] = intervention
        if location:
            params["location"] = location
        if status:
            params["status"] = status
        if phase:
            params["phase"] = phase
        if study_type:
            params["study_type"] = study_type
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        
        # Call the API (synchronous function, but we're in async context)
        result = search_trials(params)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "total": 0,
            "count": 0,
            "offset": offset or 0,
            "trials": []
        }


async def clinical_trials_get_detail(
    nct_id: str
) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific clinical trial by NCT ID.
    
    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., "NCT01234567")
    
    Returns:
        Dictionary with detailed trial information
    """
    try:
        # Validate NCT ID format
        if not nct_id.startswith("NCT") or len(nct_id) != 11:
            raise ValueError(f"Invalid NCT ID format: {nct_id}. Expected format: NCT01234567")
        
        # Call the API (synchronous function, but we're in async context)
        result = get_trial_detail(nct_id)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "nct_id": nct_id
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("clinical-trials-mcp")
    
    # Load input schemas
    search_input_schema = load_schema("schemas/clinical_trials_search.json")
    detail_input_schema = load_schema("schemas/clinical_trials_get_detail.json")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="clinical_trials_search",
                description="Search for clinical trials by condition, intervention, location, and other criteria",
                inputSchema=search_input_schema
            ),
            Tool(
                name="clinical_trials_get_detail",
                description="Retrieve detailed information about a specific clinical trial by NCT ID",
                inputSchema=detail_input_schema
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "clinical_trials_search":
                result = await clinical_trials_search(**arguments)
            elif name == "clinical_trials_get_detail":
                result = await clinical_trials_get_detail(**arguments)
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
        
        parser = argparse.ArgumentParser(description="Clinical Trials MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=["search", "get_detail"])
        parser.add_argument("--condition", help="Medical condition")
        parser.add_argument("--intervention", help="Intervention type")
        parser.add_argument("--location", help="Geographic location")
        parser.add_argument("--status", help="Recruitment status")
        parser.add_argument("--phase", help="Trial phase")
        parser.add_argument("--study_type", help="Study type")
        parser.add_argument("--limit", type=int, default=20, help="Result limit")
        parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
        parser.add_argument("--nct_id", help="NCT ID for detail retrieval")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search":
                result = await clinical_trials_search(
                    condition=args.condition,
                    intervention=args.intervention,
                    location=args.location,
                    status=args.status,
                    phase=args.phase,
                    study_type=args.study_type,
                    limit=args.limit,
                    offset=args.offset
                )
            elif args.tool == "get_detail":
                if not args.nct_id:
                    raise ValueError("--nct_id is required for get_detail tool")
                result = await clinical_trials_get_detail(nct_id=args.nct_id)
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

