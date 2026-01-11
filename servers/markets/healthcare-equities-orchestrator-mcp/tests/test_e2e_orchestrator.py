"""
E2E tests for healthcare-equities-orchestrator-mcp.

Tests the analyze_company_across_markets_and_clinical tool end-to-end,
including partial failure scenarios.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import HealthcareEquitiesOrchestratorConfig
from src.clients.mcp_orchestrator_client import MCPOrchestratorClient
from src.tools.analyze_company_tool import analyze_company_across_markets_and_clinical


pytestmark = [pytest.mark.e2e, pytest.mark.python]


class TestE2EAnalyzeCompanyAcrossMarketsAndClinical:
    """E2E tests for analyze_company_across_markets_and_clinical."""
    
    @pytest.mark.asyncio
    async def test_e2e_with_well_known_ticker(self):
        """E2E test with a well-known public ticker (mocked upstreams)."""
        # Mock well-known biotech company data
        mock_biotech_markets_data = {
            "company_name": "Moderna Inc",
            "normalized_name": "moderna inc",
            "pipeline": [
                {
                    "drug_name": "mRNA-1273",
                    "latest_phase": "Approved",
                    "indication": "COVID-19",
                    "therapeutic_area": "Infectious Disease"
                },
                {
                    "drug_name": "mRNA-1647",
                    "latest_phase": "Phase 3",
                    "indication": "CMV",
                    "therapeutic_area": "Infectious Disease"
                }
            ],
            "financial_summary": {
                "market_cap": 100000000000,  # $100B
                "revenue": 20000000000,  # $20B
                "cash_on_hand": 5000000000,  # $5B
                "has_ipo": True,
                "exchange": "NASDAQ",
                "ipo_date": "2018-12-07"
            },
            "trials_summary": {
                "total_trials": 25,
                "active_trials": 8,
                "completed_trials": 17,
                "phase_distribution": {
                    "Phase 1": 5,
                    "Phase 2": 7,
                    "Phase 3": 10,
                    "Approved": 3
                }
            },
            "risk_flags": []
        }
        
        mock_sec_data = {
            "company_name": "Moderna Inc",
            "cik": "0001682852",
            "filing_count": 150,
            "latest_filing_date": "2024-01-15",
            "filings": [
                {
                    "filing_type": "10-K",
                    "filing_date": "2024-01-15",
                    "accession_number": "0001682852-24-000001"
                }
            ]
        }
        
        mock_clinical_data = {
            "company_name": "Moderna Inc",
            "total_trials": 25,
            "active_trials": 8,
            "trials": [
                {
                    "nct_id": "NCT12345678",
                    "title": "Test Trial",
                    "status": "Recruiting",
                    "phase": "Phase 3"
                }
            ]
        }
        
        # Create config and client
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            # Setup mocks
            mock_get_markets.return_value = mock_biotech_markets_data
            mock_get_sec.return_value = mock_sec_data
            mock_get_clinical.return_value = mock_clinical_data
            mock_cache.get.return_value = None  # No cache hit
            mock_cache.set = Mock()  # Mock cache set
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            # Call the tool
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"ticker": "MRNA"},
                include_financials=True,
                include_clinical=True,
                include_sec=True
            )
            
            # Verify structure
            assert "identifier" in result
            assert result["identifier"]["ticker"] == "MRNA"
            assert "financials" in result
            assert "clinical" in result
            assert "sec" in result
            assert "risk_flags" in result
            assert "summary" in result
            
            # Verify financials data
            assert result["financials"] is not None
            assert result["financials"]["company_name"] == "Moderna Inc"
            assert len(result["financials"]["pipeline"]) == 2
            assert result["financials"]["financial_summary"]["market_cap"] == 100000000000
            
            # Verify SEC data
            assert result["sec"] is not None
            assert result["sec"]["cik"] == "0001682852"
            
            # Verify clinical data
            assert result["clinical"] is not None
            assert result["clinical"]["total_trials"] == 25
            
            # Verify summary
            summary = result["summary"]
            assert summary["has_financials"] is True
            assert summary["has_clinical"] is True
            assert summary["has_sec"] is True
            assert summary["pipeline_drugs"] == 2
            assert summary["total_trials"] == 25
    
    @pytest.mark.asyncio
    async def test_e2e_partial_failure_biotech_markets_down(self):
        """E2E test when biotech-markets-mcp is unavailable (partial failure)."""
        mock_sec_data = {
            "company_name": "Moderna Inc",
            "cik": "0001682852",
            "filing_count": 150
        }
        
        mock_clinical_data = {
            "company_name": "Moderna Inc",
            "total_trials": 25
        }
        
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            # Biotech markets fails
            mock_get_markets.side_effect = Exception("biotech-markets-mcp unavailable")
            mock_get_sec.return_value = mock_sec_data
            mock_get_clinical.return_value = mock_clinical_data
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            # Call the tool
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"ticker": "MRNA"},
                include_financials=True,
                include_clinical=True,
                include_sec=True
            )
            
            # Should still return partial results
            assert "identifier" in result
            assert result["identifier"]["ticker"] == "MRNA"
            # Financials should be None (failed)
            assert result["financials"] is None
            # But SEC and clinical should still be present
            assert result["sec"] is not None
            assert result["clinical"] is not None
            
            # Summary should reflect partial failure
            summary = result["summary"]
            assert summary["has_financials"] is False
            assert summary["has_clinical"] is True
            assert summary["has_sec"] is True
    
    @pytest.mark.asyncio
    async def test_e2e_partial_failure_clinical_trials_down(self):
        """E2E test when clinical-trials-mcp is unavailable (partial failure)."""
        mock_biotech_markets_data = {
            "company_name": "Moderna Inc",
            "normalized_name": "moderna inc",
            "pipeline": [{"drug_name": "mRNA-1273", "latest_phase": "Approved"}],
            "financial_summary": {"market_cap": 100000000000, "has_ipo": True},
            "trials_summary": {"total_trials": 25},
            "risk_flags": []
        }
        
        mock_sec_data = {
            "company_name": "Moderna Inc",
            "cik": "0001682852"
        }
        
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            mock_get_markets.return_value = mock_biotech_markets_data
            mock_get_sec.return_value = mock_sec_data
            # Clinical trials fails
            mock_get_clinical.side_effect = Exception("clinical-trials-mcp unavailable")
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            # Call the tool
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"ticker": "MRNA"},
                include_financials=True,
                include_clinical=True,
                include_sec=True
            )
            
            # Should still return partial results
            assert "identifier" in result
            assert result["financials"] is not None
            assert result["sec"] is not None
            # Clinical should be None (failed)
            assert result["clinical"] is None
            
            # Summary should reflect partial failure
            summary = result["summary"]
            assert summary["has_financials"] is True
            assert summary["has_clinical"] is False
            assert summary["has_sec"] is True
    
    @pytest.mark.asyncio
    async def test_e2e_with_company_name(self):
        """E2E test with company_name identifier."""
        mock_biotech_markets_data = {
            "company_name": "Pfizer Inc",
            "normalized_name": "pfizer inc",
            "pipeline": [{"drug_name": "Drug A", "latest_phase": "Phase 3"}],
            "financial_summary": {"market_cap": 200000000000, "has_ipo": True},
            "trials_summary": {"total_trials": 50},
            "risk_flags": []
        }
        
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            mock_get_markets.return_value = mock_biotech_markets_data
            mock_get_sec.return_value = None
            mock_get_clinical.return_value = None
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"company_name": "Pfizer"},
                include_financials=True,
                include_clinical=False,
                include_sec=False
            )
            
            assert "identifier" in result
            assert result["identifier"]["company_name"] == "Pfizer"
            assert result["financials"] is not None
            assert result["financials"]["company_name"] == "Pfizer Inc"
    
    @pytest.mark.asyncio
    async def test_e2e_with_cik(self):
        """E2E test with CIK identifier."""
        mock_biotech_markets_data = {
            "company_name": "Gilead Sciences Inc",
            "normalized_name": "gilead sciences inc",
            "pipeline": [],
            "financial_summary": {"has_ipo": True},
            "trials_summary": {},
            "risk_flags": []
        }
        
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            mock_get_markets.return_value = mock_biotech_markets_data
            mock_get_sec.return_value = None
            mock_get_clinical.return_value = None
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"cik": "0000882093"},
                include_financials=True,
                include_clinical=False,
                include_sec=False
            )
            
            assert "identifier" in result
            assert result["identifier"]["cik"] == "0000882093"
            assert result["financials"] is not None
    
    @pytest.mark.asyncio
    async def test_e2e_validates_output_structure(self):
        """E2E test that validates the complete output structure."""
        mock_biotech_markets_data = {
            "company_name": "BioNTech SE",
            "normalized_name": "biontech se",
            "pipeline": [
                {"drug_name": "BNT162b2", "latest_phase": "Approved"}
            ],
            "financial_summary": {
                "market_cap": 50000000000,
                "revenue": 10000000000,
                "has_ipo": True,
                "exchange": "NASDAQ"
            },
            "trials_summary": {
                "total_trials": 15,
                "active_trials": 5,
                "completed_trials": 10
            },
            "risk_flags": []
        }
        
        config = HealthcareEquitiesOrchestratorConfig()
        
        with patch.object(MCPOrchestratorClient, '_get_biotech_markets_data') as mock_get_markets, \
             patch.object(MCPOrchestratorClient, '_get_sec_data') as mock_get_sec, \
             patch.object(MCPOrchestratorClient, '_get_clinical_trials_data') as mock_get_clinical, \
             patch.object(MCPOrchestratorClient, '_cache') as mock_cache:
            
            mock_get_markets.return_value = mock_biotech_markets_data
            mock_get_sec.return_value = {"company_name": "BioNTech SE", "cik": "0001779115"}
            mock_get_clinical.return_value = {"company_name": "BioNTech SE", "total_trials": 15}
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            client = MCPOrchestratorClient(config, cache_ttl_seconds=300)
            
            result = analyze_company_across_markets_and_clinical(
                client=client,
                config_error_payload=None,
                identifier={"ticker": "BNTX"},
                include_financials=True,
                include_clinical=True,
                include_sec=True
            )
            
            # Validate complete structure
            required_top_level = ["identifier", "financials", "clinical", "sec", "risk_flags", "summary"]
            for key in required_top_level:
                assert key in result, f"Missing required key: {key}"
            
            # Validate identifier structure
            assert "ticker" in result["identifier"] or "company_name" in result["identifier"] or "cik" in result["identifier"]
            
            # Validate summary structure
            summary = result["summary"]
            required_summary_keys = ["has_financials", "has_clinical", "has_sec", "pipeline_drugs", "total_trials", "risk_flag_count"]
            for key in required_summary_keys:
                assert key in summary, f"Missing required summary key: {key}"
            
            # Validate risk_flags is a list
            assert isinstance(result["risk_flags"], list)
