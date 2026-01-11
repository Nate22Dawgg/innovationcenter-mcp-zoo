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

# Import configuration
from config import load_config, ClinicalTrialsConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import DCAP for tool discovery (https://github.com/boorich/dcap)
from common.dcap import (
    register_tools_with_dcap,
    ToolMetadata,
    ToolSignature,
    Connector,
    DCAP_ENABLED,
)

# Import the clinical trials API
from clinical_trials_api import (
    search_trials,
    get_trial_detail
)

# Import matching utilities
from matching_utils import (
    check_age_eligibility,
    check_sex_eligibility,
    check_condition_match,
    calculate_match_score,
    extract_eligibility_highlights
)
from geography_utils import (
    parse_geography,
    matches_geography
)
from common.identifiers import normalize_nct_id

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


async def clinical_trial_matching(
    condition: str,
    demographics: Optional[Dict[str, Any]] = None,
    geography: Optional[Dict[str, str]] = None,
    max_results: int = 20,
    max_distance_miles: int = 100
) -> Dict[str, Any]:
    """
    Match a patient to clinical trials based on condition, demographics, and geography.
    
    This is a macro workflow tool that:
    1. Searches for trials matching the condition
    2. Filters based on eligibility criteria (age, sex, condition)
    3. Ranks by proximity, phase, and fit
    4. Returns structured match results
    
    Args:
        condition: Free text description of patient's medical condition
        demographics: Optional patient demographics (age, sex, biomarkers)
        geography: Optional patient location (city, state, zip, country)
        max_results: Maximum number of matches to return (1-50, default: 20)
        max_distance_miles: Maximum distance for proximity filtering (0 = no limit, default: 100)
    
    Returns:
        Dictionary with matches array and optional query_debug_info
    """
    try:
        # Step 1: Search for candidate trials
        search_params = {
            "condition": condition,
            "status": "recruiting",  # Prefer recruiting trials
            "limit": min(100, max_results * 3)  # Get more candidates for filtering
        }
        
        # Add geography to search if provided
        parsed_geography = parse_geography(geography)
        if parsed_geography:
            # Build location string for search
            location_parts = []
            if parsed_geography.get("city"):
                location_parts.append(parsed_geography["city"])
            if parsed_geography.get("state"):
                location_parts.append(parsed_geography["state"])
            if parsed_geography.get("country"):
                location_parts.append(parsed_geography["country"])
            
            if location_parts:
                search_params["location"] = ", ".join(location_parts)
        
        search_result = search_trials(search_params)
        candidate_trials = search_result.get("trials", [])
        total_candidates = len(candidate_trials)
        
        # Step 2: Filter and score trials
        matches = []
        query_debug_info = {
            "search_queries": [f"condition: {condition}"],
            "total_candidates": total_candidates,
            "filtered_count": 0,
            "geography_used": parsed_geography is not None
        }
        
        for trial in candidate_trials:
            # Normalize NCT ID
            nct_id = normalize_nct_id(trial.get("nct_id", ""))
            if not nct_id:
                continue
            
            # Get detailed trial info for eligibility criteria
            try:
                trial_detail = get_trial_detail(nct_id)
                eligibility_criteria = trial_detail.get("enrollment", {}).get("eligibility_criteria", "")
            except Exception:
                # If detail fetch fails, use basic trial info
                eligibility_criteria = ""
                trial_detail = trial
            
            # Check geography match
            trial_locations = trial.get("locations", [])
            geo_match, distance_miles = matches_geography(
                parsed_geography,
                trial_locations,
                max_distance_miles
            )
            
            if not geo_match:
                continue  # Skip trials outside geographic range
            
            # Check age eligibility
            patient_age = demographics.get("age") if demographics else None
            age_eligible, age_reason = check_age_eligibility(patient_age, eligibility_criteria)
            
            if not age_eligible:
                continue  # Skip trials with age mismatch
            
            # Check sex eligibility
            patient_sex = demographics.get("sex") if demographics else None
            sex_eligible, sex_reason = check_sex_eligibility(patient_sex, eligibility_criteria)
            
            if not sex_eligible:
                continue  # Skip trials with sex mismatch
            
            # Check condition match
            condition_match, condition_score, condition_reason = check_condition_match(
                condition,
                trial.get("conditions", [])
            )
            
            if not condition_match:
                continue  # Skip trials that don't match condition
            
            # Calculate match score
            match_score = calculate_match_score(
                trial,
                condition,
                demographics,
                distance_miles
            )
            
            # Build why_matched explanation
            why_parts = [condition_reason]
            if age_reason and "within range" in age_reason:
                why_parts.append(age_reason)
            if sex_reason and "eligible" in sex_reason.lower():
                why_parts.append(sex_reason)
            if distance_miles is not None:
                why_parts.append(f"Within {int(distance_miles)} miles")
            
            why_matched = ". ".join(why_parts[:3])  # Limit to 3 reasons
            
            # Extract eligibility highlights
            eligibility_highlights = extract_eligibility_highlights(
                eligibility_criteria,
                demographics
            )
            
            # Build location summary
            if trial_locations:
                location_summary = "; ".join(trial_locations[:3])
                if len(trial_locations) > 3:
                    location_summary += f" (+{len(trial_locations) - 3} more)"
            else:
                location_summary = "Location information not available"
            
            # Create match object
            match = {
                "nct_id": nct_id,
                "title": trial.get("title", ""),
                "location_summary": location_summary,
                "phase": trial.get("phase", "N/A"),
                "status": trial.get("status", ""),
                "why_matched": why_matched,
                "eligibility_highlights": eligibility_highlights,
                "match_score": round(match_score, 1),
                "distance_miles": round(distance_miles, 1) if distance_miles is not None else None,
                "url": trial.get("url", f"https://clinicaltrials.gov/study/{nct_id}")
            }
            
            matches.append(match)
        
        # Step 3: Sort by match score (descending)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Step 4: Limit to max_results
        matches = matches[:max_results]
        
        query_debug_info["filtered_count"] = len(matches)
        
        return {
            "matches": matches,
            "query_debug_info": query_debug_info
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "matches": [],
            "query_debug_info": {
                "search_queries": [],
                "total_candidates": 0,
                "filtered_count": 0,
                "geography_used": False
            }
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("clinical-trials-mcp")
    
    # Load input schemas
    search_input_schema = load_schema("schemas/clinical_trials_search.json")
    detail_input_schema = load_schema("schemas/clinical_trials_get_detail.json")
    matching_input_schema = load_schema("schemas/clinical_trial_matching.json")
    
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
            ),
            Tool(
                name="clinical_trial_matching",
                description="Match a patient to clinical trials based on condition, demographics, and geography. Returns ranked list of candidate trials with eligibility reasoning.",
                inputSchema=matching_input_schema
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
            elif name == "clinical_trial_matching":
                result = await clinical_trial_matching(**arguments)
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
            name="clinical_trials_search",
            description="Search for clinical trials by condition, intervention, location, and other criteria",
            triggers=["clinical trials", "find trials", "trial search", "medical research", "study search"],
            signature=ToolSignature(input="SearchQuery", output="Maybe<TrialList>", cost=0)
        ),
        ToolMetadata(
            name="clinical_trials_get_detail",
            description="Retrieve detailed information about a specific clinical trial by NCT ID",
            triggers=["trial details", "NCT", "trial info", "specific trial"],
            signature=ToolSignature(input="NCTID", output="Maybe<Trial>", cost=0)
        ),
        ToolMetadata(
            name="clinical_trial_matching",
            description="Match a patient to clinical trials based on condition, demographics, and geography",
            triggers=["trial matching", "patient matching", "find trials for patient", "eligible trials"],
            signature=ToolSignature(input="PatientProfile", output="Maybe<MatchList>", cost=0)
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
                server_id="clinical-trials-mcp",
                tools=DCAP_TOOLS,
                base_command="python servers/clinical/clinical-trials-mcp/server.py"
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

