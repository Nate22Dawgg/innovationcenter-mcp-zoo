"""
Tests for tool implementations.

This is a template test file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Update tests to match your actual tool implementations
3. Add more comprehensive tests for your specific use cases
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.example_client import ExampleClient
from src.tools.example_tool import example_tool


def test_example_tool():
    """Test that example_tool returns a result that includes 'status': 'ok'."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key"
    )
    
    result = example_tool(client=client, message="test")
    
    assert isinstance(result, dict)
    assert result["status"] == "ok"
    assert result["message"] == "test"


if __name__ == "__main__":
    test_example_tool()
    print("All tool tests passed!")
