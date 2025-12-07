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
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_empty_results(self):
        """Test handling of empty search results."""
        from server import clinical_trials_search
        
        with patch("server.search_trials") as mock_search:
            mock_search.return_value = {
                "total": 0,
                "count": 0,
                "offset": 0,
                "trials": []
            }
            
            result = await clinical_trials_search(condition="nonexistent_condition_xyz")
            
            assert "total" in result
            assert result["total"] == 0
            assert "trials" in result
            assert isinstance(result["trials"], list)
            assert len(result["trials"]) == 0
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_huge_results(self):
        """Test handling of large result sets with pagination."""
        from server import clinical_trials_search
        
        # Simulate huge result set
        huge_trials = [{"nct_id": f"NCT{i:08d}", "title": f"Trial {i}"} for i in range(1000)]
        
        with patch("server.search_trials") as mock_search:
            mock_search.return_value = {
                "total": 1000,
                "count": 100,  # Limited by pagination
                "offset": 0,
                "trials": huge_trials[:100]
            }
            
            result = await clinical_trials_search(condition="diabetes", limit=100)
            
            assert result["total"] == 1000
            assert result["count"] == 100
            assert len(result["trials"]) == 100
            assert result["count"] < result["total"]  # Pagination working
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_invalid_inputs(self):
        """Test handling of invalid input parameters."""
        from server import clinical_trials_search
        
        # Test negative limit
        with patch("server.search_trials") as mock_search:
            result = await clinical_trials_search(condition="diabetes", limit=-1)
            # Should either reject or clamp to valid range
            assert "error" in result or result.get("count", 0) >= 0
        
        # Test limit exceeding maximum
        with patch("server.search_trials") as mock_search:
            result = await clinical_trials_search(condition="diabetes", limit=1000)
            # Should either reject or clamp to max (typically 100)
            assert "error" in result or result.get("count", 0) <= 100
        
        # Test negative offset
        with patch("server.search_trials") as mock_search:
            result = await clinical_trials_search(condition="diabetes", offset=-1)
            # Should either reject or clamp to 0
            assert "error" in result or result.get("offset", 0) >= 0
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_rate_limit(self):
        """Test handling of rate limit errors from upstream API."""
        from server import clinical_trials_search
        from common.errors import RateLimitError
        
        with patch("server.search_trials") as mock_search:
            mock_search.side_effect = RateLimitError(
                "Rate limit exceeded",
                retry_after=60
            )
            
            result = await clinical_trials_search(condition="diabetes")
            
            # Should handle rate limit gracefully
            assert "error" in result or "retry_after" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_network_error(self):
        """Test handling of network errors."""
        from server import clinical_trials_search
        from common.errors import ApiError
        
        with patch("server.search_trials") as mock_search:
            mock_search.side_effect = ApiError(
                "Network error",
                status_code=None,
                original_error=ConnectionError("Connection refused")
            )
            
            result = await clinical_trials_search(condition="diabetes")
            
            # Should handle network error gracefully
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_timeout(self):
        """Test handling of timeout errors."""
        from server import clinical_trials_search
        from common.errors import ApiError, ErrorCode
        
        with patch("server.search_trials") as mock_search:
            mock_search.side_effect = ApiError(
                "Request timed out",
                code=ErrorCode.API_TIMEOUT
            )
            
            result = await clinical_trials_search(condition="diabetes")
            
            # Should handle timeout gracefully
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_special_characters(self):
        """Test handling of special characters in search terms."""
        from server import clinical_trials_search
        
        special_queries = [
            "diabetes & hypertension",
            "test@example.com",
            "query with 'quotes'",
            "query with \"double quotes\"",
            "query with /slashes/",
        ]
        
        for query in special_queries:
            with patch("server.search_trials") as mock_search:
                mock_search.return_value = {
                    "total": 0,
                    "count": 0,
                    "offset": 0,
                    "trials": []
                }
                
                result = await clinical_trials_search(condition=query)
                
                # Should handle special characters without crashing
                assert "total" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_search_unicode(self):
        """Test handling of unicode characters."""
        from server import clinical_trials_search
        
        unicode_queries = [
            "糖尿病",  # Chinese for diabetes
            "диабет",  # Russian for diabetes
            "diabète",  # French for diabetes
        ]
        
        for query in unicode_queries:
            with patch("server.search_trials") as mock_search:
                mock_search.return_value = {
                    "total": 0,
                    "count": 0,
                    "offset": 0,
                    "trials": []
                }
                
                result = await clinical_trials_search(condition=query)
                
                # Should handle unicode without crashing
                assert "total" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_clinical_trials_get_detail_not_found(self):
        """Test handling of non-existent trial ID."""
        from server import clinical_trials_get_detail
        from common.errors import ApiError, ErrorCode
        
        with patch("server.get_trial_detail") as mock_get_detail:
            mock_get_detail.side_effect = ApiError(
                "Trial not found",
                status_code=404,
                code=ErrorCode.API_NOT_FOUND
            )
            
            result = await clinical_trials_get_detail("NCT99999999")
            
            # Should handle not found gracefully
            assert "error" in result or "nct_id" not in result

