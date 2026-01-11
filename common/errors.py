"""
Standardized error handling for MCP servers.

Provides error classes and standard error response formatting.
"""

import traceback
from enum import Enum
from typing import Any, Dict, Optional, Type, Callable
import functools
import requests

# Try to import httpx (optional dependency for async HTTP clients)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class ErrorCode(str, Enum):
    """Standard error codes for MCP servers.
    
    Simplified error codes for LLM-friendly error handling:
    - UPSTREAM_UNAVAILABLE: API down, timeout, 5xx errors
    - BAD_REQUEST: Invalid arguments, schema validation failures
    - RATE_LIMITED: Rate limit exceeded (from provider or internal limiter)
    - NOT_FOUND: Resource not found
    - INTERNAL_ERROR: Unexpected internal errors
    """

    # Simplified error codes (primary)
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    BAD_REQUEST = "BAD_REQUEST"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Legacy/Detailed error codes (for backward compatibility)
    API_ERROR = "API_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_UNAUTHORIZED = "API_UNAUTHORIZED"
    API_FORBIDDEN = "API_FORBIDDEN"
    API_NOT_FOUND = "API_NOT_FOUND"
    API_SERVER_ERROR = "API_SERVER_ERROR"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # BAD_REQUEST already defined above in primary error codes
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # System Errors
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    # Service is disabled or unusable because required configuration is missing or invalid
    # (e.g., env vars, base URLs, credentials). Used for fail-soft behavior where the server
    # runs but specific tools are disabled with clear error messages.
    SERVICE_NOT_CONFIGURED = "SERVICE_NOT_CONFIGURED"

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
        use_simplified_codes: bool = True,
        **kwargs,
    ):
        """Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body (if available)
            use_simplified_codes: If True, use simplified error codes (UPSTREAM_UNAVAILABLE, etc.)
                                 If False, use detailed error codes (API_ERROR, etc.)
            **kwargs: Additional arguments passed to McpError
        """
        details = kwargs.get("details", {})
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body

        # Map HTTP status codes to error codes
        if use_simplified_codes:
            # Use simplified error codes for LLM-friendly error handling
            if status_code == 404:
                code = ErrorCode.NOT_FOUND
            elif status_code == 429:
                code = ErrorCode.RATE_LIMITED
                kwargs.setdefault("retry_after", 60)
            elif status_code and 400 <= status_code < 500:
                code = ErrorCode.BAD_REQUEST
            elif status_code and status_code >= 500:
                code = ErrorCode.UPSTREAM_UNAVAILABLE
            else:
                code = ErrorCode.UPSTREAM_UNAVAILABLE
        else:
            # Use detailed error codes for backward compatibility
            code = kwargs.pop("code", ErrorCode.API_ERROR)
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

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        validation_errors: Optional[list] = None,
        **kwargs,
    ):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Field that failed validation (optional)
            validation_errors: List of machine-readable validation errors from JSON Schema
            **kwargs: Additional arguments passed to McpError
        """
        code = kwargs.pop("code", ErrorCode.BAD_REQUEST)
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if validation_errors:
            details["validation_errors"] = validation_errors

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


def map_upstream_error(error: Exception) -> McpError:
    """
    Map upstream errors (HTTP exceptions, timeouts, etc.) to standardized MCP errors.
    
    This function categorizes common upstream errors into the simplified error codes
    that LLMs can reason about:
    - UPSTREAM_UNAVAILABLE: API down, timeout, 5xx errors
    - BAD_REQUEST: Invalid arguments, schema validation failures
    - RATE_LIMITED: Rate limit exceeded
    - NOT_FOUND: Resource not found
    - INTERNAL_ERROR: Unexpected errors
    
    Args:
        error: The upstream exception to map
        
    Returns:
        McpError with appropriate error code
    """
    # Handle requests library exceptions
    if isinstance(error, requests.exceptions.Timeout):
        return McpError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Request to upstream service timed out",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    if isinstance(error, requests.exceptions.ConnectionError):
        return McpError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Unable to connect to upstream service",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    if isinstance(error, requests.exceptions.HTTPError):
        response = getattr(error.response, 'status_code', None)
        if response == 404:
            return McpError(
                code=ErrorCode.NOT_FOUND,
                message="Resource not found",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
        elif response == 429:
            retry_after = None
            if hasattr(error.response, 'headers'):
                retry_after_header = error.response.headers.get('Retry-After')
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except (ValueError, TypeError):
                        pass
            return McpError(
                code=ErrorCode.RATE_LIMITED,
                message="Rate limit exceeded",
                details={"status_code": response, "error_type": type(error).__name__},
                retry_after=retry_after or 60,
                original_error=error,
            )
        elif response and 400 <= response < 500:
            return McpError(
                code=ErrorCode.BAD_REQUEST,
                message=f"Invalid request: {str(error)}",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
        elif response and response >= 500:
            return McpError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="Upstream service error",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
    
    # Handle httpx library exceptions (async HTTP client)
    if HTTPX_AVAILABLE and isinstance(error, httpx.TimeoutException):
        return McpError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Request to upstream service timed out",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    if isinstance(error, httpx.ConnectError):
        return McpError(
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
            message="Unable to connect to upstream service",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    if HTTPX_AVAILABLE and isinstance(error, httpx.HTTPStatusError):
        response = error.response.status_code
        if response == 404:
            return McpError(
                code=ErrorCode.NOT_FOUND,
                message="Resource not found",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
        elif response == 429:
            retry_after = None
            if hasattr(error.response, 'headers'):
                retry_after_header = error.response.headers.get('Retry-After')
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except (ValueError, TypeError):
                        pass
            return McpError(
                code=ErrorCode.RATE_LIMITED,
                message="Rate limit exceeded",
                details={"status_code": response, "error_type": type(error).__name__},
                retry_after=retry_after or 60,
                original_error=error,
            )
        elif 400 <= response < 500:
            return McpError(
                code=ErrorCode.BAD_REQUEST,
                message=f"Invalid request: {str(error)}",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
        elif response >= 500:
            return McpError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="Upstream service error",
                details={"status_code": response, "error_type": type(error).__name__},
                original_error=error,
            )
    
    # Handle validation errors
    if isinstance(error, (ValueError, TypeError, KeyError)):
        return McpError(
            code=ErrorCode.BAD_REQUEST,
            message=f"Invalid input: {str(error)}",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    # Handle file not found
    if isinstance(error, FileNotFoundError):
        return McpError(
            code=ErrorCode.NOT_FOUND,
            message=f"Resource not found: {str(error)}",
            details={"error_type": type(error).__name__},
            original_error=error,
        )
    
    # Handle known MCP errors (pass through)
    if isinstance(error, McpError):
        return error
    
    # Default to internal error for unknown exceptions
    return McpError(
        code=ErrorCode.INTERNAL_ERROR,
        message=f"An unexpected error occurred: {str(error)}",
        details={"error_type": type(error).__name__},
        original_error=error,
    )


def handle_mcp_tool_error(func: Callable) -> Callable:
    """
    Decorator to automatically catch and convert exceptions in MCP tool functions.
    
    This decorator wraps MCP tool functions to:
    1. Catch all exceptions
    2. Map them to standardized McpError using map_upstream_error
    3. Return structured JSON error response instead of raising
    
    Usage:
        @handle_mcp_tool_error
        async def my_tool(arg1: str) -> Dict[str, Any]:
            # Tool implementation
            return {"result": "success"}
    
    Args:
        func: The MCP tool function to wrap
        
    Returns:
        Wrapped function that returns structured error responses
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Map the error to a standardized MCP error
            mcp_error = map_upstream_error(e)
            # Return structured error response (never a stack trace)
            return {
                "error": mcp_error.to_dict(include_traceback=False),
                "success": False,
            }
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        """Synchronous version of the wrapper."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Map the error to a standardized MCP error
            mcp_error = map_upstream_error(e)
            # Return structured error response (never a stack trace)
            return {
                "error": mcp_error.to_dict(include_traceback=False),
                "success": False,
            }
    
    # Return async wrapper if function is async, sync wrapper otherwise
    import inspect
    if inspect.iscoroutinefunction(func):
        return wrapper
    else:
        return sync_wrapper

