#!/usr/bin/env python3
"""
Template MCP Server

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Update the server name and description
3. Implement your actual tools in src/tools/
4. Implement your actual clients in src/clients/
5. Register your tools in the list_tools() and call_tool() handlers below

This demonstrates:
- Fail-fast: server refuses to start if critical config missing
- Fail-soft: tools can check config status and return SERVICE_NOT_CONFIGURED
- Clean tool registration pattern
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

from config import TemplateServerConfig
from common.config import validate_config_or_raise, ConfigValidationError
from common.errors import ErrorCode
from common.logging import get_logger

# Import example client and tool (replace with your actual implementations)
from src.clients.example_client import ExampleClient
from src.tools.example_tool import example_tool, example_get_data_tool

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
_client: Optional[ExampleClient] = None
_config_error_payload: Optional[Dict[str, Any]] = None


def create_server(fail_fast: bool = True) -> Server:
    """
    Create and configure the MCP server.
    
    This demonstrates two configuration validation strategies:
    
    Fail-Fast (fail_fast=True):
    - Raises ConfigValidationError if critical config is missing
    - Server refuses to start
    - Use for production deployments where misconfiguration should fail immediately
    
    Fail-Soft (fail_fast=False):
    - Allows server to start even with invalid config
    - Tools check _config_error_payload and return SERVICE_NOT_CONFIGURED
    - Use for development or when you want graceful degradation
    
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
    # TODO: Update env var names to match your server
    config = TemplateServerConfig(
        base_url=os.getenv("TEMPLATE_BASE_URL"),
        api_key=os.getenv("TEMPLATE_API_KEY"),
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
            _client = ExampleClient(
                base_url=config.base_url or "https://api.example.com",
                api_key=config.api_key or ""
            )
    
    except ConfigValidationError as e:
        # Fail-fast: configuration is invalid, don't start server
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Create MCP server
    if not MCP_AVAILABLE:
        raise ImportError("MCP SDK is required. Install with: pip install mcp")
    
    server = Server("template-mcp-server")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """
        List available tools.
        
        This demonstrates a clean pattern for tool registration.
        Each tool should have:
        - name: unique tool identifier (lowercase with underscores)
        - description: clear description of what the tool does
        - inputSchema: JSON schema for tool arguments
        
        TODO: Replace with your actual tools and schemas
        """
        tools = []
        
        # Example tool registration (replace with your actual tools)
        tools.append(Tool(
            name="example_tool",
            description="Example tool that demonstrates the template structure. Processes a message and returns status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A message to process"
                    }
                },
                "required": ["message"]
            }
        ))
        
        # Another example tool
        tools.append(Tool(
            name="example_get_data",
            description="Example tool for fetching data by resource ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "ID of the resource to fetch"
                    }
                },
                "required": ["resource_id"]
            }
        ))
        
        # TODO: Add more tools here
        # tools.append(Tool(
        #     name="your_tool_name",
        #     description="Description of what your tool does",
        #     inputSchema={...}
        # ))
        
        logger.info(f"Registered {len(tools)} tools")
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle tool calls.
        
        This demonstrates:
        1. Checking if service is configured (fail-soft behavior)
        2. Routing to appropriate tool handlers
        3. Error handling and structured responses
        
        TODO: In a real server, you should also:
        - Validate input against JSON schema (using common.validation.validate_tool_input)
        - Validate output (using common.validation.validate_tool_output)
        - Add comprehensive logging (already done via common.logging)
        - Add metrics tracking (using common.metrics or common.observability decorators)
        - Add caching for expensive operations (using common.cache)
        - Add observability decorators (using @observe_tool_call_sync from common.observability)
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
            if name == "example_tool":
                result = example_tool(
                    client=_client,
                    config_error_payload=_config_error_payload,
                    **arguments
                )
            elif name == "example_get_data":
                result = example_get_data_tool(
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
                            "available_tools": ["example_tool", "example_get_data"]
                        }
                    }
                }
            
            # TODO: In a real server, validate output here (optional, gated by MCP_STRICT_OUTPUT_VALIDATION):
            # from common.validation import validate_tool_output
            # validate_tool_output(name, result)
            #
            # Note: Output validation is optional and only runs when MCP_STRICT_OUTPUT_VALIDATION=true
            # This is to avoid performance impact in production while still allowing validation in development
            
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


async def main():
    """Main entry point for the MCP server."""
    # Determine fail-fast behavior from environment (default: True)
    # Set TEMPLATE_FAIL_FAST=false to enable fail-soft mode
    fail_fast = os.getenv("TEMPLATE_FAIL_FAST", "true").lower() == "true"
    
    logger.info("Starting template MCP server...")
    
    try:
        server = create_server(fail_fast=fail_fast)
        
        # Optional: Add health check endpoint if using HTTP transport
        # Example:
        # @server.list_resources()
        # async def list_resources() -> List[Resource]:
        #     return [Resource(uri="health", name="Health Check")]
        #
        # @server.read_resource()
        # async def read_resource(uri: str) -> str:
        #     if uri == "health":
        #         return json.dumps({"status": "ok", "configured": _client is not None})
        
        logger.info("MCP server created successfully")
        
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
