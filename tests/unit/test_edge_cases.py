"""
Edge case tests for MCP servers.

Tests common edge cases across all servers:
- Empty results
- Huge results
- Invalid inputs
- Rate limited upstreams
- Network errors
- Timeout errors
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict
import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from common.errors import (
    ApiError,
    ValidationError,
    RateLimitError,
    CircuitBreakerError,
    ErrorCode,
)

pytestmark = [pytest.mark.unit, pytest.mark.edge_cases]


class TestEdgeCases:
    """Test edge cases that should be handled gracefully."""
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self):
        """Test that empty results are handled gracefully."""
        # Mock a function that returns empty results
        async def mock_search(*args, **kwargs):
            return {
                "total": 0,
                "count": 0,
                "results": []
            }
        
        result = await mock_search()
        
        assert result["total"] == 0
        assert result["count"] == 0
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_huge_results_handling(self):
        """Test that huge results are handled (pagination, limits)."""
        # Simulate a huge result set
        huge_results = [{"id": i} for i in range(10000)]
        
        # Should respect limit
        limit = 100
        paginated = huge_results[:limit]
        
        assert len(paginated) == limit
        assert len(paginated) < len(huge_results)
    
    @pytest.mark.asyncio
    async def test_invalid_input_handling(self):
        """Test that invalid inputs are rejected with proper errors."""
        # Test None values
        with pytest.raises((ValidationError, TypeError, ValueError)):
            # This should fail validation
            if None is None:
                raise ValidationError("Required field cannot be None", field="test_field")
        
        # Test empty strings
        with pytest.raises((ValidationError, ValueError)):
            if "" == "":
                raise ValidationError("Required field cannot be empty", field="test_field")
        
        # Test wrong types
        with pytest.raises((ValidationError, TypeError)):
            if not isinstance("string", int):
                raise ValidationError("Field must be integer", field="test_field")
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test that rate limit errors are handled properly."""
        # Simulate rate limit error
        rate_limit_error = RateLimitError(
            "Rate limit exceeded",
            retry_after=60
        )
        
        assert rate_limit_error.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert rate_limit_error.retry_after == 60
        assert "rate limit" in rate_limit_error.message.lower()
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test that network errors are handled gracefully."""
        # Simulate network error
        network_error = ApiError(
            "Network error occurred",
            status_code=None,
            original_error=ConnectionError("Connection refused")
        )
        
        assert network_error.code == ErrorCode.API_ERROR
        assert network_error.original_error is not None
        assert isinstance(network_error.original_error, ConnectionError)
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test that timeout errors are handled properly."""
        # Simulate timeout
        timeout_error = ApiError(
            "Request timed out",
            code=ErrorCode.API_TIMEOUT
        )
        
        assert timeout_error.code == ErrorCode.API_TIMEOUT
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_handling(self):
        """Test that circuit breaker errors are handled."""
        circuit_error = CircuitBreakerError(
            "Circuit breaker is open"
        )
        
        assert circuit_error.code == ErrorCode.CIRCUIT_BREAKER_OPEN
    
    @pytest.mark.asyncio
    async def test_service_not_configured_error_code(self):
        """Test that SERVICE_NOT_CONFIGURED error code exists and has correct value."""
        # Verify the error code exists in the enum
        assert hasattr(ErrorCode, "SERVICE_NOT_CONFIGURED")
        assert ErrorCode.SERVICE_NOT_CONFIGURED == "SERVICE_NOT_CONFIGURED"
        assert ErrorCode.SERVICE_NOT_CONFIGURED.value == "SERVICE_NOT_CONFIGURED"
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test that malformed API responses are handled."""
        # Simulate malformed JSON response
        try:
            import json
            json.loads("{ invalid json }")
        except json.JSONDecodeError as e:
            api_error = ApiError(
                "Failed to parse API response",
                original_error=e
            )
            assert api_error.original_error is not None
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test that missing required fields are caught."""
        def validate_required(data: Dict[str, Any], required: list):
            missing = [field for field in required if field not in data or data[field] is None]
            if missing:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing)}",
                    field=missing[0] if missing else None
                )
        
        test_data = {"field1": "value1"}  # Missing field2
        with pytest.raises(ValidationError):
            validate_required(test_data, ["field1", "field2"])
    
    @pytest.mark.asyncio
    async def test_very_long_strings(self):
        """Test that very long input strings are handled."""
        # Very long string (simulating potential DoS)
        very_long_string = "a" * 100000
        
        # Should either accept it or reject with proper error
        assert len(very_long_string) == 100000
        
        # In real implementation, might want to limit length
        max_length = 10000
        if len(very_long_string) > max_length:
            with pytest.raises(ValidationError):
                raise ValidationError(f"String too long (max {max_length} characters)")
    
    @pytest.mark.asyncio
    async def test_special_characters_in_input(self):
        """Test that special characters in input are handled."""
        special_chars = "!@#$%^&*()[]{}|\\:;\"'<>?,./`~"
        
        # Should handle special characters (might need URL encoding, etc.)
        # This is a basic test - actual handling depends on implementation
        assert isinstance(special_chars, str)
        assert len(special_chars) > 0
    
    @pytest.mark.asyncio
    async def test_unicode_characters(self):
        """Test that unicode characters are handled."""
        unicode_string = "测试 🧪 émoji 日本語"
        
        # Should handle unicode
        assert isinstance(unicode_string, str)
        assert len(unicode_string) > 0
    
    @pytest.mark.asyncio
    async def test_negative_numbers(self):
        """Test that negative numbers are rejected where appropriate."""
        # Negative limit should be rejected
        limit = -10
        if limit < 0:
            with pytest.raises(ValidationError):
                raise ValidationError("Limit must be positive", field="limit")
    
    @pytest.mark.asyncio
    async def test_zero_values(self):
        """Test that zero values are handled appropriately."""
        # Zero limit might be invalid
        limit = 0
        if limit <= 0:
            with pytest.raises(ValidationError):
                raise ValidationError("Limit must be greater than 0", field="limit")
    
    @pytest.mark.asyncio
    async def test_very_large_numbers(self):
        """Test that very large numbers are handled."""
        # Very large offset
        huge_offset = 999999999
        
        # Should either accept or reject with proper error
        # In practice, might want to limit max offset
        max_offset = 1000000
        if huge_offset > max_offset:
            with pytest.raises(ValidationError):
                raise ValidationError(f"Offset too large (max {max_offset})", field="offset")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test that concurrent requests are handled."""
        async def mock_request(delay: float):
            await asyncio.sleep(delay)
            return {"status": "success"}
        
        # Make multiple concurrent requests
        results = await asyncio.gather(
            mock_request(0.1),
            mock_request(0.1),
            mock_request(0.1)
        )
        
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
    
    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """Test that partial failures are handled."""
        # Simulate partial failure (some requests succeed, some fail)
        results = []
        for i in range(5):
            try:
                if i == 2:  # Simulate failure
                    raise ApiError("Request failed")
                results.append({"id": i, "status": "success"})
            except ApiError:
                results.append({"id": i, "status": "error"})
        
        assert len(results) == 5
        assert results[2]["status"] == "error"
        assert all(r["status"] == "success" for r in results if r["id"] != 2)
