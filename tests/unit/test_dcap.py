"""
Unit tests for DCAP v3.1 integration module.

Tests the common/dcap.py module for:
- Message format compliance with DCAP v3.1 specification
- Sensitive data sanitization
- Configuration handling
- UDP sending (mocked)
- Fail-silent behavior

Reference: https://github.com/boorich/dcap
"""

import json
import os
import socket
import time
import unittest
from unittest.mock import MagicMock, patch, call
from dataclasses import asdict

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import DCAP module directly to avoid dependency issues
# We'll mock the socket operations
import importlib.util
dcap_spec = importlib.util.spec_from_file_location(
    "dcap", 
    Path(__file__).parent.parent.parent / "common" / "dcap.py"
)
dcap = importlib.util.module_from_spec(dcap_spec)
dcap_spec.loader.exec_module(dcap)


class TestDCAPConfig(unittest.TestCase):
    """Tests for DCAP configuration handling."""

    def test_default_config(self):
        """Test default configuration values."""
        config = dcap.DCAPConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.relay_host, "159.89.110.236")
        self.assertEqual(config.relay_port, 10191)
        self.assertIsNone(config.server_id_override)

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            "DCAP_ENABLED": "false",
            "DCAP_RELAY_HOST": "localhost",
            "DCAP_RELAY_PORT": "9999",
            "DCAP_SERVER_ID": "test-server"
        }):
            # Reset the cached config
            dcap._config = None
            config = dcap.get_config()
            
            self.assertFalse(config.enabled)
            self.assertEqual(config.relay_host, "localhost")
            self.assertEqual(config.relay_port, 9999)
            self.assertEqual(config.server_id_override, "test-server")
            
            # Reset for other tests
            dcap._config = None

    def test_dcap_enabled_variations(self):
        """Test various DCAP_ENABLED values."""
        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        false_values = ["false", "FALSE", "0", "no", "off", "anything"]
        
        for val in true_values:
            with patch.dict(os.environ, {"DCAP_ENABLED": val}):
                dcap._config = None
                config = dcap.get_config()
                self.assertTrue(config.enabled, f"Expected True for DCAP_ENABLED={val}")
                dcap._config = None
        
        for val in false_values:
            with patch.dict(os.environ, {"DCAP_ENABLED": val}):
                dcap._config = None
                config = dcap.get_config()
                self.assertFalse(config.enabled, f"Expected False for DCAP_ENABLED={val}")
                dcap._config = None


class TestToolSignature(unittest.TestCase):
    """Tests for ToolSignature dataclass."""

    def test_basic_signature(self):
        """Test basic signature creation."""
        sig = dcap.ToolSignature(
            input="Text",
            output="Maybe<JSON>",
            cost=5
        )
        self.assertEqual(sig.input, "Text")
        self.assertEqual(sig.output, "Maybe<JSON>")
        self.assertEqual(sig.cost, 5)

    def test_signature_to_dict(self):
        """Test signature serialization."""
        sig = dcap.ToolSignature(
            input="SearchQuery",
            output="Maybe<TrialList>",
            cost=0
        )
        d = asdict(sig)
        self.assertEqual(d, {
            "input": "SearchQuery",
            "output": "Maybe<TrialList>",
            "cost": 0
        })

    def test_default_cost(self):
        """Test default cost is 0."""
        sig = dcap.ToolSignature(input="Text", output="Text")
        self.assertEqual(sig.cost, 0)


class TestConnector(unittest.TestCase):
    """Tests for Connector dataclass."""

    def test_default_connector(self):
        """Test default connector values."""
        conn = dcap.Connector()
        self.assertEqual(conn.transport, "stdio")
        self.assertEqual(conn.protocol, "mcp")
        self.assertIsNone(conn.command)
        self.assertIsNone(conn.url)

    def test_full_connector(self):
        """Test fully specified connector."""
        conn = dcap.Connector(
            transport="http",
            protocol="rest",
            url="https://api.example.com",
            auth_type="api_key",
            headers={"X-API-Key": "***"}
        )
        self.assertEqual(conn.transport, "http")
        self.assertEqual(conn.url, "https://api.example.com")
        self.assertEqual(conn.auth_type, "api_key")


class TestSanitizeArgs(unittest.TestCase):
    """Tests for argument sanitization."""

    def test_sanitize_password(self):
        """Test password fields are redacted."""
        args = {"username": "user", "password": "secret123"}
        sanitized = dcap._sanitize_args(args)
        self.assertEqual(sanitized["username"], "user")
        self.assertEqual(sanitized["password"], "***REDACTED***")

    def test_sanitize_api_key(self):
        """Test API key fields are redacted."""
        args = {"api_key": "sk-1234567890", "query": "test"}
        sanitized = dcap._sanitize_args(args)
        self.assertEqual(sanitized["api_key"], "***REDACTED***")
        self.assertEqual(sanitized["query"], "test")

    def test_sanitize_various_sensitive_keys(self):
        """Test various sensitive key patterns."""
        sensitive_args = {
            "token": "abc123",
            "secret": "mysecret",
            "authorization": "Bearer xyz",
            "patient_id": "12345",
            "ssn": "123-45-6789",
        }
        sanitized = dcap._sanitize_args(sensitive_args)
        for key in sensitive_args:
            self.assertEqual(sanitized[key], "***REDACTED***", f"Key {key} should be redacted")

    def test_truncate_long_strings(self):
        """Test long strings are truncated."""
        long_string = "x" * 200
        args = {"content": long_string}
        sanitized = dcap._sanitize_args(args)
        self.assertEqual(len(sanitized["content"]), 103)  # 100 + "..."
        self.assertTrue(sanitized["content"].endswith("..."))

    def test_empty_args(self):
        """Test empty args returns empty dict."""
        self.assertEqual(dcap._sanitize_args(None), {})
        self.assertEqual(dcap._sanitize_args({}), {})


class TestSemanticDiscoverMessage(unittest.TestCase):
    """Tests for semantic_discover message format."""

    @patch('socket.socket')
    def test_message_format(self, mock_socket_class):
        """Test semantic_discover message format compliance."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        # Enable DCAP
        with patch.dict(os.environ, {"DCAP_ENABLED": "true"}):
            dcap._config = None
            
            # Call the function
            result = dcap.send_dcap_semantic_discover(
                server_id="test-mcp",
                tool_name="test_tool",
                description="A test tool",
                triggers=["test", "demo"],
                signature=dcap.ToolSignature(input="Text", output="Maybe<JSON>", cost=0),
                connector=dcap.Connector(transport="stdio", protocol="mcp")
            )
            
            # Verify sendto was called
            self.assertTrue(mock_socket.sendto.called)
            
            # Extract and verify the message
            call_args = mock_socket.sendto.call_args
            data = call_args[0][0]
            message = json.loads(data.decode('utf-8'))
            
            # Verify DCAP v3.1 format
            self.assertEqual(message["v"], 3)
            self.assertEqual(message["t"], "semantic_discover")
            self.assertIn("ts", message)
            self.assertEqual(message["sid"], "test-mcp")
            self.assertEqual(message["tool"], "test_tool")
            self.assertEqual(message["does"], "A test tool")
            self.assertEqual(message["when"], ["test", "demo"])
            self.assertEqual(message["signature"]["input"], "Text")
            self.assertEqual(message["signature"]["output"], "Maybe<JSON>")
            self.assertEqual(message["signature"]["cost"], 0)
            self.assertEqual(message["connector"]["transport"], "stdio")
            self.assertEqual(message["connector"]["protocol"], "mcp")
            
            dcap._config = None


class TestPerfUpdateMessage(unittest.TestCase):
    """Tests for perf_update message format."""

    @patch('socket.socket')
    def test_message_format(self, mock_socket_class):
        """Test perf_update message format compliance."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {"DCAP_ENABLED": "true"}):
            dcap._config = None
            
            result = dcap.send_dcap_perf_update(
                server_id="test-mcp",
                tool_name="test_tool",
                exec_ms=250,
                success=True,
                cost_paid=5,
                caller="agent-123",
                args={"query": "test"}
            )
            
            self.assertTrue(mock_socket.sendto.called)
            
            call_args = mock_socket.sendto.call_args
            data = call_args[0][0]
            message = json.loads(data.decode('utf-8'))
            
            # Verify DCAP v3.1 format
            self.assertEqual(message["v"], 3)
            self.assertEqual(message["t"], "perf_update")
            self.assertIn("ts", message)
            self.assertEqual(message["sid"], "test-mcp")
            self.assertEqual(message["tool"], "test_tool")
            self.assertEqual(message["exec_ms"], 250)
            self.assertEqual(message["success"], True)
            self.assertEqual(message["cost_paid"], 5)
            self.assertEqual(message["ctx"]["caller"], "agent-123")
            self.assertEqual(message["ctx"]["args"]["query"], "test")
            
            dcap._config = None

    @patch('socket.socket')
    def test_default_values(self, mock_socket_class):
        """Test perf_update with default values."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {"DCAP_ENABLED": "true"}):
            dcap._config = None
            
            dcap.send_dcap_perf_update(
                server_id="test-mcp",
                tool_name="test_tool",
                exec_ms=100,
                success=False
            )
            
            call_args = mock_socket.sendto.call_args
            data = call_args[0][0]
            message = json.loads(data.decode('utf-8'))
            
            self.assertEqual(message["cost_paid"], 0)
            self.assertEqual(message["ctx"]["caller"], "unknown-agent")
            self.assertEqual(message["ctx"]["args"], {})
            
            dcap._config = None


class TestDCAPDisabled(unittest.TestCase):
    """Tests for when DCAP is disabled."""

    @patch('socket.socket')
    def test_no_udp_when_disabled(self, mock_socket_class):
        """Test no UDP is sent when DCAP is disabled."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {"DCAP_ENABLED": "false"}):
            dcap._config = None
            
            result = dcap.send_dcap_perf_update(
                server_id="test-mcp",
                tool_name="test_tool",
                exec_ms=100,
                success=True
            )
            
            self.assertFalse(result)
            mock_socket.sendto.assert_not_called()
            
            dcap._config = None


class TestFailSilent(unittest.TestCase):
    """Tests for fail-silent behavior."""

    @patch('socket.socket')
    def test_exception_is_swallowed(self, mock_socket_class):
        """Test that socket exceptions don't propagate."""
        mock_socket = MagicMock()
        mock_socket.sendto.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {"DCAP_ENABLED": "true"}):
            dcap._config = None
            
            # Should not raise
            result = dcap.send_dcap_perf_update(
                server_id="test-mcp",
                tool_name="test_tool",
                exec_ms=100,
                success=True
            )
            
            # Function returns False on error
            self.assertFalse(result)
            
            dcap._config = None


class TestRegisterToolsWithDCAP(unittest.TestCase):
    """Tests for bulk tool registration."""

    @patch('socket.socket')
    def test_register_multiple_tools(self, mock_socket_class):
        """Test registering multiple tools."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {"DCAP_ENABLED": "true"}):
            dcap._config = None
            
            tools = [
                dcap.ToolMetadata(
                    name="tool1",
                    description="First tool",
                    triggers=["one"],
                    signature=dcap.ToolSignature(input="A", output="B", cost=0)
                ),
                dcap.ToolMetadata(
                    name="tool2",
                    description="Second tool",
                    triggers=["two"],
                    signature=dcap.ToolSignature(input="C", output="D", cost=1)
                ),
            ]
            
            count = dcap.register_tools_with_dcap("test-mcp", tools)
            
            self.assertEqual(count, 2)
            self.assertEqual(mock_socket.sendto.call_count, 2)
            
            dcap._config = None


class TestServerIdOverride(unittest.TestCase):
    """Tests for server ID override."""

    @patch('socket.socket')
    def test_override_server_id(self, mock_socket_class):
        """Test DCAP_SERVER_ID environment variable overrides server_id."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.dict(os.environ, {
            "DCAP_ENABLED": "true",
            "DCAP_SERVER_ID": "overridden-server"
        }):
            dcap._config = None
            
            dcap.send_dcap_perf_update(
                server_id="original-server",
                tool_name="test_tool",
                exec_ms=100,
                success=True
            )
            
            call_args = mock_socket.sendto.call_args
            data = call_args[0][0]
            message = json.loads(data.decode('utf-8'))
            
            self.assertEqual(message["sid"], "overridden-server")
            
            dcap._config = None


if __name__ == "__main__":
    unittest.main()
