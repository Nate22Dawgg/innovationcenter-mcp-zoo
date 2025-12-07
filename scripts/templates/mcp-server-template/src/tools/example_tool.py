"""
Example MCP tool implementation.

This is a template file. When creating a new MCP server from this template:
1. Copy this file to your server directory
2. Rename example_tool to your_tool_name
3. Implement your actual tool logic
4. Add schema-based validation using common.validation.validate_tool_input
5. Add proper error handling using common.errors
6. Add caching using common.cache (optional but recommended)
7. Add observability using common.observability decorators (optional but recommended)

This demonstrates:
- Input validation with JSON schemas
- Caching for expensive operations
- Observability (metrics, logging, tracing)
- Error handling with structured responses
- SERVICE_NOT_CONFIGURED handling (fail-soft behavior)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.clients.example_client import ExampleClient
from common.errors import ErrorCode, format_error_response, map_upstream_error, ValidationError
from common.config import validate_config_or_raise
from common.logging import get_logger
from common.cache import get_cache, build_cache_key

# Optional: Import validation utilities (if schemas are available)
try:
    from common.validation import validate_tool_input, validate_tool_output
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

# Optional: Import observability decorators
try:
    from common.observability import observe_tool_call_sync
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

logger = get_logger(__name__)


def example_tool(
    client: Optional[ExampleClient],
    config_error_payload: Optional[Dict[str, Any]] = None,
    message: str = "Hello"
) -> Dict[str, Any]:
    """
    Example tool that demonstrates the template structure.
    
    This demonstrates:
    - Checking for SERVICE_NOT_CONFIGURED (fail-soft behavior)
    - Input validation (schema-based if available)
    - Using the client to make API calls
    - Optional caching for expensive operations
    - Graceful error handling with structured error responses
    
    Args:
        client: Initialized client instance (None if service not configured)
        config_error_payload: Error payload if configuration is invalid (fail-soft mode)
        message: Input message to process
    
    Returns:
        Dictionary with tool result or error response
    
    Note: In a real server, you should:
    1. Add a JSON schema for this tool's input in schemas/example_tool.json
    2. Enable validation by uncommenting the validate_tool_input call below
    3. Optionally add observability decorator: @observe_tool_call_sync(server_name="template-mcp-server")
    """
    # Check if service is configured (fail-soft behavior)
    if config_error_payload is not None:
        logger.warning("Tool called but service is not configured")
        return config_error_payload
    
    if client is None:
        # This should not happen if config validation passed, but handle gracefully
        return format_error_response(
            error=None,
            include_traceback=False
        )["error"]  # Return just the error dict for consistency
    
    # Input validation - schema-based if available
    try:
        if VALIDATION_AVAILABLE:
            # Uncomment this when you have a schema file:
            # validate_tool_input("example_tool", {"message": message})
            pass
    except ValidationError as e:
        logger.error(f"Input validation failed: {e.message}")
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": e.message,
                "validation_errors": e.validation_errors if hasattr(e, "validation_errors") else None,
                "details": {"field": "message", "value": message}
            }
        }
    
    # Basic input validation (fallback if schema validation not available)
    if not message or not isinstance(message, str):
        logger.error("Invalid input: message must be a non-empty string")
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": "message must be a non-empty string",
                "details": {"field": "message", "value": message}
            }
        }
    
    # Optional: Check cache first (for expensive operations)
    # Uncomment and customize if you want to cache results:
    # cache = get_cache()
    # cache_key = build_cache_key("template-mcp-server", "example_tool", {"message": message})
    # cached_result = cache.get(cache_key)
    # if cached_result is not None:
    #     logger.info("Returning cached result")
    #     return cached_result
    
    try:
        # Use the client to perform operations
        logger.info(f"Processing message: {message}")
        status_response = client.ping()
        
        # Transform the response into the expected output format
        result = {
            "success": True,
            "status": status_response.get("status", "unknown"),
            "message": message,
            "processed": True,
            "data": status_response.get("data")
        }
        
        # Optional: Cache the result (uncomment if caching is enabled above)
        # cache.set(cache_key, result, ttl_seconds=300)  # Cache for 5 minutes
        
        # Optional: Validate output against schema (only in strict mode)
        if VALIDATION_AVAILABLE:
            # Uncomment when you have an output schema:
            # validate_tool_output("example_tool", result)
            pass
        
        logger.info("Tool execution successful")
        return result
        
    except Exception as e:
        # Map upstream errors to standardized MCP errors
        mcp_error = map_upstream_error(e)
        logger.error(f"Tool execution failed: {mcp_error.message}")
        
        # Return structured error response
        return format_error_response(
            error=mcp_error,
            include_traceback=False
        )["error"]  # Return just the error dict for consistency


def example_get_data_tool(
    client: Optional[ExampleClient],
    config_error_payload: Optional[Dict[str, Any]] = None,
    resource_id: str = ""
) -> Dict[str, Any]:
    """
    Another example tool demonstrating different patterns with caching.
    
    This shows how to handle a more complex tool with resource IDs and caching.
    
    Args:
        client: Initialized client instance
        config_error_payload: Error payload if configuration is invalid
        resource_id: ID of the resource to fetch
    
    Returns:
        Dictionary with tool result or error response
    
    Note: This example demonstrates caching for expensive operations.
    """
    # Check if service is configured
    if config_error_payload is not None:
        return config_error_payload
    
    if client is None:
        return {
            "error": {
                "code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
                "message": "Service is not configured"
            }
        }
    
    # Input validation - schema-based if available
    try:
        if VALIDATION_AVAILABLE:
            # Uncomment this when you have a schema file:
            # validate_tool_input("example_get_data", {"resource_id": resource_id})
            pass
    except ValidationError as e:
        logger.error(f"Input validation failed: {e.message}")
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": e.message,
                "validation_errors": e.validation_errors if hasattr(e, "validation_errors") else None
            }
        }
    
    # Basic input validation (fallback)
    if not resource_id or not isinstance(resource_id, str):
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": "resource_id must be a non-empty string"
            }
        }
    
    # Check cache first (caching is useful for read operations)
    cache = get_cache()
    cache_key = build_cache_key("template-mcp-server", "example_get_data", {"resource_id": resource_id})
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Returning cached result for resource_id: {resource_id}")
        return cached_result
    
    try:
        # Fetch from API
        data = client.get_data(resource_id)
        result = {
            "success": True,
            "resource_id": resource_id,
            "data": data
        }
        
        # Cache the result (TTL: 5 minutes)
        cache.set(cache_key, result, ttl_seconds=300)
        logger.info(f"Cached result for resource_id: {resource_id}")
        
        return result
    except Exception as e:
        mcp_error = map_upstream_error(e)
        return format_error_response(
            error=mcp_error,
            include_traceback=False
        )["error"]
