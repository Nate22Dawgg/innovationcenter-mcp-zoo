"""
Integration tests for MCP server startup and initialization.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

pytestmark = [pytest.mark.integration, pytest.mark.python]


class TestServerStartup:
    """Test that servers can start without errors."""
    
    @pytest.mark.asyncio
    async def test_clinical_trials_server_startup(self):
        """Test Clinical Trials server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "clinical-trials-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as clinical_trials_server
                    assert True  # Server imported successfully
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")
    
    @pytest.mark.asyncio
    async def test_nhanes_server_startup(self):
        """Test NHANES server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "nhanes-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as nhanes_server
                    assert True
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")
    
    @pytest.mark.asyncio
    async def test_hospital_pricing_server_startup(self):
        """Test Hospital Pricing server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "pricing" / "hospital-prices-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as hospital_pricing_server
                    assert True
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")
    
    @pytest.mark.asyncio
    async def test_claims_edi_server_startup(self):
        """Test Claims/EDI server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "claims" / "claims-edi-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as claims_edi_server
                    assert True
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")
    
    @pytest.mark.asyncio
    async def test_biotech_markets_server_startup(self):
        """Test Biotech Markets server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "markets" / "biotech-markets-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as biotech_markets_server
                    assert True
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")
    
    @pytest.mark.asyncio
    async def test_real_estate_server_startup(self):
        """Test Real Estate server can be imported and initialized."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "real-estate" / "real-estate-mcp"))
        
        with patch("mcp.server.Server"):
            with patch("mcp.server.stdio.stdio_server"):
                try:
                    import server as real_estate_server
                    assert True
                except Exception as e:
                    pytest.fail(f"Server failed to import: {e}")

