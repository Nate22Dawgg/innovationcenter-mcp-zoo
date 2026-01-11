#!/usr/bin/env python3
"""
Healthcare Equities Orchestrator MCP Server

MCP server that orchestrates multiple domain servers to provide cross-domain
analysis of healthcare companies across markets and clinical domains.

This orchestrator coordinates calls to:
- biotech-markets-mcp: Company profiles, financials, and pipeline
- sec-edgar-mcp: SEC filings and company information
- clinical-trials-mcp or biomcp-mcp: Clinical trial data
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for common modules and schema loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from config import HealthcareEquitiesOrchestratorConfig
from common.config import validate_config_or_raise, ConfigValidationError
from common.errors import ErrorCode
from common.logging import get_logger

# Import DCAP for tool discovery (https://github.com/boorich/dcap)
from common.dcap import (
    register_tools_with_dcap,
    ToolMetadata,
    ToolSignature,
    DCAP_ENABLED,
)

# Import orchestrator client and tools
from src.clients.mcp_orchestrator_client import MCPOrchestratorClient
from src.tools.analyze_company_tool import analyze_company_across_markets_and_clinical

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

logger = get_logger(__name__)

# Global client instance (initialized after config validation)
_client: Optional[MCPOrchestratorClient] = None
_config_error_payload: Optional[Dict[str, Any]] = None


def create_server(fail_fast: bool = True) -> Server:
    """
    Create and configure the MCP server.
    
    Args:
        fail_fast: If True, raise ConfigValidationError on critical config issues.
                   If False, allow server to start but tools will return SERVICE_NOT_CONFIGURED errors.
    
    Returns:
        Configured MCP Server instance
    
    Raises:
        ConfigValidationError: If fail_fast=True and configuration is invalid
    """
    global _client, _config_error_payload
    
    # Load configuration from environment variables
    config = HealthcareEquitiesOrchestratorConfig(
        biotech_markets_mcp_url=os.getenv("HEALTHCARE_EQUITIES_ORCHESTRATOR_BIOTECH_MARKETS_MCP_URL"),
        sec_edgar_mcp_url=os.getenv("HEALTHCARE_EQUITIES_ORCHESTRATOR_SEC_EDGAR_MCP_URL"),
        clinical_trials_mcp_url=os.getenv("HEALTHCARE_EQUITIES_ORCHESTRATOR_CLINICAL_TRIALS_MCP_URL"),
        cache_ttl_seconds=int(os.getenv("HEALTHCARE_EQUITIES_ORCHESTRATOR_CACHE_TTL_SECONDS", "300")),
    )
    
    logger.info(f"Validating configuration (fail_fast={fail_fast})...")
    
    # Validate configuration
    try:
        ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
        
        if not ok:
            # Configuration is invalid
            if fail_fast:
                # This should not be reached (validate_config_or_raise raises in fail_fast mode)
                raise RuntimeError("Configuration validation failed in fail_fast mode")
            else:
                # Store error payload for use in tools (fail-soft behavior)
                _config_error_payload = error_payload
                logger.warning(
                    "Server starting with invalid configuration. "
                    "Tools will return SERVICE_NOT_CONFIGURED errors."
                )
        else:
            # Configuration is valid - initialize client
            logger.info("Configuration validated successfully")
            _client = MCPOrchestratorClient(
                config=config,
                cache_ttl_seconds=config.cache_ttl_seconds
            )
    
    except ConfigValidationError as e:
        # Fail-fast: configuration is invalid, don't start server
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Create MCP server
    if not MCP_AVAILABLE:
        raise ImportError("MCP SDK is required. Install with: pip install mcp")
    
    server = Server("healthcare-equities-orchestrator-mcp")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """
        List available tools.
        """
        tools = []
        
        # Analyze company across markets and clinical domains
        tools.append(Tool(
            name="analyze_company_across_markets_and_clinical",
            description=(
                "Analyze a healthcare company across markets and clinical domains. "
                "Orchestrates calls to biotech-markets-mcp, sec-edgar-mcp, and clinical-trials-mcp "
                "to provide a comprehensive view of financials, pipeline, clinical trials, and risk flags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "object",
                        "description": "Company identifier - provide at least one of ticker, company_name, or cik",
                        "properties": {
                            "ticker": {
                                "type": ["string", "null"],
                                "description": "Stock ticker symbol (e.g., 'MRNA', 'PFE', 'BNTX')",
                                "pattern": "^[A-Z0-9]{1,5}$"
                            },
                            "company_name": {
                                "type": ["string", "null"],
                                "description": "Company name (e.g., 'Moderna', 'Pfizer', 'BioNTech')"
                            },
                            "cik": {
                                "type": ["string", "null"],
                                "description": "SEC CIK (Central Index Key) - 10-digit zero-padded string",
                                "pattern": "^\\d{10}$"
                            }
                        },
                        "additionalProperties": false
                    },
                    "include_financials": {
                        "type": "boolean",
                        "description": "Whether to include financial data from biotech-markets-mcp",
                        "default": true
                    },
                    "include_clinical": {
                        "type": "boolean",
                        "description": "Whether to include clinical trial data",
                        "default": true
                    },
                    "include_sec": {
                        "type": "boolean",
                        "description": "Whether to include SEC filing data",
                        "default": true
                    }
                },
                "required": ["identifier"],
                "anyOf": [
                    {"required": ["ticker"]},
                    {"required": ["company_name"]},
                    {"required": ["cik"]}
                ],
                "additionalProperties": false
            }
        ))
        
        logger.info(f"Registered {len(tools)} tools")
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle tool calls.
        """
        logger.info(f"Tool call: {name} with arguments: {arguments}")
        
        # Check if service is not configured (fail-soft behavior)
        if _config_error_payload is not None:
            logger.warning(f"Tool {name} called but service is not configured")
            return [TextContent(
                type="text",
                text=json.dumps(_config_error_payload, indent=2)
            )]
        
        # Route to appropriate tool handler
        try:
            if name == "analyze_company_across_markets_and_clinical":
                result = analyze_company_across_markets_and_clinical(
                    client=_client,
                    config_error_payload=_config_error_payload,
                    **arguments
                )
            else:
                # Unknown tool
                result = {
                    "error": {
                        "code": ErrorCode.BAD_REQUEST.value,
                        "message": f"Unknown tool: {name}",
                        "details": {
                            "tool_name": name,
                            "available_tools": ["analyze_company_across_markets_and_clinical"]
                        }
                    }
                }
            
            logger.info(f"Tool {name} executed successfully")
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            # Unexpected error during tool execution
            logger.error(f"Error executing tool {name}: {str(e)}", exc_info=True)
            error_response = {
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": f"An unexpected error occurred while executing tool {name}",
                    "details": {
                        "tool_name": name,
                        "error": str(e)
                    }
                }
            }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    return server


# DCAP v3.1 Tool Metadata for semantic discovery
DCAP_TOOLS = [
    ToolMetadata(
        name="analyze_company_across_markets_and_clinical",
        description="Analyze healthcare company across markets and clinical domains with orchestrated data gathering",
        triggers=["healthcare analysis", "company analysis", "cross-domain analysis", "biotech analysis", "pharma research"],
        signature=ToolSignature(input="CompanyIdentifier", output="Maybe<ComprehensiveAnalysis>", cost=0)
    ),
]


async def main():
    """Main entry point for the MCP server."""
    # Determine fail-fast behavior from environment (default: True)
    fail_fast = os.getenv("HEALTHCARE_EQUITIES_ORCHESTRATOR_FAIL_FAST", "true").lower() == "true"
    
    logger.info("Starting Healthcare Equities Orchestrator MCP server...")
    
    try:
        server = create_server(fail_fast=fail_fast)
        logger.info("MCP server created successfully")
        
        # Register tools with DCAP for dynamic discovery
        if DCAP_ENABLED:
            registered = register_tools_with_dcap(
                server_id="healthcare-equities-orchestrator-mcp",
                tools=DCAP_TOOLS,
                base_command="python servers/markets/healthcare-equities-orchestrator-mcp/server.py"
            )
            logger.info(f"DCAP: Registered {registered} tools with relay")
        
        # Run server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except ConfigValidationError as e:
        logger.error(f"Failed to start server due to configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
