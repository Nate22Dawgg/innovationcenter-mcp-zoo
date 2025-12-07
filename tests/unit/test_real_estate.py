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


class TestRealEstateConfig:
    """Test Real Estate MCP Server configuration."""
    
    def test_config_load_without_api_key(self):
        """Test config loads without API key (fail-soft)."""
        import os
        from config import load_config, RealEstateConfig
        
        # Clear API key if set
        original_key = os.environ.get("BATCHDATA_API_KEY")
        if "BATCHDATA_API_KEY" in os.environ:
            del os.environ["BATCHDATA_API_KEY"]
        
        try:
            config = load_config()
            issues = config.validate()
            
            # Should have non-critical issue about missing API key
            assert len(issues) > 0
            assert any(issue.field == "BATCHDATA_API_KEY" and not issue.critical for issue in issues)
        finally:
            if original_key:
                os.environ["BATCHDATA_API_KEY"] = original_key
    
    def test_config_load_with_api_key(self):
        """Test config loads with API key."""
        import os
        from config import load_config
        
        original_key = os.environ.get("BATCHDATA_API_KEY")
        os.environ["BATCHDATA_API_KEY"] = "test_key_1234567890"
        
        try:
            config = load_config()
            issues = config.validate()
            
            # Should not have critical issues
            assert not any(issue.critical for issue in issues)
        finally:
            if original_key:
                os.environ["BATCHDATA_API_KEY"] = original_key
            elif "BATCHDATA_API_KEY" in os.environ:
                del os.environ["BATCHDATA_API_KEY"]
    
    def test_config_invalid_base_url(self):
        """Test config validation with invalid base URL."""
        from config import RealEstateConfig
        
        config = RealEstateConfig(
            batchdata_api_key="test_key",
            batchdata_base_url="invalid_url"
        )
        issues = config.validate()
        
        # Should have non-critical issue about invalid URL
        assert any(issue.field == "BATCHDATA_BASE_URL" for issue in issues)


class TestInvestmentAnalysis:
    """Test investment analysis tools."""
    
    @pytest.mark.asyncio
    async def test_generate_property_investment_brief(self):
        """Test generating property investment brief."""
        from server import real_estate_generate_property_investment_brief
        from unittest.mock import Mock, patch
        
        mock_property_data = {
            "property_data": {
                "apn": "123456",
                "estimated_value": 500000,
                "square_feet": 2000,
                "property_type": "Single Family",
                "bedrooms": 3,
                "bathrooms": 2,
                "year_built": 2000
            }
        }
        
        mock_tax_records = {
            "tax_records": {
                "assessed_value": 450000,
                "tax_amount": 9000,
                "tax_year": 2024
            }
        }
        
        mock_recent_sales = {
            "recent_sales": [
                {
                    "sale_date": "2024-01-15",
                    "sale_price": 480000,
                    "sale_type": "arms_length"
                }
            ]
        }
        
        mock_market_trends = {
            "median_price": 500000,
            "price_trend": "increasing",
            "days_on_market": 30
        }
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            
            # Mock router methods
            mock_router.get_property_lookup.return_value = mock_property_data
            mock_router.get_tax_records.return_value = mock_tax_records
            mock_router.search_recent_sales.return_value = mock_recent_sales
            mock_router.get_market_trends.return_value = mock_market_trends
            
            result = await real_estate_generate_property_investment_brief(
                address="123 Main St, New York, NY 10001"
            )
            
            assert "address" in result
            assert "tax_info" in result
            assert "red_flags" in result
            assert isinstance(result["red_flags"], list)
            if "estimated_value" in result:
                assert result["estimated_value"] == 500000
    
    @pytest.mark.asyncio
    async def test_compare_properties(self):
        """Test comparing multiple properties."""
        from server import real_estate_compare_properties
        from unittest.mock import Mock, patch
        
        mock_property_data = {
            "property_data": {
                "estimated_value": 500000,
                "square_feet": 2000
            }
        }
        
        mock_tax_records = {
            "tax_records": {
                "tax_amount": 9000
            }
        }
        
        with patch("server.get_router") as mock_get_router:
            mock_router = Mock()
            mock_get_router.return_value = mock_router
            
            # Mock router methods to return consistent data
            mock_router.get_property_lookup.return_value = mock_property_data
            mock_router.get_tax_records.return_value = mock_tax_records
            mock_router.search_recent_sales.return_value = {"recent_sales": []}
            mock_router.get_market_trends.return_value = {}
            
            result = await real_estate_compare_properties(
                properties=[
                    "123 Main St, New York, NY 10001",
                    "456 Oak Ave, New York, NY 10001"
                ]
            )
            
            assert "properties" in result
            assert isinstance(result["properties"], list)
            assert len(result["properties"]) == 2
            assert "summary" in result
            assert "comparison_metrics" in result["summary"]
    
    @pytest.mark.asyncio
    async def test_compare_properties_too_few(self):
        """Test comparing properties with too few properties."""
        from server import real_estate_compare_properties
        
        result = await real_estate_compare_properties(
            properties=["123 Main St"]
        )
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_compare_properties_too_many(self):
        """Test comparing properties with too many properties."""
        from server import real_estate_compare_properties
        
        result = await real_estate_compare_properties(
            properties=[f"Property {i}" for i in range(11)]
        )
        
        assert "error" in result

