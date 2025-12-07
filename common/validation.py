"""
Schema-first validation for MCP servers.

Provides JSON Schema validation for tool inputs and outputs with machine-readable
error reporting. Supports runtime validation with optional output validation gating.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    Draft7Validator = None  # type: ignore
    JsonSchemaValidationError = Exception  # type: ignore

from .errors import ValidationError, ErrorCode

# Type variable for function return types
F = TypeVar("F", bound=Callable[..., Any])


# Environment variable to control strict output validation
STRICT_OUTPUT_VALIDATION_ENV = "MCP_STRICT_OUTPUT_VALIDATION"
STRICT_OUTPUT_VALIDATION_DEFAULT = False


def _is_strict_output_validation_enabled() -> bool:
    """Check if strict output validation is enabled via environment variable."""
    return os.getenv(STRICT_OUTPUT_VALIDATION_ENV, str(STRICT_OUTPUT_VALIDATION_DEFAULT)).lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


class SchemaValidator:
    """JSON Schema validator with caching and error formatting."""

    def __init__(self, schema_base_path: Optional[Path] = None):
        """
        Initialize schema validator.

        Args:
            schema_base_path: Base path for schema files. If None, uses schemas/ relative to project root.
        """
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError(
                "jsonschema is required for validation. Install with: pip install jsonschema"
            )

        # Determine schema base path
        if schema_base_path is None:
            # Try to find project root (look for schemas/ directory)
            current = Path(__file__).resolve()
            project_root = None
            for parent in [current.parent.parent, current.parent.parent.parent]:
                if (parent / "schemas").exists():
                    project_root = parent
                    break
            if project_root is None:
                # Fallback: assume schemas/ is relative to common/
                project_root = current.parent.parent
            schema_base_path = project_root / "schemas"

        self.schema_base_path = Path(schema_base_path)
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._validator_cache: Dict[str, Draft7Validator] = {}

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load a JSON schema from file.

        Args:
            schema_name: Name of schema file (e.g., "claims_parse_edi_837" or "claims_parse_edi_837.json")

        Returns:
            Schema dictionary

        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema file is invalid JSON
        """
        # Normalize schema name
        if not schema_name.endswith(".json"):
            schema_name = f"{schema_name}.json"

        # Check cache
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        # Load from file
        schema_path = self.schema_base_path / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Cache schema
        self._schema_cache[schema_name] = schema
        return schema

    def get_validator(self, schema_name: str) -> Draft7Validator:
        """
        Get a validator for a schema (with caching).

        Args:
            schema_name: Name of schema file

        Returns:
            Draft7Validator instance
        """
        if schema_name in self._validator_cache:
            return self._validator_cache[schema_name]

        schema = self.load_schema(schema_name)
        validator = Draft7Validator(schema)
        self._validator_cache[schema_name] = validator
        return validator

    def format_validation_errors(
        self, errors: List[JsonSchemaValidationError]
    ) -> List[Dict[str, Any]]:
        """
        Format JSON Schema validation errors into machine-readable format.

        Args:
            errors: List of ValidationError from jsonschema

        Returns:
            List of formatted error dictionaries
        """
        formatted = []
        for error in errors:
            formatted_error = {
                "message": error.message,
                "path": list(error.path),
                "schema_path": list(error.schema_path),
            }

            # Add additional context
            if error.validator:
                formatted_error["validator"] = error.validator
            if error.validator_value is not None:
                formatted_error["validator_value"] = error.validator_value
            if error.instance is not None:
                formatted_error["instance"] = str(error.instance)[:200]  # Truncate long instances

            formatted.append(formatted_error)

        return formatted

    def validate_input(
        self, data: Dict[str, Any], schema_name: str, tool_name: Optional[str] = None
    ) -> None:
        """
        Validate input data against a JSON schema.

        Args:
            data: Data to validate
            schema_name: Name of input schema (e.g., "claims_parse_edi_837")
            tool_name: Optional tool name for better error messages

        Raises:
            ValidationError: If validation fails, with machine-readable validation_errors
        """
        try:
            validator = self.get_validator(schema_name)
            validator.validate(data)
        except JsonSchemaValidationError as e:
            # Collect all errors
            errors = list(validator.iter_errors(data))
            formatted_errors = self.format_validation_errors(errors)

            tool_context = f" for tool '{tool_name}'" if tool_name else ""
            message = f"Input validation failed{tool_context}: {e.message}"

            raise ValidationError(
                message=message,
                validation_errors=formatted_errors,
                details={"schema": schema_name, "tool": tool_name},
            ) from e

    def validate_output(
        self, data: Dict[str, Any], schema_name: str, tool_name: Optional[str] = None
    ) -> None:
        """
        Validate output data against a JSON schema.

        Only validates if MCP_STRICT_OUTPUT_VALIDATION environment variable is enabled.

        Args:
            data: Data to validate
            schema_name: Name of output schema (e.g., "claims_parse_edi_837_output")
            tool_name: Optional tool name for better error messages

        Raises:
            ValidationError: If validation fails (only in strict mode)
        """
        if not _is_strict_output_validation_enabled():
            return

        try:
            validator = self.get_validator(schema_name)
            validator.validate(data)
        except JsonSchemaValidationError as e:
            # Collect all errors
            errors = list(validator.iter_errors(data))
            formatted_errors = self.format_validation_errors(errors)

            tool_context = f" for tool '{tool_name}'" if tool_name else ""
            message = f"Output validation failed{tool_context}: {e.message}"

            raise ValidationError(
                message=message,
                validation_errors=formatted_errors,
                details={"schema": schema_name, "tool": tool_name},
            ) from e


# Global validator instance (lazy initialization)
_validator: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """Get or create the global schema validator instance."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


def validate_tool_input(
    tool_name: str,
    arguments: Dict[str, Any],
    schema_name: Optional[str] = None,
    validator: Optional[SchemaValidator] = None,
) -> None:
    """
    Validate tool input arguments against JSON schema.

    Args:
        tool_name: Name of the tool (e.g., "claims_parse_edi_837")
        arguments: Tool arguments to validate
        schema_name: Optional schema name. If None, infers from tool_name
        validator: Optional validator instance. If None, uses global validator

    Raises:
        ValidationError: If validation fails
    """
    if validator is None:
        validator = get_validator()

    # Infer schema name from tool name if not provided
    if schema_name is None:
        # Convert tool_name to schema name (e.g., "claims_parse_edi_837" -> "claims_parse_edi_837")
        schema_name = tool_name

    validator.validate_input(arguments, schema_name, tool_name=tool_name)


def validate_tool_output(
    tool_name: str,
    result: Dict[str, Any],
    schema_name: Optional[str] = None,
    validator: Optional[SchemaValidator] = None,
) -> None:
    """
    Validate tool output against JSON schema (only in strict mode).

    Args:
        tool_name: Name of the tool
        result: Tool result to validate
        schema_name: Optional schema name. If None, infers from tool_name
        validator: Optional validator instance. If None, uses global validator

    Raises:
        ValidationError: If validation fails (only in strict mode)
    """
    if validator is None:
        validator = get_validator()

    # Infer schema name from tool name if not provided
    if schema_name is None:
        # Convert tool_name to output schema name (e.g., "claims_parse_edi_837" -> "claims_parse_edi_837_output")
        schema_name = f"{tool_name}_output"

    validator.validate_output(result, schema_name, tool_name=tool_name)


def validated_tool(
    input_schema: Optional[str] = None,
    output_schema: Optional[str] = None,
    validator: Optional[SchemaValidator] = None,
) -> Callable[[F], F]:
    """
    Decorator to validate tool function inputs and outputs.

    Usage:
        @validated_tool(input_schema="claims_parse_edi_837", output_schema="claims_parse_edi_837_output")
        async def claims_parse_edi_837(edi_content: str) -> Dict[str, Any]:
            ...

    Args:
        input_schema: Name of input schema (inferred from function name if None)
        output_schema: Name of output schema (inferred from function name if None)
        validator: Optional validator instance

    Returns:
        Decorated function with validation
    """
    def decorator(func: F) -> F:
        tool_name = func.__name__
        input_schema_name = input_schema or tool_name
        output_schema_name = output_schema or f"{tool_name}_output"

        async def validated_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate input
            # For tool functions, arguments are typically passed as kwargs
            # If args are provided, we need to handle them differently
            if args and not kwargs:
                # Single dict argument (common pattern)
                if len(args) == 1 and isinstance(args[0], dict):
                    validate_tool_input(tool_name, args[0], input_schema_name, validator)
                    result = await func(*args, **kwargs)
                else:
                    # Multiple args - construct dict from function signature
                    # This is a simplified approach; for complex cases, use inspect
                    result = await func(*args, **kwargs)
            else:
                # Validate kwargs as input
                validate_tool_input(tool_name, kwargs, input_schema_name, validator)
                result = await func(*args, **kwargs)

            # Validate output if result is a dict
            if isinstance(result, dict):
                validate_tool_output(tool_name, result, output_schema_name, validator)

            return result

        # Handle both sync and async functions
        import inspect
        if inspect.iscoroutinefunction(func):
            return cast(F, validated_wrapper)
        else:
            # Sync version
            def validated_wrapper_sync(*args: Any, **kwargs: Any) -> Any:
                if args and not kwargs:
                    if len(args) == 1 and isinstance(args[0], dict):
                        validate_tool_input(tool_name, args[0], input_schema_name, validator)
                        result = func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                else:
                    validate_tool_input(tool_name, kwargs, input_schema_name, validator)
                    result = func(*args, **kwargs)

                if isinstance(result, dict):
                    validate_tool_output(tool_name, result, output_schema_name, validator)

                return result

            return cast(F, validated_wrapper_sync)

    return decorator
