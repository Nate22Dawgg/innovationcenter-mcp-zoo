"""
Tests for tool implementations.

This is a template test file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Update tests to match your actual tool implementations
3. Add more comprehensive tests for your specific use cases

These tests demonstrate:
- Testing tool happy path
- Testing SERVICE_NOT_CONFIGURED (fail-soft behavior)
- Testing input validation
- Testing error handling
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.example_client import ExampleClient
from src.tools.example_tool import example_tool, example_get_data_tool
from common.errors import ErrorCode


def test_example_tool_success():
    """Test that example_tool works correctly with valid client."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock successful client.ping() call
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    
    with patch('src.clients.example_client.get', return_value=mock_response):
        result = example_tool(client=client, message="test message")
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["status"] == "ok"
        assert result["message"] == "test message"
        assert result["processed"] is True


def test_example_tool_service_not_configured():
    """Test that example_tool returns SERVICE_NOT_CONFIGURED when config is invalid."""
    config_error_payload = {
        "error_code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
        "message": "Service configuration is incomplete or invalid.",
        "issues": [
            {
                "field": "api_key",
                "message": "API_KEY is required",
                "critical": True
            }
        ]
    }
    
    result = example_tool(client=None, config_error_payload=config_error_payload)
    
    assert isinstance(result, dict)
    assert result["error_code"] == ErrorCode.SERVICE_NOT_CONFIGURED.value
    assert "issues" in result


def test_example_tool_input_validation():
    """Test that example_tool validates input correctly."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Test with empty message
    result = example_tool(client=client, message="")
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.BAD_REQUEST.value
    
    # Test with None message
    result = example_tool(client=client, message=None)
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.BAD_REQUEST.value


def test_example_get_data_tool_success():
    """Test that example_get_data_tool works correctly."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock successful client.get_data() call
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "resource-123",
        "name": "Test Resource"
    }
    
    with patch('src.clients.example_client.get', return_value=mock_response):
        result = example_get_data_tool(client=client, resource_id="resource-123")
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["resource_id"] == "resource-123"
        assert "data" in result


def test_example_get_data_tool_service_not_configured():
    """Test that example_get_data_tool returns SERVICE_NOT_CONFIGURED when config is invalid."""
    config_error_payload = {
        "error_code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
        "message": "Service configuration is incomplete or invalid."
    }
    
    result = example_get_data_tool(
        client=None,
        config_error_payload=config_error_payload,
        resource_id="test"
    )
    
    assert isinstance(result, dict)
    assert result["error_code"] == ErrorCode.SERVICE_NOT_CONFIGURED.value


def test_example_get_data_tool_input_validation():
    """Test that example_get_data_tool validates input correctly."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Test with empty resource_id
    result = example_get_data_tool(client=client, resource_id="")
    assert "error" in result
    assert result["error"]["code"] == ErrorCode.BAD_REQUEST.value


if __name__ == "__main__":
    # Run tests
    test_example_tool_success()
    test_example_tool_service_not_configured()
    test_example_tool_input_validation()
    test_example_get_data_tool_success()
    test_example_get_data_tool_service_not_configured()
    test_example_get_data_tool_input_validation()
    print("All tool tests passed!")
