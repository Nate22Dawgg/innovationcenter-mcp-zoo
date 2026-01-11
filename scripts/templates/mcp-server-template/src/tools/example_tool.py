"""
Example MCP tool implementation.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename example_tool to your_tool_name
3. Implement your actual tool logic
4. Add schema-based validation using common.validation.validate_tool_input
5. Add proper error handling using common.errors

This is where you map MCP tool inputs/outputs.
In a real server, you'd add schema-based validation.
"""

from typing import Dict, Any

from src.clients.example_client import ExampleClient


def example_tool(client: ExampleClient, message: str) -> Dict[str, Any]:
    """
    Example tool that demonstrates the template structure.
    
    Args:
        client: Initialized client instance
        message: Input message to process
    
    Returns:
        Dictionary with tool result
    """
    # Use the client in a trivial way
    status = client.ping()
    
    # Return a simple dict result
    return {
        "status": status,
        "message": message
    }
