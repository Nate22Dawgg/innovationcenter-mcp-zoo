"""
EDI Parser Wrapper for X12 837 and 835 Files

This module provides functions to parse EDI 837 (Professional Claims) and 
EDI 835 (Remittance Advice) files, with normalization to consistent JSON format.

Handles:
- EDI 837: Professional claims submission
- EDI 835: Remittance advice (payment/denial information)
- CPT/HCPCS code extraction
- Line item normalization
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


# X12 EDI Segment Delimiters
SEGMENT_TERMINATOR = "~"
ELEMENT_SEPARATOR = "*"
SUB_ELEMENT_SEPARATOR = ":"
REPETITION_SEPARATOR = "^"


def parse_edi_837(edi_content: str) -> Dict[str, Any]:
    """
    Parse EDI 837 Professional Claim file.
    
    Args:
        edi_content: EDI file content as string or file path
        
    Returns:
        Dictionary with normalized claim data:
        {
            "claim_type": "837",
            "transaction_id": "...",
            "submission_date": "...",
            "payer": {...},
            "provider": {...},
            "patient": {...},
            "claim": {...},
            "line_items": [...],
            "cpt_codes": [...],
            "hcpcs_codes": [...]
        }
    """
    # Handle file path input
    if isinstance(edi_content, str) and Path(edi_content).exists():
        with open(edi_content, 'r', encoding='utf-8', errors='ignore') as f:
            edi_content = f.read()
    
    if not edi_content or not isinstance(edi_content, str):
        raise ValueError("Invalid EDI content: must be string or file path")
    
    # Parse X12 segments
    segments = _parse_x12_segments(edi_content)
    
    # Extract ISA/GS/ST headers
    isa_segment = _find_segment(segments, "ISA")
    gs_segment = _find_segment(segments, "GS")
    st_segment = _find_segment(segments, "ST")
    
    # Extract transaction control number
    transaction_id = st_segment[2] if st_segment and len(st_segment) > 2 else "UNKNOWN"
    
    # Extract submission date from BHT segment
    bht_segment = _find_segment(segments, "BHT")
    submission_date = None
    if bht_segment and len(bht_segment) > 4:
        submission_date = bht_segment[4]  # BHT04 - Date
    
    # Extract payer information (NM1*PR segment)
    payer = _extract_payer(segments)
    
    # Extract provider information (NM1*85 segment)
    provider = _extract_provider(segments)
    
    # Extract patient information (NM1*QC segment)
    patient = _extract_patient(segments)
    
    # Extract claim information (CLM segment)
    claim = _extract_claim(segments)
    
    # Extract line items (LX, SV1/SV2 segments)
    line_items = _extract_line_items(segments)
    
    # Extract CPT and HCPCS codes
    cpt_codes = extract_cpt_codes({"line_items": line_items})
    hcpcs_codes = extract_hcpcs_codes({"line_items": line_items})
    
    return {
        "claim_type": "837",
        "transaction_id": transaction_id,
        "submission_date": submission_date,
        "payer": payer,
        "provider": provider,
        "patient": patient,
        "claim": claim,
        "line_items": line_items,
        "cpt_codes": cpt_codes,
        "hcpcs_codes": hcpcs_codes,
        "raw_segment_count": len(segments)
    }


def parse_edi_835(edi_content: str) -> Dict[str, Any]:
    """
    Parse EDI 835 Remittance Advice file.
    
    Args:
        edi_content: EDI file content as string or file path
        
    Returns:
        Dictionary with normalized remittance data:
        {
            "remittance_type": "835",
            "transaction_id": "...",
            "payment_date": "...",
            "payer": {...},
            "payee": {...},
            "claims": [...],
            "summary": {...}
        }
    """
    # Handle file path input
    if isinstance(edi_content, str) and Path(edi_content).exists():
        with open(edi_content, 'r', encoding='utf-8', errors='ignore') as f:
            edi_content = f.read()
    
    if not edi_content or not isinstance(edi_content, str):
        raise ValueError("Invalid EDI content: must be string or file path")
    
    # Parse X12 segments
    segments = _parse_x12_segments(edi_content)
    
    # Extract transaction control number
    st_segment = _find_segment(segments, "ST")
    transaction_id = st_segment[2] if st_segment and len(st_segment) > 2 else "UNKNOWN"
    
    # Extract payment date from BPR segment
    bpr_segment = _find_segment(segments, "BPR")
    payment_date = None
    if bpr_segment and len(bpr_segment) > 16:
        payment_date = bpr_segment[16]  # BPR16 - Payment Date
    
    # Extract payer information
    payer = _extract_payer_835(segments)
    
    # Extract payee information
    payee = _extract_payee(segments)
    
    # Extract claims and payment information
    claims = _extract_835_claims(segments)
    
    # Extract summary information
    summary = _extract_835_summary(segments)
    
    return {
        "remittance_type": "835",
        "transaction_id": transaction_id,
        "payment_date": payment_date,
        "payer": payer,
        "payee": payee,
        "claims": claims,
        "summary": summary,
        "raw_segment_count": len(segments)
    }


def normalize_claim_line_item(line_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a claim line item to consistent format.
    
    Args:
        line_item: Raw line item dictionary from parser
        
    Returns:
        Normalized line item with standard fields:
        {
            "line_number": int,
            "procedure_code": str,
            "procedure_modifier": str,
            "diagnosis_code": str,
            "units": float,
            "charge_amount": float,
            "service_date": str,
            "place_of_service": str,
            "description": str
        }
    """
    normalized = {
        "line_number": line_item.get("line_number", line_item.get("sequence", 0)),
        "procedure_code": line_item.get("procedure_code", line_item.get("cpt_code", line_item.get("hcpcs_code", ""))),
        "procedure_modifier": line_item.get("modifier", line_item.get("procedure_modifier", "")),
        "diagnosis_code": line_item.get("diagnosis_code", line_item.get("diagnosis", "")),
        "units": float(line_item.get("units", line_item.get("quantity", 1.0))),
        "charge_amount": float(line_item.get("charge_amount", line_item.get("amount", line_item.get("charge", 0.0)))),
        "service_date": line_item.get("service_date", line_item.get("date", "")),
        "place_of_service": line_item.get("place_of_service", line_item.get("pos", "")),
        "description": line_item.get("description", line_item.get("procedure_description", ""))
    }
    
    # Clean up empty strings
    for key, value in normalized.items():
        if isinstance(value, str) and not value:
            normalized[key] = None
        elif isinstance(value, float) and value == 0.0 and key != "units":
            normalized[key] = None
    
    return normalized


def extract_cpt_codes(claim: Dict[str, Any]) -> List[str]:
    """
    Extract CPT codes from a parsed claim.
    
    Args:
        claim: Parsed claim dictionary
        
    Returns:
        List of CPT codes (5-digit numeric codes)
    """
    cpt_codes = []
    
    # Check line items
    line_items = claim.get("line_items", [])
    for item in line_items:
        proc_code = item.get("procedure_code", "")
        if proc_code and _is_cpt_code(proc_code):
            if proc_code not in cpt_codes:
                cpt_codes.append(proc_code)
    
    # Check claim-level codes
    claim_data = claim.get("claim", {})
    proc_code = claim_data.get("procedure_code", "")
    if proc_code and _is_cpt_code(proc_code):
        if proc_code not in cpt_codes:
            cpt_codes.append(proc_code)
    
    return sorted(cpt_codes)


def extract_hcpcs_codes(claim: Dict[str, Any]) -> List[str]:
    """
    Extract HCPCS codes from a parsed claim.
    
    Args:
        claim: Parsed claim dictionary
        
    Returns:
        List of HCPCS codes (alphanumeric codes)
    """
    hcpcs_codes = []
    
    # Check line items
    line_items = claim.get("line_items", [])
    for item in line_items:
        proc_code = item.get("procedure_code", "")
        if proc_code and _is_hcpcs_code(proc_code):
            if proc_code not in hcpcs_codes:
                hcpcs_codes.append(proc_code)
    
    # Check claim-level codes
    claim_data = claim.get("claim", {})
    proc_code = claim_data.get("procedure_code", "")
    if proc_code and _is_hcpcs_code(proc_code):
        if proc_code not in hcpcs_codes:
            hcpcs_codes.append(proc_code)
    
    return sorted(hcpcs_codes)


# Internal helper functions

def _parse_x12_segments(edi_content: str) -> List[List[str]]:
    """Parse X12 EDI content into segments."""
    # Remove whitespace and newlines
    content = re.sub(r'\s+', '', edi_content)
    
    # Split by segment terminator
    segment_strings = content.split(SEGMENT_TERMINATOR)
    
    segments = []
    for seg_str in segment_strings:
        if not seg_str.strip():
            continue
        # Split by element separator
        elements = seg_str.split(ELEMENT_SEPARATOR)
        if elements:
            segments.append(elements)
    
    return segments


def _find_segment(segments: List[List[str]], segment_id: str) -> Optional[List[str]]:
    """Find first segment with given ID."""
    for seg in segments:
        if seg and seg[0] == segment_id:
            return seg
    return None


def _find_segments(segments: List[List[str]], segment_id: str) -> List[List[str]]:
    """Find all segments with given ID."""
    return [seg for seg in segments if seg and seg[0] == segment_id]


def _extract_payer(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract payer information from NM1*PR segment."""
    payer_segments = _find_segments(segments, "NM1")
    for seg in payer_segments:
        if len(seg) > 2 and seg[1] == "PR":  # PR = Payer
            return {
                "entity_type": "PR",
                "name": seg[3] if len(seg) > 3 else "",
                "id": seg[9] if len(seg) > 9 else ""
            }
    return {}


def _extract_provider(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract provider information from NM1*85 segment."""
    provider_segments = _find_segments(segments, "NM1")
    for seg in provider_segments:
        if len(seg) > 2 and seg[1] == "85":  # 85 = Billing Provider
            return {
                "entity_type": "85",
                "name": seg[3] if len(seg) > 3 else "",
                "npi": seg[9] if len(seg) > 9 else "",
                "tax_id": ""
            }
    return {}


def _extract_patient(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract patient information from NM1*QC segment."""
    patient_segments = _find_segments(segments, "NM1")
    for seg in patient_segments:
        if len(seg) > 2 and seg[1] == "QC":  # QC = Patient
            return {
                "entity_type": "QC",
                "last_name": seg[3] if len(seg) > 3 else "",
                "first_name": seg[4] if len(seg) > 4 else "",
                "member_id": seg[9] if len(seg) > 9 else ""
            }
    return {}


def _extract_claim(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract claim information from CLM segment."""
    clm_segment = _find_segment(segments, "CLM")
    if not clm_segment or len(clm_segment) < 2:
        return {}
    
    return {
        "claim_number": clm_segment[1] if len(clm_segment) > 1 else "",
        "charge_amount": float(clm_segment[2]) if len(clm_segment) > 2 and clm_segment[2] else 0.0,
        "place_of_service": clm_segment[5] if len(clm_segment) > 5 else "",
        "diagnosis_codes": []
    }


def _extract_line_items(segments: List[List[str]]) -> List[Dict[str, Any]]:
    """Extract line items from LX and SV1/SV2 segments."""
    line_items = []
    lx_segments = _find_segments(segments, "LX")
    
    for lx_seg in lx_segments:
        line_number = lx_seg[1] if len(lx_seg) > 1 else ""
        
        # Find SV1 or SV2 segment following this LX
        line_item = {
            "line_number": line_number,
            "procedure_code": "",
            "charge_amount": 0.0,
            "units": 1.0,
            "service_date": ""
        }
        
        # Look for SV1 (Professional Service) or SV2 (Facility Service)
        # This is simplified - real parsing would track segment order
        line_items.append(line_item)
    
    return line_items


def _extract_payer_835(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract payer information from 835 NM1*PR segment."""
    return _extract_payer(segments)


def _extract_payee(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract payee information from 835 NM1*PE segment."""
    payee_segments = _find_segments(segments, "NM1")
    for seg in payee_segments:
        if len(seg) > 2 and seg[1] == "PE":  # PE = Payee
            return {
                "entity_type": "PE",
                "name": seg[3] if len(seg) > 3 else "",
                "npi": seg[9] if len(seg) > 9 else ""
            }
    return {}


def _extract_835_claims(segments: List[List[str]]) -> List[Dict[str, Any]]:
    """Extract claim payment information from 835 CLP segments."""
    claims = []
    clp_segments = _find_segments(segments, "CLP")
    
    for clp_seg in clp_segments:
        if len(clp_seg) < 4:
            continue
        
        claim = {
            "claim_number": clp_seg[1] if len(clp_seg) > 1 else "",
            "claim_status": clp_seg[2] if len(clp_seg) > 2 else "",
            "charge_amount": float(clp_seg[3]) if len(clp_seg) > 3 and clp_seg[3] else 0.0,
            "paid_amount": float(clp_seg[4]) if len(clp_seg) > 4 and clp_seg[4] else 0.0,
            "patient_responsibility": float(clp_seg[5]) if len(clp_seg) > 5 and clp_seg[5] else 0.0,
            "claim_filing_indicator": clp_seg[6] if len(clp_seg) > 6 else ""
        }
        claims.append(claim)
    
    return claims


def _extract_835_summary(segments: List[List[str]]) -> Dict[str, Any]:
    """Extract summary information from 835 SE segment."""
    se_segment = _find_segment(segments, "SE")
    bpr_segment = _find_segment(segments, "BPR")
    
    summary = {
        "total_claims": len(_find_segments(segments, "CLP")),
        "transaction_control_number": se_segment[2] if se_segment and len(se_segment) > 2 else ""
    }
    
    if bpr_segment and len(bpr_segment) > 2:
        summary["total_payment_amount"] = float(bpr_segment[2]) if bpr_segment[2] else 0.0
    
    return summary


def _is_cpt_code(code: str) -> bool:
    """Check if code is a CPT code (5-digit numeric)."""
    if not code:
        return False
    # Remove modifiers if present
    code_clean = code.split("-")[0].strip()
    return len(code_clean) == 5 and code_clean.isdigit()


def _is_hcpcs_code(code: str) -> bool:
    """Check if code is an HCPCS code (alphanumeric, typically starts with letter)."""
    if not code:
        return False
    # Remove modifiers if present
    code_clean = code.split("-")[0].strip()
    # HCPCS codes are typically 5 characters, alphanumeric, often starting with a letter
    return len(code_clean) == 5 and code_clean[0].isalpha() and code_clean[1:].isalnum()

