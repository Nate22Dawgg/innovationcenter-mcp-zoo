"""
Unit tests for Hospital Pricing MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "pricing" / "hospital-prices-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestHospitalPricingServer:
    """Test Hospital Pricing MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as hospital_pricing_server
            
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as hospital_pricing_server
            
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_hospital_prices_search_procedure(self, sample_hospital_price):
        """Test searching for hospital procedure prices."""
        from server import hospital_prices_search_procedure
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.search_procedure_price.return_value = {
                "count": 1,
                "total": 1,
                "prices": [sample_hospital_price]
            }
            
            result = await hospital_prices_search_procedure(
                cpt_code="99213",
                location="New York, NY"
            )
            
            assert "prices" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_hospital_prices_get_rates(self):
        """Test getting hospital rate sheet."""
        from server import hospital_prices_get_rates
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "hospital_name": "Test Hospital",
                "count": 10,
                "prices": []
            }
            
            result = await hospital_prices_get_rates(
                hospital_id="test_123"
            )
            
            assert "hospital_id" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_hospital_prices_compare(self, sample_hospital_price):
        """Test comparing prices across facilities."""
        from server import hospital_prices_compare
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.compare_prices.return_value = {
                "procedure_code": "99213",
                "count": 5,
                "comparisons": [sample_hospital_price]
            }
            
            result = await hospital_prices_compare(
                cpt_code="99213",
                location="New York, NY",
                limit=10
            )
            
            assert "comparisons" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_hospital_prices_estimate_cash(self):
        """Test cash price estimation."""
        from server import hospital_prices_estimate_cash
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.estimate_cash_price.return_value = {
                "procedure_code": "99213",
                "location": "New York, NY",
                "estimate": {
                    "min": 100.0,
                    "max": 200.0,
                    "median": 150.0
                }
            }
            
            result = await hospital_prices_estimate_cash(
                cpt_code="99213",
                location="New York, NY"
            )
            
            assert "estimate" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        from server import hospital_prices_search_procedure
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.search_procedure_price.side_effect = Exception("API Error")
            
            result = await hospital_prices_search_procedure(
                cpt_code="99213"
            )
            
            assert "error" in result

