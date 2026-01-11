#!/usr/bin/env python3
"""
NHANES MCP Server

MCP server for accessing NHANES (National Health and Nutrition Examination Survey) data.
Provides tools for querying public health survey data from CDC/NCHS.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current directory to path for importing modules
sys.path.insert(0, str(Path(__file__).parent))

# Import configuration
from config import load_config, NhanesConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import DCAP for tool discovery (https://github.com/boorich/dcap)
from common.dcap import (
    register_tools_with_dcap,
    ToolMetadata,
    ToolSignature,
    DCAP_ENABLED,
)

# Import NHANES modules
from nhanes_query_engine import (
    list_datasets,
    get_dataset_info,
    query_data,
    get_variable_info,
    calculate_percentile,
    get_demographics_summary
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


# Configuration will be loaded at startup
_config: Optional[NhanesConfig] = None


# Load schemas
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


# Tool implementations
def get_config() -> NhanesConfig:
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


async def nhanes_list_datasets(
    cycle: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available NHANES datasets for a cycle.
    
    Args:
        cycle: Data cycle (e.g., "2017-2018"). If not provided, lists all cycles.
    
    Returns:
        Dictionary with list of available datasets
    """
    try:
        from nhanes_data_loader import get_available_cycles
        
        config = get_config()
        config_path = Path(config.config_path) if config.config_path else Path(__file__).parent / "config" / "datasets.json"
        
        if cycle:
            datasets = list_datasets(cycle, config_path)
            return {
                "cycle": cycle,
                "datasets": datasets,
                "count": len(datasets)
            }
        else:
            # Return datasets for all cycles
            cycles = get_available_cycles()
            all_datasets = {}
            for c in cycles:
                datasets = list_datasets(c, config_path)
                all_datasets[c] = {
                    "datasets": datasets,
                    "count": len(datasets)
                }
            return {
                "cycles": all_datasets
            }
    except Exception as e:
        return {
            "error": str(e),
            "cycle": cycle
        }


async def nhanes_get_data(
    dataset: str,
    cycle: str,
    filters: Optional[Dict[str, Any]] = None,
    variables: Optional[List[str]] = None,
    limit: Optional[int] = 100
) -> Dict[str, Any]:
    """
    Query NHANES data with optional filters and variable selection.
    
    Args:
        dataset: Dataset ID (e.g., "demographics", "body_measures")
        cycle: Data cycle (e.g., "2017-2018")
        filters: Optional filter dictionary (e.g., {"RIDAGEYR": {"min": 18, "max": 65}})
        variables: Optional list of variables to select
        limit: Maximum number of rows to return (default: 100)
    
    Returns:
        Dictionary with query results
    """
    try:
        config = get_config()
        data_dir = Path(config.data_directory) if config.data_directory else Path(__file__).parent / "data"
        config_path = Path(config.config_path) if config.config_path else Path(__file__).parent / "config" / "datasets.json"
        
        result = query_data(
            dataset,
            cycle,
            filters=filters,
            variables=variables,
            limit=limit,
            data_dir=data_dir,
            config_path=config_path
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "dataset": dataset,
            "cycle": cycle
        }


async def nhanes_get_variable_info(
    dataset: str,
    variable: str,
    cycle: str
) -> Dict[str, Any]:
    """
    Get information about a specific variable in a dataset.
    
    Args:
        dataset: Dataset ID
        variable: Variable name (e.g., "RIDAGEYR", "BMXBMI")
        cycle: Data cycle
    
    Returns:
        Dictionary with variable information and statistics
    """
    try:
        config = get_config()
        data_dir = Path(config.data_directory) if config.data_directory else Path(__file__).parent / "data"
        config_path = Path(config.config_path) if config.config_path else Path(__file__).parent / "config" / "datasets.json"
        
        result = get_variable_info(
            dataset,
            variable,
            cycle,
            data_dir=data_dir,
            config_path=config_path
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "dataset": dataset,
            "variable": variable,
            "cycle": cycle
        }


async def nhanes_calculate_percentile(
    variable: str,
    value: float,
    dataset: str,
    cycle: str,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate percentile rank of a value for a variable.
    
    Args:
        variable: Variable name (e.g., "BMXBMI")
        value: Value to calculate percentile for
        dataset: Dataset ID
        cycle: Data cycle
        filters: Optional filters to apply (e.g., {"RIAGENDR": 1} for males only)
    
    Returns:
        Dictionary with percentile rank and statistics
    """
    try:
        config = get_config()
        data_dir = Path(config.data_directory) if config.data_directory else Path(__file__).parent / "data"
        config_path = Path(config.config_path) if config.config_path else Path(__file__).parent / "config" / "datasets.json"
        
        result = calculate_percentile(
            variable,
            value,
            dataset,
            cycle,
            filters=filters,
            data_dir=data_dir,
            config_path=config_path
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "variable": variable,
            "value": value,
            "dataset": dataset,
            "cycle": cycle
        }


async def nhanes_get_demographics_summary(
    cycle: str
) -> Dict[str, Any]:
    """
    Get summary statistics for demographics data.
    
    Args:
        cycle: Data cycle
    
    Returns:
        Dictionary with demographics summary statistics
    """
    try:
        config = get_config()
        data_dir = Path(config.data_directory) if config.data_directory else Path(__file__).parent / "data"
        config_path = Path(config.config_path) if config.config_path else Path(__file__).parent / "config" / "datasets.json"
        
        result = get_demographics_summary(
            cycle,
            data_dir=data_dir,
            config_path=config_path
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "cycle": cycle
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("nhanes-mcp")
    
    # Load input schemas
    list_datasets_schema = load_schema("schemas/nhanes_list_datasets.json")
    get_data_schema = load_schema("schemas/nhanes_get_data.json")
    get_variable_info_schema = load_schema("schemas/nhanes_get_variable_info.json")
    calculate_percentile_schema = load_schema("schemas/nhanes_calculate_percentile.json")
    get_demographics_summary_schema = load_schema("schemas/nhanes_get_demographics_summary.json")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="nhanes_list_datasets",
                description="List available NHANES datasets for a cycle",
                inputSchema=list_datasets_schema
            ),
            Tool(
                name="nhanes_get_data",
                description="Query NHANES data with optional filters and variable selection",
                inputSchema=get_data_schema
            ),
            Tool(
                name="nhanes_get_variable_info",
                description="Get information about a specific variable in a dataset",
                inputSchema=get_variable_info_schema
            ),
            Tool(
                name="nhanes_calculate_percentile",
                description="Calculate percentile rank of a value for a variable",
                inputSchema=calculate_percentile_schema
            ),
            Tool(
                name="nhanes_get_demographics_summary",
                description="Get summary statistics for demographics data",
                inputSchema=get_demographics_summary_schema
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "nhanes_list_datasets":
                result = await nhanes_list_datasets(**arguments)
            elif name == "nhanes_get_data":
                result = await nhanes_get_data(**arguments)
            elif name == "nhanes_get_variable_info":
                result = await nhanes_get_variable_info(**arguments)
            elif name == "nhanes_calculate_percentile":
                result = await nhanes_calculate_percentile(**arguments)
            elif name == "nhanes_get_demographics_summary":
                result = await nhanes_get_demographics_summary(**arguments)
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
            name="nhanes_list_datasets",
            description="List available NHANES datasets for a cycle",
            triggers=["NHANES datasets", "health survey data", "CDC data", "available datasets"],
            signature=ToolSignature(input="CycleQuery", output="Maybe<DatasetList>", cost=0)
        ),
        ToolMetadata(
            name="nhanes_get_data",
            description="Query NHANES data with optional filters and variable selection",
            triggers=["NHANES query", "health survey", "nutrition data", "examination data"],
            signature=ToolSignature(input="DataQuery", output="Maybe<DataResult>", cost=0)
        ),
        ToolMetadata(
            name="nhanes_get_variable_info",
            description="Get information about a specific variable in a dataset",
            triggers=["variable info", "NHANES variable", "data dictionary"],
            signature=ToolSignature(input="VariableQuery", output="Maybe<VariableInfo>", cost=0)
        ),
        ToolMetadata(
            name="nhanes_calculate_percentile",
            description="Calculate percentile rank of a value for a variable",
            triggers=["percentile", "population comparison", "health metrics percentile"],
            signature=ToolSignature(input="PercentileQuery", output="Maybe<PercentileResult>", cost=0)
        ),
        ToolMetadata(
            name="nhanes_get_demographics_summary",
            description="Get summary statistics for demographics data",
            triggers=["demographics", "population summary", "NHANES demographics"],
            signature=ToolSignature(input="Cycle", output="Maybe<DemographicsSummary>", cost=0)
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
                server_id="nhanes-mcp",
                tools=DCAP_TOOLS,
                base_command="python servers/clinical/nhanes-mcp/server.py"
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
        
        parser = argparse.ArgumentParser(description="NHANES MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "list_datasets", "get_data", "get_variable_info", 
            "calculate_percentile", "get_demographics_summary"
        ])
        parser.add_argument("--cycle", help="Data cycle (e.g., 2017-2018)")
        parser.add_argument("--dataset", help="Dataset ID")
        parser.add_argument("--variable", help="Variable name")
        parser.add_argument("--value", type=float, help="Value for percentile calculation")
        parser.add_argument("--filters", help="JSON string with filters")
        parser.add_argument("--variables", help="Comma-separated list of variables")
        parser.add_argument("--limit", type=int, default=100, help="Result limit")
        
        args = parser.parse_args()
        
        try:
            filters = json.loads(args.filters) if args.filters else None
            variables = args.variables.split(",") if args.variables else None
            
            if args.tool == "list_datasets":
                result = await nhanes_list_datasets(cycle=args.cycle)
            elif args.tool == "get_data":
                if not args.dataset or not args.cycle:
                    raise ValueError("--dataset and --cycle are required for get_data")
                result = await nhanes_get_data(
                    dataset=args.dataset,
                    cycle=args.cycle,
                    filters=filters,
                    variables=variables,
                    limit=args.limit
                )
            elif args.tool == "get_variable_info":
                if not args.dataset or not args.variable or not args.cycle:
                    raise ValueError("--dataset, --variable, and --cycle are required")
                result = await nhanes_get_variable_info(
                    dataset=args.dataset,
                    variable=args.variable,
                    cycle=args.cycle
                )
            elif args.tool == "calculate_percentile":
                if not args.variable or args.value is None or not args.dataset or not args.cycle:
                    raise ValueError("--variable, --value, --dataset, and --cycle are required")
                result = await nhanes_calculate_percentile(
                    variable=args.variable,
                    value=args.value,
                    dataset=args.dataset,
                    cycle=args.cycle,
                    filters=filters
                )
            elif args.tool == "get_demographics_summary":
                if not args.cycle:
                    raise ValueError("--cycle is required")
                result = await nhanes_get_demographics_summary(cycle=args.cycle)
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

