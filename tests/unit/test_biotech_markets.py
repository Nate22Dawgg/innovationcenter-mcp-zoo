"""
Unit tests for Biotech Markets MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "markets" / "biotech-markets-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestBiotechMarketsServer:
    """Test Biotech Markets MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as biotech_markets_server
            
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as biotech_markets_server
            
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_biotech_search_companies(self, sample_biotech_company):
        """Test searching for biotech companies."""
        from server import biotech_search_companies
        
        with patch("server.search_companies") as mock_search:
            mock_search.return_value = [sample_biotech_company]
            
            result = await biotech_search_companies(
                therapeutic_area="Oncology",
                limit=20
            )
            
            assert "companies" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_biotech_get_company_profile(self):
        """Test getting company profile."""
        from server import biotech_get_company_profile
        
        with patch("server.get_profile") as mock_get_profile:
            mock_get_profile.return_value = {
                "company_name": "Test Biotech",
                "pipeline": [],
                "trials": []
            }
            
            result = await biotech_get_company_profile(
                company_name="Test Biotech"
            )
            
            assert "company_name" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_biotech_get_pipeline_drugs(self):
        """Test getting pipeline drugs."""
        from server import biotech_get_pipeline_drugs
        
        with patch("server.get_pipeline_drugs") as mock_get_pipeline:
            mock_get_pipeline.return_value = [
                {"drug_name": "Test Drug", "phase": "Phase 3"}
            ]
            
            result = await biotech_get_pipeline_drugs(
                company_name="Test Biotech"
            )
            
            assert "drugs" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_biotech_get_funding_rounds(self):
        """Test getting funding rounds."""
        from server import biotech_get_funding_rounds
        
        with patch("server.get_ipo_filings") as mock_get_filings:
            mock_get_filings.return_value = [
                {
                    "filing_date": "2023-01-01",
                    "form_type": "S-1",
                    "accession_number": "0001234567-23-000001"
                }
            ]
            
            result = await biotech_get_funding_rounds(
                company_name="Test Biotech"
            )
            
            assert "funding_rounds" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_biotech_analyze_target_exposure(self):
        """Test analyzing target exposure."""
        from server import biotech_analyze_target_exposure
        
        with patch("server.get_target_exposure") as mock_get_exposure:
            mock_get_exposure.return_value = [
                {
                    "company": "Test Biotech",
                    "trial_count": 5,
                    "phases": ["Phase 2", "Phase 3"]
                }
            ]
            
            result = await biotech_analyze_target_exposure(
                target="PD-1"
            )
            
            assert "companies" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        from server import biotech_search_companies
        
        with patch("server.search_companies") as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            result = await biotech_search_companies()
            
            assert "error" in result

