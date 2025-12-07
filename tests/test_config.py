"""
Tests for configuration validation framework.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from common.config import (
    ConfigIssue,
    ServerConfig,
    ConfigValidationError,
    validate_config_or_raise,
)
from common.errors import ErrorCode


class DummyServerConfig(ServerConfig):
    """Dummy ServerConfig subclass for testing.
    
    Has one required field (API_KEY) and one optional field (OPTIONAL_FIELD).
    """

    def __init__(self, api_key: Optional[str] = None, optional_field: Optional[str] = None):
        """
        Initialize dummy config.
        
        Args:
            api_key: Required API key (can be None to simulate missing env var)
            optional_field: Optional field (can be None)
        """
        self.api_key = api_key
        self.optional_field = optional_field

    def validate(self) -> List[ConfigIssue]:
        """Validate configuration and return issues."""
        issues = []

        # API_KEY is required
        if not self.api_key:
            issues.append(
                ConfigIssue(
                    field="API_KEY",
                    message="API key is required but not provided",
                    critical=True,
                )
            )

        # OPTIONAL_FIELD is optional, but if provided should not be empty
        if self.optional_field is not None and not self.optional_field.strip():
            issues.append(
                ConfigIssue(
                    field="OPTIONAL_FIELD",
                    message="Optional field cannot be empty if provided",
                    critical=False,
                )
            )

        return issues


class TestConfigIssue:
    """Test ConfigIssue dataclass."""

    def test_config_issue_creation(self):
        """Test creating a ConfigIssue."""
        issue = ConfigIssue(
            field="API_KEY",
            message="API key is missing",
            critical=True,
        )

        assert issue.field == "API_KEY"
        assert issue.message == "API key is missing"
        assert issue.critical is True

    def test_config_issue_default_critical(self):
        """Test that critical defaults to True."""
        issue = ConfigIssue(field="FIELD", message="Message")

        assert issue.critical is True


class TestServerConfig:
    """Test ServerConfig base class."""

    def test_validate_default_returns_empty(self):
        """Test that default validate() returns empty list."""
        config = ServerConfig()
        issues = config.validate()

        assert issues == []
        assert config.is_valid() is True

    def test_is_valid_with_no_issues(self):
        """Test is_valid() returns True when no issues."""
        config = DummyServerConfig(api_key="test-key")
        assert config.is_valid() is True

    def test_is_valid_with_critical_issue(self):
        """Test is_valid() returns False when critical issue exists."""
        config = DummyServerConfig(api_key=None)
        assert config.is_valid() is False

    def test_is_valid_with_non_critical_issue(self):
        """Test is_valid() returns True when only non-critical issues exist."""
        config = DummyServerConfig(api_key="test-key", optional_field="")
        # Should still be valid because only non-critical issue
        assert config.is_valid() is True


class TestConfigValidationError:
    """Test ConfigValidationError exception."""

    def test_error_creation(self):
        """Test creating a ConfigValidationError."""
        issues = [
            ConfigIssue(field="API_KEY", message="Missing API key", critical=True),
            ConfigIssue(field="BASE_URL", message="Invalid URL", critical=False),
        ]
        error = ConfigValidationError(issues)

        assert error.issues == issues
        assert len(error.issues) == 2

    def test_error_message_formatting(self):
        """Test error message formatting."""
        issues = [
            ConfigIssue(field="API_KEY", message="Missing API key", critical=True),
            ConfigIssue(field="BASE_URL", message="Invalid URL", critical=False),
        ]
        error = ConfigValidationError(issues)
        message = str(error)

        assert "Configuration validation failed" in message
        assert "API_KEY" in message
        assert "Missing API key" in message
        assert "BASE_URL" in message
        assert "Invalid URL" in message
        assert "Critical issues" in message
        assert "Non-critical issues" in message

    def test_error_message_only_critical(self):
        """Test error message with only critical issues."""
        issues = [
            ConfigIssue(field="API_KEY", message="Missing API key", critical=True),
        ]
        error = ConfigValidationError(issues)
        message = str(error)

        assert "Critical issues" in message
        assert "Non-critical issues" not in message

    def test_error_message_empty_issues(self):
        """Test error message with empty issues list."""
        error = ConfigValidationError([])
        message = str(error)

        assert "Configuration validation failed" in message


class TestValidateConfigOrRaise:
    """Test validate_config_or_raise function."""

    def test_valid_config_fail_fast(self):
        """Test valid config with fail_fast=True returns (True, None)."""
        config = DummyServerConfig(api_key="test-key")
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=True)

        assert is_valid is True
        assert error_payload is None

    def test_valid_config_fail_soft(self):
        """Test valid config with fail_fast=False returns (True, None)."""
        config = DummyServerConfig(api_key="test-key")
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=False)

        assert is_valid is True
        assert error_payload is None

    def test_invalid_config_fail_fast_raises(self):
        """Test invalid config with fail_fast=True raises ConfigValidationError."""
        config = DummyServerConfig(api_key=None)

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config_or_raise(config, fail_fast=True)

        error = exc_info.value
        assert len(error.issues) > 0
        assert any(issue.field == "API_KEY" for issue in error.issues)

    def test_invalid_config_fail_soft_returns_error(self):
        """Test invalid config with fail_fast=False returns (False, error_payload)."""
        config = DummyServerConfig(api_key=None)
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=False)

        assert is_valid is False
        assert error_payload is not None
        assert error_payload["error_code"] == ErrorCode.SERVICE_NOT_CONFIGURED.value
        assert error_payload["message"] == "Service configuration is incomplete or invalid."
        assert "issues" in error_payload
        assert len(error_payload["issues"]) > 0

        # Check issue structure
        issue = error_payload["issues"][0]
        assert "field" in issue
        assert "message" in issue
        assert "critical" in issue
        assert issue["field"] == "API_KEY"
        assert issue["critical"] is True

    def test_fail_soft_includes_all_issues(self):
        """Test fail_soft includes both critical and non-critical issues."""
        config = DummyServerConfig(api_key=None, optional_field="")
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=False)

        assert is_valid is False
        assert error_payload is not None
        assert len(error_payload["issues"]) == 2

        # Find critical and non-critical issues
        critical_issues = [i for i in error_payload["issues"] if i["critical"]]
        non_critical_issues = [i for i in error_payload["issues"] if not i["critical"]]

        assert len(critical_issues) == 1
        assert len(non_critical_issues) == 1
        assert critical_issues[0]["field"] == "API_KEY"
        assert non_critical_issues[0]["field"] == "OPTIONAL_FIELD"

    def test_fail_soft_only_critical_issues_make_invalid(self):
        """Test that only critical issues cause is_valid=False."""
        # Config with only non-critical issue should still be valid
        config = DummyServerConfig(api_key="test-key", optional_field="")
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=False)

        assert is_valid is True
        assert error_payload is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
