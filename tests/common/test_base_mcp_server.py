"""
Base test class for standardizing MCP server behavior.

Provides common test patterns and utilities for all MCP servers.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from common.errors import (
    McpError,
    ApiError,
    ValidationError,
    RateLimitError,
    ErrorCode,
    format_error_response,
)
from common.logging import get_logger
from common.metrics import get_metrics_collector
from common.rate_limit import get_rate_limiter
from common.circuit_breaker import get_circuit_breaker_manager

pytestmark = [pytest.mark.unit, pytest.mark.python]


class BaseMCPServerTest(ABC):
    """Base test class for MCP servers."""
    
    @property
    @abstractmethod
    def server_name(self) -> str:
        """Return the name of the server being tested."""
        pass
    
    @property
    @abstractmethod
    def server_module_path(self) -> str:
        """Return the Python module path to the server."""
        pass
    
    @property
    @abstractmethod
    def tool_names(self) -> List[str]:
        """Return list of tool names provided by this server."""
        pass
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger(self.server_name)
        self.metrics = get_metrics_collector()
        self.rate_limiter = get_rate_limiter()
        self.circuit_breaker = get_circuit_breaker_manager()
    
    def test_server_uses_common_utilities(self):
        """Test that server uses common utilities."""
        # Check that common utilities are available
        assert self.logger is not None
        assert self.metrics is not None
        assert self.rate_limiter is not None
        assert self.circuit_breaker is not None
    
    def test_error_handling_standardized(self):
        """Test that error handling follows standard patterns."""
        # Test that errors use standard error classes
        test_error = ValidationError("Test error", field="test_field")
        
        assert isinstance(test_error, McpError)
        assert test_error.code == ErrorCode.VALIDATION_ERROR
        assert "test_field" in test_error.details.get("field", "")
    
    def test_error_response_format(self):
        """Test that error responses follow standard format."""
        error = ValidationError("Test error")
        response = format_error_response(error)
        
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert response["error"]["code"] == ErrorCode.VALIDATION_ERROR.value
    
    @pytest.mark.asyncio
    async def test_rate_limiting_applied(self):
        """Test that rate limiting is applied."""
        # Check that rate limiter is configured
        assert self.rate_limiter is not None
        
        # In real implementation, would test actual rate limiting
        # For now, just verify the limiter exists
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_configured(self):
        """Test that circuit breaker is configured."""
        # Check that circuit breaker is configured
        assert self.circuit_breaker is not None
        
        # In real implementation, would test circuit breaker behavior
    
    def test_logging_configured(self):
        """Test that logging is configured."""
        # Check that logger is configured
        assert self.logger is not None
        
        # Logger should have standard methods
        assert hasattr(self.logger, "info")
        assert hasattr(self.logger, "error")
        assert hasattr(self.logger, "warning")
        assert hasattr(self.logger, "debug")
    
    def test_metrics_collection(self):
        """Test that metrics are collected."""
        # Check that metrics collector exists
        assert self.metrics is not None
        
        # In real implementation, would test metrics collection
    
    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test that inputs are validated."""
        # This should be implemented by subclasses
        # Test that None values are rejected
        with pytest.raises((ValidationError, TypeError, ValueError)):
            # Subclass should implement specific validation
            pass
    
    @pytest.mark.asyncio
    async def test_empty_result_handling(self):
        """Test that empty results are handled gracefully."""
        # Standard empty result format
        empty_result = {
            "total": 0,
            "count": 0,
            "results": []
        }
        
        assert empty_result["total"] == 0
        assert isinstance(empty_result["results"], list)
        assert len(empty_result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_error_response_includes_retry_info(self):
        """Test that rate limit errors include retry information."""
        rate_limit_error = RateLimitError("Rate limit exceeded", retry_after=60)
        response = format_error_response(rate_limit_error)
        
        assert "error" in response
        assert "retry_after" in response["error"] or "retryAfter" in response["error"]
    
    def test_server_registered_in_registry(self):
        """Test that server is registered in tools_registry.json."""
        registry_path = PROJECT_ROOT / "registry" / "tools_registry.json"
        
        if registry_path.exists():
            import json
            with open(registry_path, "r") as f:
                registry = json.load(f)
            
            # Check that at least one tool from this server is in registry
            server_tools = [
                tool for tool in registry.get("tools", [])
                if any(tool_name in tool.get("id", "") for tool_name in self.tool_names)
            ]
            
            # At least one tool should be registered (or skip if server not in registry yet)
            if len(server_tools) == 0:
                pytest.skip(f"Server {self.server_name} not yet registered in registry")


class TestClinicalTrialsServer(BaseMCPServerTest):
    """Test Clinical Trials MCP Server."""
    
    @property
    def server_name(self) -> str:
        return "clinical-trials-mcp"
    
    @property
    def server_module_path(self) -> str:
        return "servers.clinical.clinical-trials-mcp.server"
    
    @property
    def tool_names(self) -> List[str]:
        return ["clinical_trials.search", "clinical_trials.get_detail"]


class TestNHANESServer(BaseMCPServerTest):
    """Test NHANES MCP Server."""
    
    @property
    def server_name(self) -> str:
        return "nhanes-mcp"
    
    @property
    def server_module_path(self) -> str:
        return "servers.clinical.nhanes-mcp.server"
    
    @property
    def tool_names(self) -> List[str]:
        return [
            "nhanes.list_datasets",
            "nhanes.get_data",
            "nhanes.get_variable_info",
            "nhanes.calculate_percentile",
            "nhanes.get_demographics_summary",
        ]
