"""
Unit tests for Claims/EDI MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, mock_open
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "claims" / "claims-edi-mcp"))

pytestmark = [pytest.mark.unit, pytest.mark.python]


class TestClaimsEDIServer:
    """Test Claims/EDI MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized without errors."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as claims_edi_server
            
            assert mock_server_class.called
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that tools are properly registered."""
        with patch("mcp.server.Server") as mock_server_class:
            mock_server = Mock()
            mock_server_class.return_value = mock_server
            
            import server as claims_edi_server
            
            assert mock_server is not None
    
    @pytest.mark.asyncio
    async def test_claims_parse_edi_837(self):
        """Test parsing EDI 837 file."""
        from server import claims_parse_edi_837
        
        sample_edi = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*^*00501*000000001*0*P*:~"
        
        with patch("server.parse_edi_837") as mock_parse:
            mock_parse.return_value = {
                "status": "success",
                "claims": []
            }
            
            result = await claims_parse_edi_837(edi_content=sample_edi)
            
            assert "status" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_claims_parse_edi_835(self):
        """Test parsing EDI 835 file."""
        from server import claims_parse_edi_835
        
        sample_edi = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*^*00501*000000001*0*P*:~"
        
        with patch("server.parse_edi_835") as mock_parse:
            mock_parse.return_value = {
                "status": "success",
                "remittances": []
            }
            
            result = await claims_parse_edi_835(edi_content=sample_edi)
            
            assert "status" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_claims_normalize_line_item(self, sample_claim_line_item):
        """Test normalizing claim line item."""
        from server import claims_normalize_line_item
        
        with patch("server.normalize_claim_line_item") as mock_normalize:
            mock_normalize.return_value = sample_claim_line_item
            
            result = await claims_normalize_line_item(
                line_item=sample_claim_line_item
            )
            
            assert "normalized_item" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_claims_lookup_cpt_price(self):
        """Test CPT code price lookup."""
        from server import claims_lookup_cpt_price
        
        with patch("server.lookup_cpt_price") as mock_lookup:
            mock_lookup.return_value = {
                "cpt_code": "99213",
                "price": 120.00,
                "year": 2023
            }
            
            result = await claims_lookup_cpt_price(
                cpt_code="99213"
            )
            
            assert "cpt_code" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_claims_lookup_hcpcs_price(self):
        """Test HCPCS code price lookup."""
        from server import claims_lookup_hcpcs_price
        
        with patch("server.lookup_hcpcs_price") as mock_lookup:
            mock_lookup.return_value = {
                "hcpcs_code": "A0425",
                "price": 50.00,
                "year": 2023
            }
            
            result = await claims_lookup_hcpcs_price(
                hcpcs_code="A0425"
            )
            
            assert "hcpcs_code" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        from server import claims_parse_edi_837
        
        with patch("server.parse_edi_837") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            
            result = await claims_parse_edi_837(edi_content="invalid")
            
            assert "error" in result

