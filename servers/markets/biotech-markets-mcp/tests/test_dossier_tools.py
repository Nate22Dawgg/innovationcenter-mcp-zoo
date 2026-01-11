"""
Tests for biotech company dossier macro tools.

Tests for:
- generate_biotech_company_dossier
- refine_biotech_dossier
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dossier_generator import generate_biotech_company_dossier
from dossier_refiner import refine_biotech_dossier
from artifact_store import get_artifact_store


pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestGenerateBiotechCompanyDossier:
    """Tests for generate_biotech_company_dossier."""
    
    @pytest.mark.asyncio
    async def test_minimal_valid_input_with_company_name(self):
        """Test that minimal valid input (company_name) produces a structured dossier."""
        # Mock all upstream dependencies
        with patch('dossier_generator.get_profile') as mock_profile, \
             patch('dossier_generator.get_pipeline_drugs') as mock_pipeline, \
             patch('dossier_generator.get_company_trials') as mock_trials, \
             patch('dossier_generator.search_company_cik') as mock_cik, \
             patch('dossier_generator.search_company_filings') as mock_filings, \
             patch('dossier_generator.get_ipo_filings') as mock_ipo, \
             patch('dossier_generator.get_investors_from_filings') as mock_investors, \
             patch('dossier_generator.search_company_publications') as mock_pubmed, \
             patch('dossier_generator._cache') as mock_cache:
            
            # Setup mocks
            mock_profile.return_value = {
                "company_name": "Test Biotech Inc",
                "normalized_name": "test biotech inc"
            }
            mock_pipeline.return_value = []
            mock_trials.return_value = []
            mock_cik.return_value = None
            mock_filings.return_value = []
            mock_ipo.return_value = []
            mock_investors.return_value = []
            mock_pubmed.return_value = []
            mock_cache.get.return_value = None  # No cache hit
            mock_cache.set = Mock()  # Mock cache set
            
            # Call function
            result = await generate_biotech_company_dossier(
                company_identifier={"company_name": "Test Biotech Inc"},
                include_publications=False,
                include_trials=False,
                include_financials=False
            )
            
            # Verify structure
            assert "company_name" in result
            assert result["company_name"] == "Test Biotech Inc"
            assert "identifiers" in result
            assert "pipeline" in result
            assert "financial_summary" in result
            assert "risk_flags" in result
            assert "publications" in result
            assert "trials_summary" in result
            assert "investors" in result
            assert "metadata" in result
            assert "generated_at" in result["metadata"]
            assert "data_sources" in result["metadata"]
            assert "data_quality" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_minimal_valid_input_with_ticker(self):
        """Test that ticker identifier works."""
        with patch('dossier_generator.get_profile') as mock_profile, \
             patch('dossier_generator.get_pipeline_drugs') as mock_pipeline, \
             patch('dossier_generator.get_company_trials') as mock_trials, \
             patch('dossier_generator.search_company_cik') as mock_cik, \
             patch('dossier_generator.search_company_filings') as mock_filings, \
             patch('dossier_generator.get_ipo_filings') as mock_ipo, \
             patch('dossier_generator.get_investors_from_filings') as mock_investors, \
             patch('dossier_generator.search_company_publications') as mock_pubmed, \
             patch('dossier_generator._cache') as mock_cache:
            
            mock_profile.return_value = {"company_name": "MRNA", "normalized_name": "mrna"}
            mock_pipeline.return_value = []
            mock_trials.return_value = []
            mock_cik.return_value = None
            mock_filings.return_value = []
            mock_ipo.return_value = []
            mock_investors.return_value = []
            mock_pubmed.return_value = []
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            result = await generate_biotech_company_dossier(
                company_identifier={"ticker": "MRNA"},
                include_publications=False,
                include_trials=False,
                include_financials=False
            )
            
            assert result["company_name"] == "MRNA"
            assert result["identifiers"]["ticker"] == "MRNA"
    
    @pytest.mark.asyncio
    async def test_missing_all_identifiers(self):
        """Test that missing all identifiers raises an error."""
        with patch('dossier_generator._cache') as mock_cache:
            mock_cache.get.return_value = None
            
            with pytest.raises(Exception) as exc_info:
                await generate_biotech_company_dossier(
                    company_identifier={},
                    include_publications=False,
                    include_trials=False,
                    include_financials=False
                )
            
            # Should raise BAD_REQUEST error
            assert "ticker" in str(exc_info.value).lower() or "company_name" in str(exc_info.value).lower() or "cik" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_upstream_pubmed_failure(self):
        """Test behavior when PubMed API fails."""
        with patch('dossier_generator.get_profile') as mock_profile, \
             patch('dossier_generator.get_pipeline_drugs') as mock_pipeline, \
             patch('dossier_generator.get_company_trials') as mock_trials, \
             patch('dossier_generator.search_company_cik') as mock_cik, \
             patch('dossier_generator.search_company_filings') as mock_filings, \
             patch('dossier_generator.get_ipo_filings') as mock_ipo, \
             patch('dossier_generator.get_investors_from_filings') as mock_investors, \
             patch('dossier_generator.search_company_publications') as mock_pubmed, \
             patch('dossier_generator._cache') as mock_cache:
            
            mock_profile.return_value = {"company_name": "Test Co", "normalized_name": "test co"}
            mock_pipeline.return_value = []
            mock_trials.return_value = []
            mock_cik.return_value = None
            mock_filings.return_value = []
            mock_ipo.return_value = []
            mock_investors.return_value = []
            mock_pubmed.side_effect = Exception("PubMed API unavailable")
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            # Should not raise, but should record error in metadata
            result = await generate_biotech_company_dossier(
                company_identifier={"company_name": "Test Co"},
                include_publications=True,
                include_trials=False,
                include_financials=False
            )
            
            assert result["publications"] == []
            assert "pubmed" in result["metadata"]["data_quality"]
            assert "error" in result["metadata"]["data_quality"]["pubmed"].lower()
    
    @pytest.mark.asyncio
    async def test_upstream_clinical_trials_failure(self):
        """Test behavior when ClinicalTrials.gov API fails."""
        with patch('dossier_generator.get_profile') as mock_profile, \
             patch('dossier_generator.get_pipeline_drugs') as mock_pipeline, \
             patch('dossier_generator.get_company_trials') as mock_trials, \
             patch('dossier_generator.search_company_cik') as mock_cik, \
             patch('dossier_generator.search_company_filings') as mock_filings, \
             patch('dossier_generator.get_ipo_filings') as mock_ipo, \
             patch('dossier_generator.get_investors_from_filings') as mock_investors, \
             patch('dossier_generator.search_company_publications') as mock_pubmed, \
             patch('dossier_generator._cache') as mock_cache:
            
            mock_profile.return_value = {"company_name": "Test Co", "normalized_name": "test co"}
            mock_pipeline.side_effect = Exception("ClinicalTrials.gov API unavailable")
            mock_trials.return_value = []
            mock_cik.return_value = None
            mock_filings.return_value = []
            mock_ipo.return_value = []
            mock_investors.return_value = []
            mock_pubmed.return_value = []
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            result = await generate_biotech_company_dossier(
                company_identifier={"company_name": "Test Co"},
                include_publications=False,
                include_trials=True,
                include_financials=False
            )
            
            assert result["pipeline"] == []
            assert "clinical_trials" in result["metadata"]["data_quality"]
            assert "error" in result["metadata"]["data_quality"]["clinical_trials"].lower()
    
    @pytest.mark.asyncio
    async def test_with_pipeline_data(self):
        """Test dossier generation with pipeline data."""
        with patch('dossier_generator.get_profile') as mock_profile, \
             patch('dossier_generator.get_pipeline_drugs') as mock_pipeline, \
             patch('dossier_generator.get_company_trials') as mock_trials, \
             patch('dossier_generator.search_company_cik') as mock_cik, \
             patch('dossier_generator.search_company_filings') as mock_filings, \
             patch('dossier_generator.get_ipo_filings') as mock_ipo, \
             patch('dossier_generator.get_investors_from_filings') as mock_investors, \
             patch('dossier_generator.search_company_publications') as mock_pubmed, \
             patch('dossier_generator._cache') as mock_cache:
            
            mock_profile.return_value = {"company_name": "Test Co", "normalized_name": "test co"}
            mock_pipeline.return_value = [
                {
                    "drug_name": "Test Drug",
                    "latest_phase": "Phase 3",
                    "indication": "Test Indication"
                }
            ]
            mock_trials.return_value = []
            mock_cik.return_value = None
            mock_filings.return_value = []
            mock_ipo.return_value = []
            mock_investors.return_value = []
            mock_pubmed.return_value = []
            mock_cache.get.return_value = None
            mock_cache.set = Mock()
            
            result = await generate_biotech_company_dossier(
                company_identifier={"company_name": "Test Co"},
                include_publications=False,
                include_trials=False,
                include_financials=False
            )
            
            assert len(result["pipeline"]) == 1
            assert result["pipeline"][0]["drug_name"] == "Test Drug"
            # Should not flag "No active pipeline drugs"
            assert "No active pipeline drugs" not in result["risk_flags"]


class TestRefineBiotechDossier:
    """Tests for refine_biotech_dossier."""
    
    @pytest.mark.asyncio
    async def test_refine_with_dossier_object(self):
        """Test refining a dossier provided as object."""
        test_dossier = {
            "company_name": "Test Biotech Inc",
            "normalized_name": "test biotech inc",
            "pipeline": [
                {"drug_name": "Drug A", "latest_phase": "Phase 3"},
                {"drug_name": "Drug B", "latest_phase": "Phase 1"}
            ],
            "financial_summary": {
                "has_ipo": True,
                "market_cap": 1000000000,
                "exchange": "NASDAQ"
            },
            "risk_flags": [],
            "trials_summary": {
                "total_trials": 5,
                "active_trials": 3,
                "completed_trials": 2
            },
            "publications": [],
            "investors": [],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = await refine_biotech_dossier(
            dossier=test_dossier,
            focus_areas=["pipeline", "financials"]
        )
        
        assert "refined_dossier" in result
        assert "summary" in result
        assert "key_insights" in result
        assert "focus_areas_covered" in result
        assert result["refined_dossier"]["company_name"] == "Test Biotech Inc"
        assert "pipeline" in result["focus_areas_covered"]
        assert "financials" in result["focus_areas_covered"]
        assert len(result["key_insights"]) > 0
    
    @pytest.mark.asyncio
    async def test_refine_with_dossier_id(self):
        """Test refining a dossier using dossier_id from artifact store."""
        # Create a test dossier and store it
        artifact_store = get_artifact_store()
        test_dossier = {
            "company_name": "Test Biotech Inc",
            "normalized_name": "test biotech inc",
            "pipeline": [],
            "financial_summary": {},
            "risk_flags": [],
            "trials_summary": {},
            "publications": [],
            "investors": [],
            "metadata": {}
        }
        
        dossier_id = artifact_store.store(test_dossier)
        
        try:
            result = await refine_biotech_dossier(
                dossier_id=dossier_id,
                focus_areas=["risks"]
            )
            
            assert "refined_dossier" in result
            assert result["metadata"]["used_cached_dossier"] is True
            assert "risks" in result["focus_areas_covered"]
        finally:
            # Cleanup
            artifact_store.delete(dossier_id)
    
    @pytest.mark.asyncio
    async def test_refine_with_question(self):
        """Test refining a dossier with a question."""
        test_dossier = {
            "company_name": "Test Biotech Inc",
            "normalized_name": "test biotech inc",
            "pipeline": [
                {"drug_name": "Drug A", "latest_phase": "Phase 3"}
            ],
            "financial_summary": {
                "has_ipo": True,
                "market_cap": 1000000000
            },
            "risk_flags": ["High valuation"],
            "trials_summary": {},
            "publications": [],
            "investors": [],
            "metadata": {}
        }
        
        result = await refine_biotech_dossier(
            dossier=test_dossier,
            new_question="What are the main risks?"
        )
        
        assert "refined_dossier" in result
        assert "summary" in result
        assert "question_answered" in result["focus_areas_covered"]
        assert result["metadata"]["question"] == "What are the main risks?"
        # Should include risk insights
        assert any("risk" in insight.lower() for insight in result["key_insights"])
    
    @pytest.mark.asyncio
    async def test_refine_with_invalid_dossier_id(self):
        """Test refining with non-existent dossier_id raises error."""
        with pytest.raises(Exception) as exc_info:
            await refine_biotech_dossier(
                dossier_id="non-existent-id-12345"
            )
        
        # Should raise NOT_FOUND error
        assert "not found" in str(exc_info.value).lower() or "NOT_FOUND" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_refine_with_no_dossier_or_id(self):
        """Test that providing neither dossier nor dossier_id raises error."""
        with pytest.raises(Exception) as exc_info:
            await refine_biotech_dossier()
        
        # Should raise BAD_REQUEST error
        assert "dossier" in str(exc_info.value).lower() or "dossier_id" in str(exc_info.value).lower() or "BAD_REQUEST" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_refine_all_focus_areas(self):
        """Test refining with all focus areas."""
        test_dossier = {
            "company_name": "Test Biotech Inc",
            "normalized_name": "test biotech inc",
            "pipeline": [{"drug_name": "Drug A", "latest_phase": "Phase 2"}],
            "financial_summary": {"has_ipo": True, "market_cap": 500000000},
            "risk_flags": [],
            "trials_summary": {"total_trials": 3, "active_trials": 2},
            "publications": [{"title": "Paper 1", "pub_date": "2024-01-01"}],
            "investors": [{"name": "Investor A", "type": "VC"}],
            "metadata": {}
        }
        
        result = await refine_biotech_dossier(
            dossier=test_dossier,
            focus_areas=["pipeline", "financials", "risks", "trials", "publications", "investors"]
        )
        
        assert "pipeline" in result["focus_areas_covered"]
        assert "financials" in result["focus_areas_covered"]
        assert "risks" in result["focus_areas_covered"]
        assert "trials" in result["focus_areas_covered"]
        assert "publications" in result["focus_areas_covered"]
        assert "investors" in result["focus_areas_covered"]
        assert len(result["key_insights"]) > 0
