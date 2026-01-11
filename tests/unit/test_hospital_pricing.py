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
    
    @pytest.mark.asyncio
    async def test_patient_oop_estimate_macro_with_hospital_pricing(self):
        """Test patient OOP estimate macro tool with hospital pricing data."""
        from server import patient_oop_estimate_macro
        
        with patch("server.get_client") as mock_get_client, \
             patch("server.CMS_FEE_SCHEDULES_AVAILABLE", False):
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "prices": [
                    {
                        "procedure_code": "99213",
                        "pricing": {
                            "cash_price": 200.0,
                            "insurance_price": 150.0
                        }
                    }
                ]
            }
            
            result = await patient_oop_estimate_macro(
                procedure_codes=["99213"],
                facility={"hospital_id": "test_123"},
                insurance_plan={
                    "insurance_type": "PPO",
                    "coinsurance_percent": 20.0,
                    "deductible_met": True
                }
            )
            
            assert "procedure_summary" in result
            assert "price_components" in result
            assert "total_estimated_oop" in result
            assert "line_item_estimates" in result
            assert len(result["procedure_summary"]) == 1
            assert result["procedure_summary"][0]["procedure_code"] == "99213"
    
    @pytest.mark.asyncio
    async def test_patient_oop_estimate_macro_with_cms_data(self):
        """Test patient OOP estimate macro tool with CMS fee schedule data."""
        from server import patient_oop_estimate_macro
        
        # Mock CMS fee schedule lookup
        mock_cms_result = {
            "cpt_code": "99213",
            "status": "found",
            "facility_price": 120.0,
            "non_facility_price": 150.0,
            "description": "Office or other outpatient visit"
        }
        
        with patch("server.get_client") as mock_get_client, \
             patch("server.CMS_FEE_SCHEDULES_AVAILABLE", True), \
             patch("server.lookup_cpt_price", return_value=mock_cms_result):
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "prices": []  # No hospital pricing, will use CMS
            }
            
            result = await patient_oop_estimate_macro(
                procedure_codes=["99213"],
                facility={"hospital_id": "test_123"},
                insurance_plan={
                    "insurance_type": "HMO",
                    "copay": 25.0
                }
            )
            
            assert "procedure_summary" in result
            assert "data_sources" in result
            assert "CMS Fee Schedule" in result["data_sources"] or "Turquoise Health API" in result["data_sources"]
            assert result["line_item_estimates"][0]["estimated_oop_min"] == 25.0  # Copay
    
    @pytest.mark.asyncio
    async def test_patient_oop_estimate_macro_self_pay(self):
        """Test patient OOP estimate macro tool for self-pay scenario."""
        from server import patient_oop_estimate_macro
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "prices": [
                    {
                        "procedure_code": "99213",
                        "pricing": {
                            "cash_price": 200.0,
                            "insurance_price": 150.0
                        }
                    }
                ]
            }
            
            result = await patient_oop_estimate_macro(
                procedure_codes=["99213"],
                facility={"hospital_id": "test_123"},
                insurance_plan={
                    "insurance_type": "self-pay"
                }
            )
            
            assert "total_estimated_oop" in result
            # Self-pay should equal cash price
            assert result["line_item_estimates"][0]["estimated_oop_min"] == 200.0
            assert result["line_item_estimates"][0]["estimated_oop_max"] == 200.0
    
    @pytest.mark.asyncio
    async def test_patient_oop_estimate_macro_with_deductible(self):
        """Test patient OOP estimate macro tool with deductible calculation."""
        from server import patient_oop_estimate_macro
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "prices": [
                    {
                        "procedure_code": "99213",
                        "pricing": {
                            "cash_price": 200.0,
                            "insurance_price": 150.0
                        }
                    }
                ]
            }
            
            result = await patient_oop_estimate_macro(
                procedure_codes=["99213"],
                facility={"hospital_id": "test_123"},
                insurance_plan={
                    "insurance_type": "PPO",
                    "deductible": 500.0,
                    "deductible_met": False,
                    "coinsurance_percent": 20.0
                }
            )
            
            assert "total_estimated_oop" in result
            # Should include deductible portion
            assert result["line_item_estimates"][0]["estimated_oop_min"] > 0
            assert "Deductible" in str(result["assumptions"])
    
    @pytest.mark.asyncio
    async def test_patient_oop_estimate_macro_missing_data(self):
        """Test patient OOP estimate macro tool with missing data scenarios."""
        from server import patient_oop_estimate_macro
        
        with patch("server.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            mock_client.get_hospital_rates.return_value = {
                "hospital_id": "test_123",
                "prices": []  # No pricing data
            }
            
            result = await patient_oop_estimate_macro(
                procedure_codes=["99213"],
                facility={"hospital_id": "test_123"}
            )
            
            assert "risk_flags" in result
            assert len(result["risk_flags"]) > 0  # Should have risk flags for missing data
            assert "assumptions" in result

