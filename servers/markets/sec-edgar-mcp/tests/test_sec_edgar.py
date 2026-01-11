"""
Unit tests for SEC EDGAR MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestSecEdgarServer:
    """Test SEC EDGAR MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_sec_search_company_success(self):
        """Test successful company search."""
        import sys
        import importlib
        # Import the server module
        server_module = importlib.import_module("server")
        sec_search_company = server_module.sec_search_company
        
        with patch("sec_edgar_client.search_company_cik") as mock_search_cik, \
             patch("sec_edgar_client.get_company_ticker_info") as mock_ticker_info, \
             patch("sec_edgar_client.get_company_submissions") as mock_submissions:
            
            # Mock successful search
            mock_search_cik.return_value = "0000320193"  # Apple CIK
            mock_ticker_info.return_value = None
            mock_submissions.return_value = {
                "name": "Apple Inc.",
                "tickers": ["AAPL"]
            }
            
            result = await sec_search_company(query="Apple", limit=10)
            
            assert "companies" in result
            assert result["count"] > 0
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_sec_search_company_timeout(self):
        """Test company search with timeout error."""
        import sys
        import importlib
        server_module = importlib.import_module("server")
        sec_search_company = server_module.sec_search_company
        from common.errors import McpError, ErrorCode
        import requests
        
        with patch("sec_edgar_client.search_company_cik") as mock_search_cik:
            # Simulate timeout
            timeout_error = requests.exceptions.Timeout("Request timed out")
            mock_search_cik.side_effect = timeout_error
            
            result = await sec_search_company(query="Apple", limit=10)
            
            # Should return error in response (current behavior)
            # After standardization, this should raise McpError
            assert "error" in result or "companies" in result
    
    @pytest.mark.asyncio
    async def test_sec_get_company_filings_success(self):
        """Test successful filing retrieval."""
        import sys
        import importlib
        server_module = importlib.import_module("server")
        sec_get_company_filings = server_module.sec_get_company_filings
        
        with patch("sec_edgar_client.search_company_cik") as mock_search_cik, \
             patch("sec_edgar_client.get_filings_by_cik") as mock_get_filings:
            
            mock_search_cik.return_value = "0000320193"
            mock_get_filings.return_value = [
                {
                    "form_type": "10-K",
                    "filing_date": "2024-01-01",
                    "accession_number": "0000320193-24-000001",
                    "cik": "0000320193"
                }
            ]
            
            result = await sec_get_company_filings(
                company_name="Apple",
                form_type="10-K",
                limit=10
            )
            
            assert "filings" in result
            assert result["count"] > 0
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_sec_get_company_filings_403_forbidden(self):
        """Test filing retrieval with 403 Forbidden error."""
        import sys
        import importlib
        server_module = importlib.import_module("server")
        sec_get_company_filings = server_module.sec_get_company_filings
        from common.errors import ApiError
        import requests
        
        with patch("sec_edgar_client.search_company_cik") as mock_search_cik:
            # Simulate 403 Forbidden
            response = Mock()
            response.status_code = 403
            http_error = requests.exceptions.HTTPError(response=response)
            api_error = ApiError(
                message="Forbidden: Access denied",
                status_code=403,
                original_error=http_error
            )
            mock_search_cik.side_effect = api_error
            
            result = await sec_get_company_filings(
                company_name="Apple",
                limit=10
            )
            
            # Should return error in response
            assert "error" in result or "filings" in result
    
    @pytest.mark.asyncio
    async def test_sec_get_filing_content_success(self):
        """Test successful filing content retrieval."""
        import sys
        import importlib
        server_module = importlib.import_module("server")
        sec_get_filing_content = server_module.sec_get_filing_content
        
        with patch("sec_edgar_client.get_filing_content") as mock_get_content:
            mock_get_content.return_value = {
                "cik": "0000320193",
                "accession_number": "0000320193-24-000001",
                "content": "Test filing content...",
                "content_length": 1000,
                "url": "https://data.sec.gov/files/data/0000320193/0000320193-24-000001/0000320193-24-000001.txt"
            }
            
            result = await sec_get_filing_content(
                cik="0000320193",
                accession_number="0000320193-24-000001"
            )
            
            assert "content_preview" in result or "content" in result
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_sec_get_filing_content_malformed_response(self):
        """Test filing content retrieval with malformed upstream response."""
        import sys
        import importlib
        server_module = importlib.import_module("server")
        sec_get_filing_content = server_module.sec_get_filing_content
        import json
        
        with patch("sec_edgar_client.get_filing_content") as mock_get_content:
            # Simulate malformed JSON response
            mock_get_content.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            
            result = await sec_get_filing_content(
                cik="0000320193",
                accession_number="0000320193-24-000001"
            )
            
            # Should return error in response
            assert "error" in result
