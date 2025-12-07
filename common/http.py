"""
Unified HTTP client wrapper for MCP servers.

Provides standardized HTTP requests with:
- Timeouts (fail fast, 5-10s default)
- Retries with exponential backoff (only for idempotent GETs/searches, only on network/5xx, not 4xx)
- Circuit breaker per upstream (tracks failure rate per domain)
- Standardized error handling

Usage:
    # Sync version
    from common.http import call_upstream
    
    response = call_upstream(
        method="GET",
        url="https://api.example.com/data",
        upstream="example",
        timeout=10
    )
    
    # Async version
    from common.http import call_upstream_async
    
    response = await call_upstream_async(
        method="GET",
        url="https://api.example.com/data",
        upstream="example",
        timeout=10
    )
"""

import time
import random
from typing import Optional, Dict, Any, Literal, Union, Callable
from urllib.parse import urlparse
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from .errors import ApiError, ErrorCode, CircuitBreakerError
from .circuit_breaker import get_circuit_breaker_manager
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class CallOptions:
    """Options for HTTP calls."""
    
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    url: str = ""
    upstream: Optional[str] = None  # Upstream name (e.g., "pubmed", "sec_edgar", "turquoise")
    timeout: float = 10.0  # Timeout in seconds (5-10s default)
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = None
    data: Optional[Union[str, bytes, Dict[str, Any]]] = None
    allow_retries: bool = True  # Whether retries are allowed (only for idempotent operations)
    max_retries: int = 3
    retry_on_4xx: bool = False  # Don't retry on 4xx by default
    retry_on_5xx: bool = True  # Retry on 5xx by default
    retry_on_network: bool = True  # Retry on network errors by default
    backoff_base: float = 1.0  # Base delay for exponential backoff
    backoff_max: float = 60.0  # Maximum delay
    backoff_multiplier: float = 2.0
    verify: Union[bool, str] = True  # SSL verification
    # Cache hooks (for future integration - not used yet)
    cache_key_builder: Optional[Callable[[str, Dict[str, Any]], str]] = None  # Optional function to build cache key
    cache_ttl_seconds: Optional[int] = None  # Optional TTL for caching responses (None = no caching)


def _extract_upstream_from_url(url: str) -> str:
    """
    Extract upstream name from URL.
    
    Examples:
        "https://api.pubmed.ncbi.nlm.nih.gov/..." -> "pubmed"
        "https://api.turquoise.health/..." -> "turquoise"
        "https://www.sec.gov/..." -> "sec_edgar"
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or "unknown"
        
        # Extract meaningful part of hostname
        parts = hostname.split(".")
        if len(parts) >= 2:
            # Get second-level domain (e.g., "pubmed" from "api.pubmed.ncbi.nlm.nih.gov")
            # or first part if it's a subdomain (e.g., "sec" from "www.sec.gov")
            if parts[0] in ("api", "www", "www2"):
                return parts[1]
            return parts[0]
        return hostname
    except Exception:
        return "unknown"


def _is_retryable_status(status_code: int, options: CallOptions) -> bool:
    """Check if status code should trigger retry."""
    if 400 <= status_code < 500:
        return options.retry_on_4xx
    if status_code >= 500:
        return options.retry_on_5xx
    return False


def _is_retryable_exception(exception: Exception, options: CallOptions) -> bool:
    """Check if exception should trigger retry."""
    if not options.retry_on_network:
        return False
    
    # Network errors that should be retried
    retryable_types = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadTimeout,
        ConnectionError,
        TimeoutError,
    )
    
    return isinstance(exception, retryable_types)


def _calculate_backoff(attempt: int, options: CallOptions) -> float:
    """Calculate backoff delay with jitter."""
    delay = min(
        options.backoff_base * (options.backoff_multiplier ** attempt),
        options.backoff_max
    )
    # Add jitter (random between 0.5x and 1.5x)
    jitter = delay * (0.5 + random.random() * 0.5)
    return jitter


def call_upstream(options: CallOptions):
    """
    Make an HTTP request with timeout, retries, and circuit breaker.
    
    This is the synchronous version using requests library.
    
    Args:
        options: CallOptions with request configuration
        
    Returns:
        requests.Response object
        
    Raises:
        ApiError: For API errors (4xx, 5xx)
        CircuitBreakerError: If circuit breaker is open
        TimeoutError: If request times out
    """
    if requests is None:
        raise ImportError("requests library is required for sync HTTP calls. Install with: pip install requests")
    """
    Make an HTTP request with timeout, retries, and circuit breaker.
    
    This is the synchronous version using requests library.
    
    Args:
        options: CallOptions with request configuration
        
    Returns:
        requests.Response object
        
    Raises:
        ApiError: For API errors (4xx, 5xx)
        CircuitBreakerError: If circuit breaker is open
        TimeoutError: If request times out
    """
    # Extract upstream name if not provided
    upstream = options.upstream or _extract_upstream_from_url(options.url)
    
    # Get circuit breaker for this upstream
    circuit_breaker_manager = get_circuit_breaker_manager()
    breaker = circuit_breaker_manager.get_breaker(
        name=f"upstream_{upstream}",
        failure_threshold=5,
        timeout_seconds=60,
        success_threshold=2,
    )
    
    # Prepare request kwargs
    request_kwargs: Dict[str, Any] = {
        "method": options.method,
        "url": options.url,
        "timeout": options.timeout,
        "verify": options.verify,
    }
    
    if options.headers:
        request_kwargs["headers"] = options.headers
    
    if options.params:
        request_kwargs["params"] = options.params
    
    if options.json is not None:
        request_kwargs["json"] = options.json
    
    if options.data is not None:
        request_kwargs["data"] = options.data
    
    def _make_request() -> requests.Response:
        """Inner function to make the actual HTTP request."""
        try:
            response = requests.request(**request_kwargs)
            
            # Raise error for non-2xx status codes
            if not response.ok:
                # Check if status code indicates retryable error
                if _is_retryable_status(response.status_code, options):
                    raise ApiError(
                        message=f"Retryable error: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text[:500],  # Limit response body size
                        code=ErrorCode.UPSTREAM_UNAVAILABLE,
                    )
                raise ApiError(
                    message=f"API request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )
            
            return response
            
        except requests.exceptions.Timeout as e:
            raise ApiError(
                message=f"Request timeout after {options.timeout}s",
                original_error=e,
                code=ErrorCode.API_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            # Check if this is a retryable network error
            if _is_retryable_exception(e, options):
                raise ApiError(
                    message=f"Network error: {str(e)}",
                    original_error=e,
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                )
            raise ApiError(
                message=f"Request failed: {str(e)}",
                original_error=e,
            )
    
    # Apply retries if allowed (only for idempotent operations)
    if options.allow_retries and options.max_retries > 0:
        last_exception = None
        
        for attempt in range(options.max_retries + 1):
            try:
                # Execute through circuit breaker
                response = breaker.call(_make_request)
                return response
                
            except (ApiError, CircuitBreakerError) as e:
                last_exception = e
                
                # Don't retry on last attempt
                if attempt >= options.max_retries:
                    break
                
                # Don't retry if circuit breaker is open
                if isinstance(e, CircuitBreakerError):
                    raise
                
                # Only retry on retryable errors
                if isinstance(e, ApiError):
                    if e.code == ErrorCode.UPSTREAM_UNAVAILABLE or e.code == ErrorCode.API_TIMEOUT:
                        # Calculate backoff and wait
                        delay = _calculate_backoff(attempt, options)
                        logger.warning(
                            f"Retryable error on attempt {attempt + 1}/{options.max_retries + 1} "
                            f"for {upstream}: {e.message}. Retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)
                        continue
                
                # Don't retry on other errors
                raise
            
            except Exception as e:
                # Unexpected error, don't retry
                raise ApiError(
                    message=f"Unexpected error: {str(e)}",
                    original_error=e,
                    code=ErrorCode.INTERNAL_ERROR,
                )
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        raise ApiError(
            message=f"Request failed after {options.max_retries + 1} attempts",
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
        )
    else:
        # No retries, execute directly through circuit breaker
        return breaker.call(_make_request)


async def call_upstream_async(options: CallOptions):
    """
    Make an async HTTP request with timeout, retries, and circuit breaker.
    
    This is the asynchronous version using httpx library.
    
    Args:
        options: CallOptions with request configuration
        
    Returns:
        httpx.Response object
        
    Raises:
        ApiError: For API errors (4xx, 5xx)
        CircuitBreakerError: If circuit breaker is open
        TimeoutError: If request times out
    """
    if httpx is None:
        raise ImportError("httpx library is required for async HTTP calls. Install with: pip install httpx")
    
    import asyncio
    
    # Extract upstream name if not provided
    upstream = options.upstream or _extract_upstream_from_url(options.url)
    
    # Get circuit breaker for this upstream
    circuit_breaker_manager = get_circuit_breaker_manager()
    breaker = circuit_breaker_manager.get_breaker(
        name=f"upstream_{upstream}",
        failure_threshold=5,
        timeout_seconds=60,
        success_threshold=2,
    )
    
    # Prepare request kwargs
    request_kwargs: Dict[str, Any] = {
        "method": options.method,
        "url": options.url,
        "timeout": options.timeout,
        "verify": options.verify,
    }
    
    if options.headers:
        request_kwargs["headers"] = options.headers
    
    if options.params:
        request_kwargs["params"] = options.params
    
    if options.json is not None:
        request_kwargs["json"] = options.json
    
    if options.data is not None:
        request_kwargs["data"] = options.data
    
    async def _make_request() -> httpx.Response:
        """Inner async function to make the actual HTTP request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(**request_kwargs)
                
                # Raise error for non-2xx status codes
                if not response.is_success:
                    # Check if status code indicates retryable error
                    if _is_retryable_status(response.status_code, options):
                        raise ApiError(
                            message=f"Retryable error: {response.status_code}",
                            status_code=response.status_code,
                            response_body=response.text[:500],
                            code=ErrorCode.UPSTREAM_UNAVAILABLE,
                        )
                    raise ApiError(
                        message=f"API request failed: {response.status_code} {response.reason_phrase}",
                        status_code=response.status_code,
                        response_body=response.text[:500],
                    )
                
                return response
                
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Request timeout after {options.timeout}s",
                original_error=e,
                code=ErrorCode.API_TIMEOUT,
            )
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.NetworkError) as e:
            # Check if this is a retryable network error
            if _is_retryable_exception(e, options):
                raise ApiError(
                    message=f"Network error: {str(e)}",
                    original_error=e,
                    code=ErrorCode.UPSTREAM_UNAVAILABLE,
                )
            raise ApiError(
                message=f"Request failed: {str(e)}",
                original_error=e,
            )
        except httpx.HTTPStatusError as e:
            raise ApiError(
                message=f"HTTP error: {e.response.status_code} {e.response.reason_phrase}",
                status_code=e.response.status_code,
                response_body=e.response.text[:500],
            )
    
    # Apply retries if allowed (only for idempotent operations)
    if options.allow_retries and options.max_retries > 0:
        last_exception = None
        
        for attempt in range(options.max_retries + 1):
            try:
                # Execute through circuit breaker
                response = await breaker.call_async(_make_request)
                return response
                
            except (ApiError, CircuitBreakerError) as e:
                last_exception = e
                
                # Don't retry on last attempt
                if attempt >= options.max_retries:
                    break
                
                # Don't retry if circuit breaker is open
                if isinstance(e, CircuitBreakerError):
                    raise
                
                # Only retry on retryable errors
                if isinstance(e, ApiError):
                    if e.code == ErrorCode.UPSTREAM_UNAVAILABLE or e.code == ErrorCode.API_TIMEOUT:
                        # Calculate backoff and wait
                        delay = _calculate_backoff(attempt, options)
                        logger.warning(
                            f"Retryable error on attempt {attempt + 1}/{options.max_retries + 1} "
                            f"for {upstream}: {e.message}. Retrying in {delay:.2f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                
                # Don't retry on other errors
                raise
            
            except Exception as e:
                # Unexpected error, don't retry
                raise ApiError(
                    message=f"Unexpected error: {str(e)}",
                    original_error=e,
                    code=ErrorCode.INTERNAL_ERROR,
                )
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        raise ApiError(
            message=f"Request failed after {options.max_retries + 1} attempts",
            code=ErrorCode.UPSTREAM_UNAVAILABLE,
        )
    else:
        # No retries, execute directly through circuit breaker
        return await breaker.call_async(_make_request)


# Convenience functions for common use cases
def get(
    url: str,
    upstream: Optional[str] = None,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    allow_retries: bool = True,
    **kwargs
):
    """
    Convenience function for GET requests.
    
    Args:
        url: Request URL
        upstream: Upstream name (auto-detected from URL if not provided)
        timeout: Request timeout in seconds
        headers: Request headers
        params: Query parameters
        allow_retries: Whether to allow retries (default: True for GET)
        **kwargs: Additional options passed to CallOptions
        
    Returns:
        requests.Response object
    """
    options = CallOptions(
        method="GET",
        url=url,
        upstream=upstream,
        timeout=timeout,
        headers=headers,
        params=params,
        allow_retries=allow_retries,
        **kwargs
    )
    return call_upstream(options)


async def get_async(
    url: str,
    upstream: Optional[str] = None,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    allow_retries: bool = True,
    **kwargs
):
    """
    Convenience function for async GET requests.
    
    Args:
        url: Request URL
        upstream: Upstream name (auto-detected from URL if not provided)
        timeout: Request timeout in seconds
        headers: Request headers
        params: Query parameters
        allow_retries: Whether to allow retries (default: True for GET)
        **kwargs: Additional options passed to CallOptions
        
    Returns:
        httpx.Response object
    """
    options = CallOptions(
        method="GET",
        url=url,
        upstream=upstream,
        timeout=timeout,
        headers=headers,
        params=params,
        allow_retries=allow_retries,
        **kwargs
    )
    return await call_upstream_async(options)


def post(
    url: str,
    upstream: Optional[str] = None,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
    allow_retries: bool = False,  # POST is not idempotent by default
    **kwargs
):
    """
    Convenience function for POST requests.
    
    Args:
        url: Request URL
        upstream: Upstream name (auto-detected from URL if not provided)
        timeout: Request timeout in seconds
        headers: Request headers
        json: JSON body
        data: Form data or raw body
        allow_retries: Whether to allow retries (default: False for POST)
        **kwargs: Additional options passed to CallOptions
        
    Returns:
        requests.Response object
    """
    options = CallOptions(
        method="POST",
        url=url,
        upstream=upstream,
        timeout=timeout,
        headers=headers,
        json=json,
        data=data,
        allow_retries=allow_retries,
        **kwargs
    )
    return call_upstream(options)


async def post_async(
    url: str,
    upstream: Optional[str] = None,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
    allow_retries: bool = False,  # POST is not idempotent by default
    **kwargs
):
    """
    Convenience function for async POST requests.
    
    Args:
        url: Request URL
        upstream: Upstream name (auto-detected from URL if not provided)
        timeout: Request timeout in seconds
        headers: Request headers
        json: JSON body
        data: Form data or raw body
        allow_retries: Whether to allow retries (default: False for POST)
        **kwargs: Additional options passed to CallOptions
        
    Returns:
        httpx.Response object
    """
    options = CallOptions(
        method="POST",
        url=url,
        upstream=upstream,
        timeout=timeout,
        headers=headers,
        json=json,
        data=data,
        allow_retries=allow_retries,
        **kwargs
    )
    return await call_upstream_async(options)
