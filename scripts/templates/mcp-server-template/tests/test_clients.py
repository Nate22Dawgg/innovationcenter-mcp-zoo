"""
Tests for client implementations.

This is a template test file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Update tests to match your actual client implementation
3. Add more comprehensive tests for your specific use cases

These tests demonstrate:
- Testing client initialization
- Testing client methods with mocked HTTP responses
- Testing error handling
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.example_client import ExampleClient
from common.errors import ApiError, ErrorCode


def test_example_client_initialization():
    """Test that ExampleClient initializes correctly."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    assert client.base_url == "https://api.example.com"
    assert client.api_key == "test-api-key-12345"
    assert "Authorization" in client._headers
    assert client._headers["Authorization"] == "Bearer test-api-key-12345"


def test_example_client_ping_success():
    """Test that ExampleClient.ping() handles successful response."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok", "message": "pong"}
    
    with patch('src.clients.example_client.get', return_value=mock_response):
        result = client.ping()
        
        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert "data" in result


def test_example_client_ping_error_handling():
    """Test that ExampleClient.ping() handles errors gracefully."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock HTTP error
    with patch('src.clients.example_client.get', side_effect=ApiError(
        code=ErrorCode.UPSTREAM_UNAVAILABLE,
        message="API unavailable"
    )):
        try:
            client.ping()
            assert False, "Expected ApiError to be raised"
        except ApiError as e:
            assert e.code == ErrorCode.UPSTREAM_UNAVAILABLE
            assert "API unavailable" in e.message


def test_example_client_get_data_success():
    """Test that ExampleClient.get_data() handles successful response."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "resource-123",
        "name": "Test Resource",
        "value": 42
    }
    
    with patch('src.clients.example_client.get', return_value=mock_response):
        result = client.get_data("resource-123")
        
        assert isinstance(result, dict)
        assert result["id"] == "resource-123"
        assert result["name"] == "Test Resource"


def test_example_client_get_data_not_found():
    """Test that ExampleClient.get_data() handles 404 errors."""
    client = ExampleClient(
        base_url="https://api.example.com",
        api_key="test-api-key-12345"
    )
    
    # Mock 404 error
    with patch('src.clients.example_client.get', side_effect=ApiError(
        code=ErrorCode.NOT_FOUND,
        message="Resource not found",
        status_code=404
    )):
        try:
            client.get_data("nonexistent-resource")
            assert False, "Expected ApiError to be raised"
        except ApiError as e:
            assert e.code == ErrorCode.NOT_FOUND


if __name__ == "__main__":
    # Run tests
    test_example_client_initialization()
    test_example_client_ping_success()
    test_example_client_ping_error_handling()
    test_example_client_get_data_success()
    test_example_client_get_data_not_found()
    print("All client tests passed!")
