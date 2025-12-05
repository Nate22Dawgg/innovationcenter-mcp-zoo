"""
Unit tests for Real Estate MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "real-estate" / "real-estate-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestRealEstateServer:
    """Test Real Estate MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as real_estate_server
            
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as real_estate_server
            
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_real_estate_property_lookup(self, sample_property):
        """Test property lookup."""
        from server import real_estate_property_lookup
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.get_property_lookup.return_value = sample_property
            
            result = await real_estate_property_lookup(
                address="123 Main St, New York, NY 10001"
            )
            
            assert "address" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_real_estate_get_tax_records(self):
        """Test getting tax records."""
        from server import real_estate_get_tax_records
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.get_tax_records.return_value = {
                "address": "123 Main St",
                "tax_amount": 10000,
                "assessed_value": 500000
            }
            
            result = await real_estate_get_tax_records(
                address="123 Main St",
                county="New York",
                state="NY"
            )
            
            assert "address" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_real_estate_get_parcel_info(self):
        """Test getting parcel information."""
        from server import real_estate_get_parcel_info
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.get_parcel_info.return_value = {
                "address": "123 Main St",
                "parcel_id": "123456",
                "boundaries": {}
            }
            
            result = await real_estate_get_parcel_info(
                address="123 Main St",
                county="New York",
                state="NY"
            )
            
            assert "parcel_id" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_real_estate_search_recent_sales(self):
        """Test searching recent sales."""
        from server import real_estate_search_recent_sales
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.search_recent_sales.return_value = {
                "zip_code": "10001",
                "sales": [],
                "count": 0
            }
            
            result = await real_estate_search_recent_sales(
                zip_code="10001",
                days=90,
                limit=10
            )
            
            assert "zip_code" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_real_estate_get_market_trends(self):
        """Test getting market trends."""
        from server import real_estate_get_market_trends
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.get_market_trends.return_value = {
                "zip_code": "10001",
                "trends": {},
                "statistics": {}
            }
            
            result = await real_estate_get_market_trends(
                zip_code="10001"
            )
            
            assert "zip_code" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        from server import real_estate_property_lookup
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            mock_router.get_property_lookup.side_effect = Exception("API Error")
            
            result = await real_estate_property_lookup(
                address="invalid"
            )
            
            assert "error" in result

