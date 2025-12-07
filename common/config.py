"""
Configuration validation framework for MCP servers.

This module provides a base class and utilities for validating server configuration,
supporting both fail-fast and fail-soft validation strategies.

ServerConfig is a base class for server-specific configs (env vars, base URLs, API keys, etc.).
Subclasses should implement validate() to check required and optional fields and return
ConfigIssue objects.

validate_config_or_raise() provides two validation strategies:
- fail-fast: raise ConfigValidationError and typically abort server startup
- fail-soft: allow server to start, but tools should surface SERVICE_NOT_CONFIGURED with issue details
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .errors import ErrorCode


@dataclass
class ConfigIssue:
    """Represents a configuration validation issue.
    
    Attributes:
        field: The name of the configuration field with the issue
        message: Human-readable description of the issue
        critical: Whether this issue prevents the service from functioning (default: True)
    """
    field: str
    message: str
    critical: bool = True


class ServerConfig:
    """
    Base class for MCP server configuration.

    Responsibilities:
    - Load config (e.g., from env vars)
    - Validate required/optional fields
    - Provide structured validation results

    Subclasses should:
    1. Define configuration fields as instance attributes
    2. Override validate() to check required and optional fields
    3. Return a list of ConfigIssue objects for any problems found
    """

    def validate(self) -> List[ConfigIssue]:
        """
        Validate configuration and return a list of issues.
        
        Returns:
            List of ConfigIssue objects. Empty list means configuration is valid.
            Issues marked as critical=True indicate the service cannot function.
        """
        return []

    def is_valid(self) -> bool:
        """
        Check if configuration is valid (no critical issues).
        
        Returns:
            True if there are no critical issues, False otherwise.
        """
        issues = self.validate()
        return not any(issue.critical for issue in issues)


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails in fail-fast mode.
    
    This exception contains structured information about all configuration issues
    found during validation.
    """

    def __init__(self, issues: List[ConfigIssue]):
        """
        Initialize configuration validation error.
        
        Args:
            issues: List of configuration issues found during validation
        """
        self.issues = issues
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """
        Format a human-readable error message from the issues.
        
        Returns:
            Formatted error message listing all critical and non-critical issues
        """
        if not self.issues:
            return "Configuration validation failed (no details available)"

        critical_issues = [issue for issue in self.issues if issue.critical]
        non_critical_issues = [issue for issue in self.issues if not issue.critical]

        parts = ["Configuration validation failed:"]

        if critical_issues:
            parts.append("\nCritical issues (must be fixed):")
            for issue in critical_issues:
                parts.append(f"  - {issue.field}: {issue.message}")

        if non_critical_issues:
            parts.append("\nNon-critical issues (warnings):")
            for issue in non_critical_issues:
                parts.append(f"  - {issue.field}: {issue.message}")

        return "\n".join(parts)


def validate_config_or_raise(
    config: ServerConfig,
    fail_fast: bool = True,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate configuration with configurable failure strategy.

    Args:
        config: ServerConfig instance to validate
        fail_fast: If True, raise ConfigValidationError on critical issues.
                   If False, return (False, error_payload) for critical issues.

    Returns:
        Tuple of (is_valid, error_payload):
        - (True, None) if configuration is valid (no critical issues)
        - (False, error_payload) if fail_fast=False and there are critical issues.
          error_payload contains SERVICE_NOT_CONFIGURED error code and issue details.

    Raises:
        ConfigValidationError: If fail_fast=True and there are critical issues.
    """
    issues = config.validate()
    critical_issues = [issue for issue in issues if issue.critical]

    # If no critical issues, configuration is valid
    if not critical_issues:
        return (True, None)

    # If fail_fast, raise exception
    if fail_fast:
        raise ConfigValidationError(issues)

    # Otherwise, return error payload for fail-soft behavior
    error_payload = {
        "error_code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
        "message": "Service configuration is incomplete or invalid.",
        "issues": [
            {
                "field": issue.field,
                "message": issue.message,
                "critical": issue.critical,
            }
            for issue in issues
        ],
    }

    return (False, error_payload)
