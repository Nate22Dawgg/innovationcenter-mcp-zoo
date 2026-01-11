"""
Unit tests for S&P Global MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestSPGlobalServer:
    """Test S&P Global MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_sp_global_search_companies_success(self):
        """Test successful company search."""
        from server import sp_global_search_companies
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.search_companies.return_value = {
                "count": 1,
                "companies": [
                    {
                        "company_id": "12345",
                        "name": "Test Company",
                        "ticker": "TEST",
                        "country": "US"
                    }
                ],
                "query": "Test"
            }
            
            result = await sp_global_search_companies(query="Test", limit=10)
            
            assert "companies" in result or "count" in result
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_sp_global_search_companies_timeout(self):
        """Test company search with timeout error."""
        from server import sp_global_search_companies
        import requests
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            # Simulate timeout
            timeout_error = requests.exceptions.Timeout("Request timed out")
            mock_client.search_companies.side_effect = timeout_error
            
            result = await sp_global_search_companies(query="Test", limit=10)
            
            # Should return error response (already using map_upstream_error)
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_sp_global_get_fundamentals_success(self):
        """Test successful fundamentals retrieval."""
        from server import sp_global_get_fundamentals
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_fundamentals.return_value = {
                "company_id": "12345",
                "period_type": "Annual",
                "fundamentals": {
                    "revenue": 1000000,
                    "net_income": 100000
                }
            }
            
            result = await sp_global_get_fundamentals(
                company_id="12345",
                period_type="Annual"
            )
            
            assert "fundamentals" in result or "company_id" in result
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_sp_global_get_fundamentals_403_forbidden(self):
        """Test fundamentals retrieval with 403 Forbidden error."""
        from server import sp_global_get_fundamentals
        from common.errors import ApiError
        import requests
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            # Simulate 403 Forbidden
            response = Mock()
            response.status_code = 403
            http_error = requests.exceptions.HTTPError(response=response)
            api_error = ApiError(
                message="Forbidden: Access denied",
                status_code=403,
                original_error=http_error
            )
            mock_client.get_fundamentals.side_effect = api_error
            
            result = await sp_global_get_fundamentals(
                company_id="12345",
                period_type="Annual"
            )
            
            # Should return error response (already using map_upstream_error)
            assert "error" in result
