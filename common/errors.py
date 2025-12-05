"""
Standardized error handling for MCP servers.

Provides error classes and standard error response formatting.
"""

import traceback
from enum import Enum
from typing import Any, Dict, Optional, Type


class ErrorCode(str, Enum):
    """Standard error codes for MCP servers."""

    # API Errors
    API_ERROR = "API_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_UNAUTHORIZED = "API_UNAUTHORIZED"
    API_FORBIDDEN = "API_FORBIDDEN"
    API_NOT_FOUND = "API_NOT_FOUND"
    API_SERVER_ERROR = "API_SERVER_ERROR"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # System Errors
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Data Errors
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_PARSE_ERROR = "DATA_PARSE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"


class McpError(Exception):
    """Base exception class for MCP server errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        docs_url: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize MCP error.

        Args:
            code: Error code from ErrorCode enum
            message: Human-readable error message
            details: Additional error details
            retry_after: Seconds to wait before retrying (for rate limits)
            docs_url: URL to documentation about this error
            original_error: Original exception that caused this error
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after
        self.docs_url = docs_url
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self, include_traceback: bool = False) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        error_dict = {
            "code": self.code.value,
            "message": self.message,
        }

        if self.details:
            error_dict["details"] = self.details

        if self.retry_after is not None:
            error_dict["retry_after"] = self.retry_after

        if self.docs_url:
            error_dict["docs_url"] = self.docs_url

        if include_traceback and self.original_error:
            error_dict["traceback"] = traceback.format_exception(
                type(self.original_error),
                self.original_error,
                self.original_error.__traceback__,
            )

        return error_dict


class ApiError(McpError):
    """Error raised when API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs,
    ):
        """Initialize API error."""
        code = kwargs.pop("code", ErrorCode.API_ERROR)
        details = kwargs.get("details", {})
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body

        # Map HTTP status codes to error codes
        if status_code == 401:
            code = ErrorCode.API_UNAUTHORIZED
        elif status_code == 403:
            code = ErrorCode.API_FORBIDDEN
        elif status_code == 404:
            code = ErrorCode.API_NOT_FOUND
        elif status_code == 429:
            code = ErrorCode.API_RATE_LIMIT
            kwargs.setdefault("retry_after", 60)
        elif status_code and status_code >= 500:
            code = ErrorCode.API_SERVER_ERROR

        kwargs["details"] = details
        super().__init__(code, message, **kwargs)


class ValidationError(McpError):
    """Error raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        """Initialize validation error."""
        code = kwargs.pop("code", ErrorCode.VALIDATION_ERROR)
        details = kwargs.get("details", {})
        if field:
            details["field"] = field

        kwargs["details"] = details
        super().__init__(code, message, **kwargs)


class RateLimitError(McpError):
    """Error raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        """Initialize rate limit error."""
        super().__init__(
            ErrorCode.RATE_LIMIT_EXCEEDED, message, retry_after=retry_after, **kwargs
        )


class CircuitBreakerError(McpError):
    """Error raised when circuit breaker is open."""

    def __init__(self, message: str, **kwargs):
        """Initialize circuit breaker error."""
        super().__init__(ErrorCode.CIRCUIT_BREAKER_OPEN, message, **kwargs)


def format_error_response(
    error: Exception,
    include_traceback: bool = False,
    docs_base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Format an exception as a standard error response.

    Args:
        error: Exception to format
        include_traceback: Whether to include traceback in response
        docs_base_url: Base URL for documentation links

    Returns:
        Standardized error response dictionary
    """
    if isinstance(error, McpError):
        error_dict = error.to_dict(include_traceback=include_traceback)
    else:
        # Convert unknown exceptions to internal error
        error_dict = {
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": str(error) or "An unexpected error occurred",
        }

        if include_traceback:
            error_dict["traceback"] = traceback.format_exception(
                type(error), error, error.__traceback__
            )

    # Add docs URL if base URL provided
    if docs_base_url and "docs_url" not in error_dict:
        error_dict["docs_url"] = f"{docs_base_url}/errors/{error_dict['code']}"

    return {"error": error_dict}


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None,
    docs_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standard error response dictionary.

    Args:
        code: Error code
        message: Error message
        details: Additional details
        retry_after: Retry after seconds
        docs_url: Documentation URL

    Returns:
        Error response dictionary
    """
    error = McpError(
        code=code,
        message=message,
        details=details,
        retry_after=retry_after,
        docs_url=docs_url,
    )
    return format_error_response(error)

