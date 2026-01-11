"""
Tests for client implementations.

This is a template test file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Update tests to match your actual client implementation
3. Add more comprehensive tests for your specific use cases
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.example_client import ExampleClient


def test_example_client_ping():
    """Test that ExampleClient.ping() returns 'ok'."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key"
    )
    
    result = client.ping()
    assert result == "ok"


if __name__ == "__main__":
    test_example_client_ping()
    print("All client tests passed!")
