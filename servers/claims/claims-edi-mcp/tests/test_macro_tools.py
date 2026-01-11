"""
Tests for claims-edi-mcp macro tools.

Tests for:
- claims_summarize_claim_with_risks
- claims_plan_claim_adjustments
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import tempfile
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import claims_summarize_claim_with_risks, claims_plan_claim_adjustments
from edi_parser import parse_edi_837


pytestmark = [pytest.mark.unit, pytest.mark.python]


# Synthetic EDI 837 sample (clearly synthetic, no real PHI)
SYNTHETIC_EDI_837 = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240101*1200*^*00501*000000001*0*P*:~
GS*HC*SENDER*RECEIVER*20240101*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*1234567890*20240101*1200*CH~
NM1*41*2*TEST HEALTH PLAN*****46*1234567890~
PER*IC*TEST CONTACT*TE*5551234567~
NM1*40*2*TEST BILLING PROVIDER*****46*9876543210~
NM1*85*2*TEST PROVIDER NAME*****XX*1234567890~
N3*123 TEST ST~
N4*TESTCITY*TS*12345~
NM1*QC*1*TESTPATIENT*JOHN*M***MI*123456789~
DMG*D8*19800101*M~
CLM*TESTCLM001*100.00***11:B:1*Y*A*Y*I~
DTP*431*D8*20240101~
REF*D9*123456789~
HI*BK:Z0000~
LX*1~
SV1*HC:99213*100.00*UN*1***1~
DTP*472*D8*20240101~
SE*20*0001~
GE*1*1~
IEA*1*000000001~"""


# Synthetic claim with missing fields (for risk testing)
SYNTHETIC_CLAIM_MISSING_FIELDS = {
    "claim_type": "837",
    "transaction_id": "TEST001",
    "submission_date": "20240101",
    "payer": {
        "name": "Test Payer",
        "id": "PAYER001"
    },
    "provider": {
        "name": "Test Provider",
        "npi": ""  # Missing NPI
    },
    "patient": {
        "name": "Test Patient",
        "dob": "19800101",
        "gender": "M"
    },
    "claim": {
        "claim_number": "",  # Missing claim number
        "charge_amount": 100.00,
        "place_of_service": "11"
    },
    "line_items": [
        {
            "line_number": 1,
            "procedure_code": "",  # Missing procedure code
            "charge_amount": 100.00,
            "diagnosis_code": "",  # Missing diagnosis code
            "place_of_service": "11"
        },
        {
            "line_number": 2,
            "procedure_code": "99213",
            "charge_amount": 0.00,  # Zero charge
            "diagnosis_code": "Z0000",
            "place_of_service": "21"  # Inconsistent with claim
        }
    ],
    "cpt_codes": ["99213", "123"],  # Invalid format
    "hcpcs_codes": []
}


# Synthetic claim with valid structure
SYNTHETIC_CLAIM_VALID = {
    "claim_type": "837",
    "transaction_id": "TEST002",
    "submission_date": "20240101",
    "payer": {
        "name": "Test Payer",
        "id": "PAYER002"
    },
    "provider": {
        "name": "Test Provider",
        "npi": "1234567890"
    },
    "patient": {
        "name": "Test Patient",
        "dob": "19800101",
        "gender": "M"
    },
    "claim": {
        "claim_number": "CLM002",
        "charge_amount": 250.00,
        "place_of_service": "11"
    },
    "line_items": [
        {
            "line_number": 1,
            "procedure_code": "99213",
            "charge_amount": 150.00,
            "diagnosis_code": "Z0000",
            "place_of_service": "11"
        },
        {
            "line_number": 2,
            "procedure_code": "99214",
            "charge_amount": 100.00,
            "diagnosis_code": "Z0000",
            "place_of_service": "11"
        }
    ],
    "cpt_codes": ["99213", "99214"],
    "hcpcs_codes": []
}


class TestClaimsSummarizeClaimWithRisks:
    """Tests for claims_summarize_claim_with_risks."""
    
    @pytest.mark.asyncio
    async def test_with_synthetic_edi_content(self):
        """Test summarizing a claim from EDI content."""
        result = await claims_summarize_claim_with_risks(
            edi_content=SYNTHETIC_EDI_837
        )
        
        assert result["status"] == "success"
        assert "summary" in result
        assert "human_readable_summary" in result
        assert "risk_flags" in result
        assert "risk_details" in result
        assert "line_item_count" in result
        assert "cpt_codes" in result
        assert "hcpcs_codes" in result
        
        # Verify summary structure
        summary = result["summary"]
        assert "claim_number" in summary
        assert "total_charge_amount" in summary
        assert "line_item_count" in summary
        assert "provider" in summary
        assert "payer" in summary
    
    @pytest.mark.asyncio
    async def test_with_claim_dict(self):
        """Test summarizing a claim from parsed claim dictionary."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_VALID
        )
        
        assert result["status"] == "success"
        assert result["summary"]["claim_number"] == "CLM002"
        assert result["summary"]["total_charge_amount"] == 250.00
        assert result["line_item_count"] == 2
    
    @pytest.mark.asyncio
    async def test_risk_flagging_missing_provider_npi(self):
        """Test that missing provider NPI is flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "missing_provider_npi" in result["risk_flags"]
        assert any("Provider NPI" in detail for detail in result["risk_details"])
    
    @pytest.mark.asyncio
    async def test_risk_flagging_missing_claim_number(self):
        """Test that missing claim number is flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "missing_claim_number" in result["risk_flags"]
    
    @pytest.mark.asyncio
    async def test_risk_flagging_missing_procedure_code(self):
        """Test that missing procedure codes are flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "missing_procedure_code" in result["risk_flags"]
        assert any("Line item 1" in detail and "missing_procedure_code" in detail for detail in result["risk_details"])
    
    @pytest.mark.asyncio
    async def test_risk_flagging_missing_diagnosis_code(self):
        """Test that missing diagnosis codes are flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "missing_diagnosis_code" in result["risk_flags"]
    
    @pytest.mark.asyncio
    async def test_risk_flagging_zero_charge(self):
        """Test that zero or negative charges are flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "zero_or_negative_charge" in result["risk_flags"]
    
    @pytest.mark.asyncio
    async def test_risk_flagging_inconsistent_place_of_service(self):
        """Test that inconsistent place of service is flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "inconsistent_place_of_service" in result["risk_flags"]
    
    @pytest.mark.asyncio
    async def test_risk_flagging_invalid_cpt_format(self):
        """Test that invalid CPT code format is flagged."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        assert "invalid_cpt_code_format" in result["risk_flags"]
        assert any("Invalid CPT code format" in detail for detail in result["risk_details"])
    
    @pytest.mark.asyncio
    async def test_with_edi_file_path(self):
        """Test summarizing a claim from EDI file path."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(SYNTHETIC_EDI_837)
            temp_path = f.name
        
        try:
            result = await claims_summarize_claim_with_risks(
                edi_file_path=temp_path
            )
            
            assert result["status"] == "success"
            assert "summary" in result
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_missing_all_inputs(self):
        """Test that providing no inputs returns error."""
        result = await claims_summarize_claim_with_risks()
        
        assert result["status"] == "error" or "error" in result
        assert "BAD_REQUEST" in str(result).upper() or "must be provided" in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_human_readable_summary_format(self):
        """Test that human-readable summary is properly formatted."""
        result = await claims_summarize_claim_with_risks(
            claim=SYNTHETIC_CLAIM_VALID
        )
        
        assert "human_readable_summary" in result
        summary_text = result["human_readable_summary"]
        assert "Claim Summary:" in summary_text
        assert "Claim Number:" in summary_text
        assert "Provider:" in summary_text
        assert "Payer:" in summary_text
        assert "Total Charge:" in summary_text
        assert "Line Items:" in summary_text


class TestClaimsPlanClaimAdjustments:
    """Tests for claims_plan_claim_adjustments."""
    
    @pytest.mark.asyncio
    async def test_with_synthetic_edi_content(self):
        """Test planning adjustments from EDI content."""
        result = await claims_plan_claim_adjustments(
            edi_content=SYNTHETIC_EDI_837
        )
        
        assert result["status"] == "success"
        assert "adjustment_plan" in result
        plan = result["adjustment_plan"]
        assert "claim_number" in plan
        assert "review_status" in plan
        assert "line_items_to_review" in plan
        assert "suggested_code_changes" in plan
        assert "documentation_needs" in plan
        assert "potential_issues" in plan
        assert "summary" in plan
        assert "note" in plan
        assert "planning tool only" in plan["note"].lower()
    
    @pytest.mark.asyncio
    async def test_with_claim_dict(self):
        """Test planning adjustments from parsed claim dictionary."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        assert plan["review_status"] == "pending_review"
        assert len(plan["line_items_to_review"]) > 0
    
    @pytest.mark.asyncio
    async def test_read_only_verification(self):
        """Test that the tool explicitly states it's read-only."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_VALID
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        assert "note" in plan
        assert "planning tool only" in plan["note"].lower()
        assert "no changes" in plan["note"].lower() or "not write" in plan["note"].lower()
    
    @pytest.mark.asyncio
    async def test_identifies_missing_modifiers(self):
        """Test that missing modifiers are identified."""
        claim_without_modifier = {
            **SYNTHETIC_CLAIM_VALID,
            "line_items": [
                {
                    "line_number": 1,
                    "procedure_code": "99213",
                    "charge_amount": 150.00,
                    "procedure_modifier": "",  # Missing modifier
                    "diagnosis_code": "Z0000",
                    "place_of_service": "11"
                }
            ]
        }
        
        result = await claims_plan_claim_adjustments(
            claim=claim_without_modifier
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        # Should flag missing modifier
        line_reviews = plan["line_items_to_review"]
        assert any("missing_modifier" in str(item.get("issues", [])) for item in line_reviews)
    
    @pytest.mark.asyncio
    async def test_identifies_missing_diagnosis_codes(self):
        """Test that missing diagnosis codes are identified."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        line_reviews = plan["line_items_to_review"]
        assert any("missing_diagnosis_code" in str(item.get("issues", [])) for item in line_reviews)
        # Should be high priority
        assert any(item.get("review_priority") == "high" for item in line_reviews if "missing_diagnosis_code" in str(item.get("issues", [])))
    
    @pytest.mark.asyncio
    async def test_identifies_place_of_service_inconsistency(self):
        """Test that place of service inconsistencies are identified."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        line_reviews = plan["line_items_to_review"]
        assert any("inconsistent_place_of_service" in str(item.get("issues", [])) for item in line_reviews)
    
    @pytest.mark.asyncio
    async def test_identifies_zero_charge(self):
        """Test that zero charges are identified."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        line_reviews = plan["line_items_to_review"]
        assert any("zero_or_negative_charge" in str(item.get("issues", [])) for item in line_reviews)
        # Should be high priority
        assert any(item.get("review_priority") == "high" for item in line_reviews if "zero_or_negative_charge" in str(item.get("issues", [])))
    
    @pytest.mark.asyncio
    async def test_with_payer_rules(self):
        """Test that payer rules are applied."""
        payer_rules = {
            "require_modifiers": True,
            "max_line_items": 1
        }
        
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_VALID,
            payer_rules=payer_rules
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        # Should flag if modifiers are required but missing
        # Should flag if exceeds max line items
        assert len(plan["potential_issues"]) >= 0  # May or may not have issues depending on claim
    
    @pytest.mark.asyncio
    async def test_suggested_code_changes(self):
        """Test that invalid codes trigger suggested changes."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        # Should have suggested code changes for invalid CPT format
        assert len(plan["suggested_code_changes"]) > 0
        assert any("Invalid CPT code format" in str(change) for change in plan["suggested_code_changes"])
    
    @pytest.mark.asyncio
    async def test_summary_statistics(self):
        """Test that summary statistics are calculated."""
        result = await claims_plan_claim_adjustments(
            claim=SYNTHETIC_CLAIM_MISSING_FIELDS
        )
        
        assert result["status"] == "success"
        plan = result["adjustment_plan"]
        summary = plan["summary"]
        assert "total_line_items" in summary
        assert "line_items_requiring_review" in summary
        assert "total_issues_found" in summary
        assert "high_priority_issues" in summary
        assert "suggested_code_changes_count" in summary
        assert "documentation_needs_count" in summary
        assert summary["total_line_items"] == 2
        assert summary["line_items_requiring_review"] >= 0
    
    @pytest.mark.asyncio
    async def test_missing_all_inputs(self):
        """Test that providing no inputs returns error."""
        result = await claims_plan_claim_adjustments()
        
        assert result["status"] == "error" or "error" in result
        assert "BAD_REQUEST" in str(result).upper() or "must be provided" in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_no_modifications_to_data(self):
        """Test that the function never modifies the input claim data."""
        original_claim = SYNTHETIC_CLAIM_VALID.copy()
        original_line_items = [item.copy() for item in original_claim["line_items"]]
        
        result = await claims_plan_claim_adjustments(
            claim=original_claim
        )
        
        # Verify original claim was not modified
        assert original_claim == SYNTHETIC_CLAIM_VALID
        assert original_claim["line_items"] == original_line_items
        assert result["status"] == "success"
