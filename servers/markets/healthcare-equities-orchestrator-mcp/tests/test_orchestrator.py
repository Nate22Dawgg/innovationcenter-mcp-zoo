"""
Tests for the Healthcare Equities Orchestrator MCP server.

These tests verify the orchestrator's ability to coordinate calls to
multiple upstream MCP servers and aggregate results.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import HealthcareEquitiesOrchestratorConfig
from src.clients.mcp_orchestrator_client import MCPOrchestratorClient
from src.tools.analyze_company_tool import analyze_company_across_markets_and_clinical


class TestOrchestratorClient:
    """Tests for MCPOrchestratorClient."""
    
    def test_client_initialization(self):
        """Test that client initializes correctly."""
        config = HealthcareEquitiesOrchestratorConfig()
        client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
        
        assert client.config == config
        assert client.cache_ttl_seconds == 300
        assert client._cache is not None
    
    @patch('src.clients.mcp_orchestrator_client.get_profile')
    def test_analyze_company_with_mock_data(self, mock_get_profile):
        """Test analyze_company with mocked upstream data."""
        # Mock biotech markets data
        mock_profile = {
            "company_name": "Moderna",
            "normalized_name": "moderna",
            "pipeline": [
                {
                    "drug_name": "mRNA-1273",
                    "phases": ["Phase 3", "Approved"],
                    "latest_phase": "Approved",
                    "trial_count": 5,
                    "indication": "COVID-19",
                    "therapeutic_area": "Infectious Disease"
                }
            ],
            "financial_summary": {
                "market_cap": 100000000000,
                "revenue": 20000000000,
                "cash_on_hand": 5000000000,
                "has_ipo": True,
                "exchange": "NASDAQ"
            },
            "trials_summary": {
                "total_trials": 10,
                "active_trials": 3,
                "completed_trials": 7
            },
            "risk_flags": ["High valuation", "Concentration risk"]
        }
        mock_get_profile.return_value = mock_profile
        
        config = HealthcareEquitiesOrchestratorConfig()
        client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
        
        identifier = {"company_name": "Moderna"}
        result = client.analyze_company(
            identifier=identifier,
            include_financials=True,
            include_clinical=True,
            include_sec=True
        )
        
        assert result["identifier"] == identifier
        assert result["financials"] is not None
        assert result["financials"]["company_name"] == "Moderna"
        assert len(result["financials"]["pipeline"]) == 1
        assert result["summary"]["has_financials"] is True
        assert result["summary"]["pipeline_drugs"] == 1
        assert len(result["risk_flags"]) >= 0


class TestAnalyzeCompanyTool:
    """Tests for analyze_company_across_markets_and_clinical tool."""
    
    def test_tool_with_missing_identifier(self):
        """Test tool with missing identifier."""
        result = analyze_company_across_markets_and_clinical(
            client=None,
            config_error_payload=None,
            identifier=None
        )
        
        assert "error" in result
        assert result["error"]["code"] == "BAD_REQUEST"
    
    def test_tool_with_empty_identifier(self):
        """Test tool with empty identifier."""
        result = analyze_company_across_markets_and_clinical(
            client=None,
            config_error_payload=None,
            identifier={}
        )
        
        assert "error" in result
        assert result["error"]["code"] == "BAD_REQUEST"
    
    def test_tool_with_config_error(self):
        """Test tool with configuration error (fail-soft behavior)."""
        config_error = {
            "error_code": "SERVICE_NOT_CONFIGURED",
            "message": "Service configuration is incomplete or invalid.",
            "issues": []
        }
        
        result = analyze_company_across_markets_and_clinical(
            client=None,
            config_error_payload=config_error,
            identifier={"company_name": "Moderna"}
        )
        
        assert result == config_error
    
    @patch('src.tools.analyze_company_tool.MCPOrchestratorClient')
    def test_tool_with_valid_client(self, mock_client_class):
        """Test tool with valid client."""
        # Mock client and its analyze_company method
        mock_client = MagicMock()
        mock_result = {
            "identifier": {"company_name": "Moderna"},
            "financials": {"company_name": "Moderna"},
            "clinical": {"total_trials": 10},
            "sec": None,
            "risk_flags": [],
            "summary": {
                "has_financials": True,
                "has_clinical": True,
                "has_sec": False,
                "pipeline_drugs": 1,
                "total_trials": 10,
                "risk_flag_count": 0
            }
        }
        mock_client.analyze_company.return_value = mock_result
        mock_client_class.return_value = mock_client
        
        config = HealthcareEquitiesOrchestratorConfig()
        client = MCPOrchestratorClient(config)
        
        result = analyze_company_across_markets_and_clinical(
            client=client,
            config_error_payload=None,
            identifier={"company_name": "Moderna"}
        )
        
        assert result["identifier"]["company_name"] == "Moderna"
        assert result["summary"]["has_financials"] is True


class TestConfig:
    """Tests for HealthcareEquitiesOrchestratorConfig."""
    
    def test_config_defaults(self):
        """Test config with default values."""
        config = HealthcareEquitiesOrchestratorConfig()
        
        assert config.biotech_markets_mcp_url is None
        assert config.sec_edgar_mcp_url is None
        assert config.clinical_trials_mcp_url is None
        assert config.cache_ttl_seconds == 300
    
    def test_config_validation_valid(self):
        """Test config validation with valid values."""
        config = HealthcareEquitiesOrchestratorConfig(
            biotech_markets_mcp_url="https://example.com",
            cache_ttl_seconds=600
        )
        
        issues = config.validate()
        assert len(issues) == 0
    
    def test_config_validation_invalid_url(self):
        """Test config validation with invalid URL."""
        config = HealthcareEquitiesOrchestratorConfig(
            biotech_markets_mcp_url="not-a-url"
        )
        
        issues = config.validate()
        assert len(issues) > 0
        assert any(issue.field == "biotech_markets_mcp_url" for issue in issues)
    
    def test_config_validation_negative_ttl(self):
        """Test config validation with negative TTL."""
        config = HealthcareEquitiesOrchestratorConfig(
            cache_ttl_seconds=-1
        )
        
        issues = config.validate()
        assert len(issues) > 0
        assert any(issue.field == "cache_ttl_seconds" for issue in issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
