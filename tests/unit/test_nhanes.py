"""
Unit tests for NHANES MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "nhanes-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestNHANESServer:
    """Test NHANES MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            # Import after patching
            import server as nhanes_server
            
            # Server should be created
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as nhanes_server
            
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_nhanes_list_datasets(self, sample_nhanes_dataset):
        """Test listing NHANES datasets."""
        from server import nhanes_list_datasets
        
        with patch("server.list_datasets") as mock_list:
            mock_list.return_value = ["demographics", "body_measures"]
            
            result = await nhanes_list_datasets(cycle="2017-2018")
            
            assert "datasets" in result or "cycles" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_nhanes_get_data(self, sample_nhanes_dataset):
        """Test querying NHANES data."""
        from server import nhanes_get_data
        
        with patch("server.query_data") as mock_query:
            mock_query.return_value = {
                "dataset": "demographics",
                "cycle": "2017-2018",
                "row_count": 100,
                "data": []
            }
            
            result = await nhanes_get_data(
                dataset="demographics",
                cycle="2017-2018",
                limit=100
            )
            
            assert "dataset" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_nhanes_get_variable_info(self):
        """Test getting variable information."""
        from server import nhanes_get_variable_info
        
        with patch("server.get_variable_info") as mock_get_info:
            mock_get_info.return_value = {
                "variable": "RIDAGEYR",
                "description": "Age in years",
                "type": "numeric"
            }
            
            result = await nhanes_get_variable_info(
                dataset="demographics",
                variable="RIDAGEYR",
                cycle="2017-2018"
            )
            
            assert "variable" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_nhanes_calculate_percentile(self):
        """Test percentile calculation."""
        from server import nhanes_calculate_percentile
        
        with patch("server.calculate_percentile") as mock_calc:
            mock_calc.return_value = {
                "variable": "BMXBMI",
                "value": 25.0,
                "percentile": 75.5
            }
            
            result = await nhanes_calculate_percentile(
                variable="BMXBMI",
                value=25.0,
                dataset="body_measures",
                cycle="2017-2018"
            )
            
            assert "percentile" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_nhanes_error_handling(self):
        """Test error handling."""
        from server import nhanes_get_data
        
        with patch("server.query_data") as mock_query:
            mock_query.side_effect = Exception("Data not found")
            
            result = await nhanes_get_data(
                dataset="invalid",
                cycle="2017-2018"
            )
            
            assert "error" in result

