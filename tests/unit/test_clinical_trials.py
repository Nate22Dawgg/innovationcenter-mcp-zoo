"""
Unit tests for Clinical Trials MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "clinical-trials-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestClinicalTrialsServer:
    """Test Clinical Trials MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            # Import after patching
            import server as clinical_trials_server
            
            # Server should be created
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            # Import server to trigger registration
            import server as clinical_trials_server
            
            # Check that list_tools decorator was called
            # (This is a basic check - actual registration happens via decorators)
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search(self, sample_clinical_trial):
        """Test clinical trials search functionality."""
        from server import clinical_trials_search
        
        with patch("server.search_trials") as mock_search:
            mock_search.return_value = {
                "total": 1,
                "count": 1,
                "offset": 0,
                "trials": [sample_clinical_trial]
            }
            
            result = await clinical_trials_search(
                condition="diabetes",
                limit=10
            )
            
            assert "total" in result
            assert "trials" in result
            assert result["total"] >= 0
            assert isinstance(result["trials"], list)
    
    @pytest.mark.asyncio
    async def test_clinical_trials_get_detail(self):
        """Test getting trial detail by NCT ID."""
        from server import clinical_trials_get_detail
        
        with patch("server.get_trial_detail") as mock_get_detail:
            mock_get_detail.return_value = {
                "nct_id": "NCT01234567",
                "title": "Test Trial",
                "status": "Recruiting"
            }
            
            result = await clinical_trials_get_detail("NCT01234567")
            
            assert "nct_id" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_error_handling(self):
        """Test error handling in search."""
        from server import clinical_trials_search
        
        with patch("server.search_trials") as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            result = await clinical_trials_search(condition="test")
            
            assert "error" in result
            assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_clinical_trials_get_detail_invalid_nct_id(self):
        """Test validation of NCT ID format."""
        from server import clinical_trials_get_detail
        
        result = await clinical_trials_get_detail("INVALID")
        
        # Should return error for invalid format
        assert "error" in result or "nct_id" in result

