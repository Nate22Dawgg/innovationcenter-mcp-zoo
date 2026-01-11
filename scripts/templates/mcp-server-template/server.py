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
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from config import TemplateServerConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import example client and tool (replace with your actual implementations)
from src.clients.example_client import ExampleClient
from src.tools.example_tool import example_tool


def create_server(fail_fast: bool = True):
    """
    Create and configure the MCP server.
    
    This demonstrates how to:
    - Construct TemplateServerConfig from os.environ
    - Call validate_config_or_raise with a configuration flag to choose fail-fast vs fail-soft
    - Use error_payload from validate_config_or_raise to disable tools in fail-soft mode
    
    Args:
        fail_fast: If True, raise ConfigValidationError on critical config issues.
                   If False, return (False, error_payload) for critical issues.
    
    Returns:
        Configured MCP Server instance (omitted / minimal for template)
    
    Raises:
        ConfigValidationError: If fail_fast=True and configuration is invalid
    """
    # Construct TemplateServerConfig from environment variables
    config = TemplateServerConfig(
        base_url=os.getenv("TEMPLATE_BASE_URL"),
        api_key=os.getenv("TEMPLATE_API_KEY"),
    )
    
    # Validate configuration
    ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
    
    # If fail_soft (ok is False), you should show a comment/hook where tools
    # would use error_payload with SERVICE_NOT_CONFIGURED.
    # For example:
    # if not ok:
    #     # Store error_payload for tools to use
    #     # Tools should check this and return error_payload when called
    #     _config_error_payload = error_payload
    # else:
    #     # Configuration is valid - initialize client
    #     _client = ExampleClient(base_url=config.base_url, api_key=config.api_key)
    
    # Then, proceed with MCP server setup (omitted / minimal for template).
    # Tool registration would occur here:
    # @server.list_tools()
    # async def list_tools() -> List[Tool]:
    #     # Register your tools here
    #     pass
    #
    # @server.call_tool()
    # async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    #     # Route to tool handlers here
    #     # Check error_payload and return SERVICE_NOT_CONFIGURED if config invalid
    #     pass
    
    # Minimal placeholder return (replace with actual server setup)
    return None


if __name__ == "__main__":
    # Example usage
    try:
        server = create_server(fail_fast=True)
    except ConfigValidationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
