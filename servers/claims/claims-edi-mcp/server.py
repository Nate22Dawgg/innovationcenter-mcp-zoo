#!/usr/bin/env python3
"""
Claims/EDI MCP Server

MCP server for health insurance claims processing, EDI 837/835 parsing, 
CPT/HCPCS pricing, and claims normalization.

Provides tools for:
- Parsing EDI 837 (Professional Claims) files
- Parsing EDI 835 (Remittance Advice) files
- Normalizing claim line items
- Looking up CPT codes in CMS fee schedules
- Looking up HCPCS codes in CMS fee schedules
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading and common modules
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from edi_parser import (
    parse_edi_837,
    parse_edi_835,
    normalize_claim_line_item,
    extract_cpt_codes,
    extract_hcpcs_codes
)
from cms_fee_schedules import (
    lookup_cpt_price,
    lookup_hcpcs_price
)
from config import load_config, ClaimsEdiConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import common utilities for logging and PHI handling
try:
    from common.logging import get_logger, request_context
    from common.phi import redact_phi, is_ephemeral
    from common.validation import validate_tool_input, validate_tool_output
    from common.errors import (
        ValidationError,
        format_error_response,
        map_upstream_error,
        ErrorCode,
        McpError,
    )
    from common.observability import observe_tool_call
    COMMON_AVAILABLE = True
    VALIDATION_AVAILABLE = True
    ERROR_HANDLING_AVAILABLE = True
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    COMMON_AVAILABLE = False
    VALIDATION_AVAILABLE = False
    ERROR_HANDLING_AVAILABLE = False
    OBSERVABILITY_AVAILABLE = False
    # Fallback logging
    import logging
    def get_logger(name: str):
        return logging.getLogger(name)
    def request_context(logger, tool_name, **kwargs):
        from contextlib import nullcontext
        return nullcontext()
    def redact_phi(payload: Any) -> Any:
        return payload
    def is_ephemeral(data: Dict[str, Any]) -> bool:
        return False
    def observe_tool_call(server_name: str):
        def decorator(func):
            return func
        return decorator
    map_upstream_error = None
    ErrorCode = None
    McpError = Exception
    print("Warning: Common modules not found. PHI redaction and validation will be skipped.", file=sys.stderr)

# Try to import MCP SDK - fallback to basic implementation if not available
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    # Fallback: create minimal MCP-like interface
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not found. Install with: pip install mcp", file=sys.stderr)


# Load schemas
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


# Initialize logger
logger = get_logger("claims-edi-mcp") if COMMON_AVAILABLE else None

# Initialize configuration
_config: Optional[ClaimsEdiConfig] = None
_config_error_payload: Optional[Dict[str, Any]] = None


def get_config() -> ClaimsEdiConfig:
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

# Tool implementations with observability
@observe_tool_call(server_name="claims-edi-mcp") if OBSERVABILITY_AVAILABLE else lambda f: f
async def claims_parse_edi_837(
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse EDI 837 Professional Claim file.
    
    Args:
        edi_content: EDI file content as string
        edi_file_path: Path to EDI file (alternative to edi_content)
    
    Returns:
        Dictionary with normalized claim data (marked as ephemeral due to PHI)
    """
    if logger:
        with request_context(logger, "claims_parse_edi_837", 
                           edi_file_path=edi_file_path if edi_file_path else None,
                           has_edi_content=bool(edi_content)):
            try:
                if edi_file_path:
                    result = parse_edi_837(edi_file_path)
                elif edi_content:
                    result = parse_edi_837(edi_content)
                else:
                    # Missing required parameter - return structured error
                    if ERROR_HANDLING_AVAILABLE and ErrorCode:
                        error = McpError(
                            code=ErrorCode.BAD_REQUEST,
                            message="Either edi_content or edi_file_path must be provided",
                            details={"missing_fields": ["edi_content", "edi_file_path"]}
                        )
                        return format_error_response(error)
                    return {
                        "error": {
                            "code": "BAD_REQUEST",
                            "message": "Either edi_content or edi_file_path must be provided"
                        },
                        "status": "error"
                    }
                
                return result
            except Exception as e:
                if logger:
                    logger.error(f"Error parsing EDI 837: {e}", exc_info=True)
                # Map to standardized error and return structured response
                if ERROR_HANDLING_AVAILABLE and map_upstream_error:
                    mcp_error = map_upstream_error(e)
                    return format_error_response(mcp_error)
                return {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(e) or "An unexpected error occurred"
                    },
                    "status": "error"
                }
    else:
        # Fallback without logging
        try:
            if edi_file_path:
                result = parse_edi_837(edi_file_path)
            elif edi_content:
                result = parse_edi_837(edi_content)
            else:
                # Missing required parameter - return structured error
                if ERROR_HANDLING_AVAILABLE and ErrorCode:
                    error = McpError(
                        code=ErrorCode.BAD_REQUEST,
                        message="Either edi_content or edi_file_path must be provided",
                        details={"missing_fields": ["edi_content", "edi_file_path"]}
                    )
                    return format_error_response(error)
                return {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Either edi_content or edi_file_path must be provided"
                    },
                    "status": "error"
                }
            return result
        except Exception as e:
            # Map to standardized error and return structured response
            if ERROR_HANDLING_AVAILABLE and map_upstream_error:
                mcp_error = map_upstream_error(e)
                return format_error_response(mcp_error)
            return {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e) or "An unexpected error occurred"
                },
                "status": "error"
            }


@observe_tool_call(server_name="claims-edi-mcp") if OBSERVABILITY_AVAILABLE else lambda f: f
async def claims_parse_edi_835(
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse EDI 835 Remittance Advice file.
    
    Args:
        edi_content: EDI file content as string
        edi_file_path: Path to EDI file (alternative to edi_content)
    
    Returns:
        Dictionary with normalized remittance data (marked as ephemeral due to PHI)
    """
    if logger:
        with request_context(logger, "claims_parse_edi_835",
                           edi_file_path=edi_file_path if edi_file_path else None,
                           has_edi_content=bool(edi_content)):
            try:
                if edi_file_path:
                    result = parse_edi_835(edi_file_path)
                elif edi_content:
                    result = parse_edi_835(edi_content)
                else:
                    # Missing required parameter - return structured error
                    if ERROR_HANDLING_AVAILABLE and ErrorCode:
                        error = McpError(
                            code=ErrorCode.BAD_REQUEST,
                            message="Either edi_content or edi_file_path must be provided",
                            details={"missing_fields": ["edi_content", "edi_file_path"]}
                        )
                        return format_error_response(error)
                    return {
                        "error": {
                            "code": "BAD_REQUEST",
                            "message": "Either edi_content or edi_file_path must be provided"
                        },
                        "status": "error"
                    }
                
                return result
            except Exception as e:
                if logger:
                    logger.error(f"Error parsing EDI 835: {e}", exc_info=True)
                # Map to standardized error and return structured response
                if ERROR_HANDLING_AVAILABLE and map_upstream_error:
                    mcp_error = map_upstream_error(e)
                    return format_error_response(mcp_error)
                return {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(e) or "An unexpected error occurred"
                    },
                    "status": "error"
                }
    else:
        # Fallback without logging
        try:
            if edi_file_path:
                result = parse_edi_835(edi_file_path)
            elif edi_content:
                result = parse_edi_835(edi_content)
            else:
                # Missing required parameter - return structured error
                if ERROR_HANDLING_AVAILABLE and ErrorCode:
                    error = McpError(
                        code=ErrorCode.BAD_REQUEST,
                        message="Either edi_content or edi_file_path must be provided",
                        details={"missing_fields": ["edi_content", "edi_file_path"]}
                    )
                    return format_error_response(error)
                return {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Either edi_content or edi_file_path must be provided"
                    },
                    "status": "error"
                }
            return result
        except Exception as e:
            # Map to standardized error and return structured response
            if ERROR_HANDLING_AVAILABLE and map_upstream_error:
                mcp_error = map_upstream_error(e)
                return format_error_response(mcp_error)
            return {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e) or "An unexpected error occurred"
                },
                "status": "error"
            }


async def claims_normalize_line_item(
    line_item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize a claim line item to consistent format.
    
    Args:
        line_item: Raw line item dictionary from parser
    
    Returns:
        Normalized line item with standard fields
    """
    try:
        result = normalize_claim_line_item(line_item)
        return {
            "status": "success",
            "normalized_item": result
        }
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "status": "error"
        }


@observe_tool_call(server_name="claims-edi-mcp") if OBSERVABILITY_AVAILABLE else lambda f: f
async def claims_lookup_cpt_price(
    cpt_code: str,
    year: Optional[int] = None,
    locality: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lookup CPT code price from CMS Physician Fee Schedule.
    
    Args:
        cpt_code: CPT procedure code (5-digit, e.g., "99213")
        year: Year for fee schedule (default: current year)
        locality: Locality code (default: "00" for national average)
    
    Returns:
        Dictionary with price information
    """
    try:
        result = lookup_cpt_price(
            cpt_code=cpt_code,
            year=year,
            locality=locality
        )
        return result
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "cpt_code": cpt_code,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "status": "error"
        }


async def claims_lookup_hcpcs_price(
    hcpcs_code: str,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lookup HCPCS code price from CMS fee schedules.
    
    Args:
        hcpcs_code: HCPCS procedure code (5-character alphanumeric, e.g., "A0425")
        year: Year for fee schedule (default: current year)
    
    Returns:
        Dictionary with price information
    """
    try:
        result = lookup_hcpcs_price(
            hcpcs_code=hcpcs_code,
            year=year
        )
        return result
    except Exception as e:
        # Map to standardized error and return structured response
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        # Fallback for when error handling not available
        return {
            "hcpcs_code": hcpcs_code,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "status": "error"
        }


@observe_tool_call(server_name="claims-edi-mcp") if OBSERVABILITY_AVAILABLE else lambda f: f
async def claims_summarize_claim_with_risks(
    claim: Optional[Dict[str, Any]] = None,
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a human-readable summary of a claim with risk flags.
    
    This tool analyzes a parsed EDI 837 claim or normalized claim structure
    and identifies potential issues, coding errors, and inconsistencies.
    
    Args:
        claim: Normalized claim dictionary (from parse_edi_837 or other source)
        edi_content: EDI file content as string (alternative to claim)
        edi_file_path: Path to EDI file (alternative to claim or edi_content)
    
    Returns:
        Dictionary with human-readable summary and risk flags
    """
    try:
        # Parse EDI if needed
        if claim is None:
            if edi_file_path:
                claim = parse_edi_837(edi_file_path)
            elif edi_content:
                claim = parse_edi_837(edi_content)
            else:
                if ERROR_HANDLING_AVAILABLE and ErrorCode:
                    error = McpError(
                        code=ErrorCode.BAD_REQUEST,
                        message="Either claim, edi_content, or edi_file_path must be provided",
                        details={"missing_fields": ["claim", "edi_content", "edi_file_path"]}
                    )
                    return format_error_response(error)
                return {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Either claim, edi_content, or edi_file_path must be provided"
                    },
                    "status": "error"
                }
        
        # Extract key information
        claim_data = claim.get("claim", {})
        line_items = claim.get("line_items", [])
        provider = claim.get("provider", {})
        patient = claim.get("patient", {})
        payer = claim.get("payer", {})
        
        # Build summary
        summary = {
            "claim_type": claim.get("claim_type", "unknown"),
            "transaction_id": claim.get("transaction_id", "unknown"),
            "submission_date": claim.get("submission_date"),
            "claim_number": claim_data.get("claim_number", "unknown"),
            "total_charge_amount": claim_data.get("charge_amount", 0.0),
            "line_item_count": len(line_items),
            "provider": {
                "name": provider.get("name", "unknown"),
                "npi": provider.get("npi", "unknown")
            },
            "payer": {
                "name": payer.get("name", "unknown"),
                "id": payer.get("id", "unknown")
            }
        }
        
        # Analyze risks
        risk_flags = []
        risk_details = []
        
        # Check for missing required fields
        if not provider.get("npi"):
            risk_flags.append("missing_provider_npi")
            risk_details.append("Provider NPI is missing or invalid")
        
        if not claim_data.get("claim_number"):
            risk_flags.append("missing_claim_number")
            risk_details.append("Claim number is missing")
        
        # Check line items for issues
        for idx, line_item in enumerate(line_items):
            line_risks = []
            
            # Check for missing procedure codes
            proc_code = line_item.get("procedure_code", "")
            if not proc_code:
                line_risks.append("missing_procedure_code")
                risk_flags.append("missing_procedure_code")
            
            # Check for missing modifiers when they might be required
            modifier = line_item.get("procedure_modifier", "")
            charge_amount = line_item.get("charge_amount", 0.0)
            if charge_amount > 0 and not modifier and proc_code:
                # Some procedures require modifiers - this is a soft check
                pass
            
            # Check for inconsistent place of service
            pos = line_item.get("place_of_service", "")
            claim_pos = claim_data.get("place_of_service", "")
            if pos and claim_pos and pos != claim_pos:
                line_risks.append("inconsistent_place_of_service")
                risk_flags.append("inconsistent_place_of_service")
            
            # Check for missing diagnosis codes
            diag_code = line_item.get("diagnosis_code", "")
            if not diag_code:
                line_risks.append("missing_diagnosis_code")
                risk_flags.append("missing_diagnosis_code")
            
            # Check for zero or negative charges
            if charge_amount <= 0:
                line_risks.append("zero_or_negative_charge")
                risk_flags.append("zero_or_negative_charge")
            
            if line_risks:
                risk_details.append(f"Line item {idx + 1} ({proc_code}): {', '.join(line_risks)}")
        
        # Check for coding errors (simplified checks)
        cpt_codes = claim.get("cpt_codes", [])
        hcpcs_codes = claim.get("hcpcs_codes", [])
        
        # Check for invalid CPT code format
        for code in cpt_codes:
            if len(code) != 5 or not code.isdigit():
                risk_flags.append("invalid_cpt_code_format")
                risk_details.append(f"Invalid CPT code format: {code}")
        
        # Check for invalid HCPCS code format
        for code in hcpcs_codes:
            if len(code) != 5 or not (code[0].isalpha() and code[1:].isalnum()):
                risk_flags.append("invalid_hcpcs_code_format")
                risk_details.append(f"Invalid HCPCS code format: {code}")
        
        # Build human-readable summary
        human_readable = f"Claim Summary:\n"
        human_readable += f"  Claim Number: {summary['claim_number']}\n"
        human_readable += f"  Submission Date: {summary['submission_date'] or 'Unknown'}\n"
        human_readable += f"  Provider: {summary['provider']['name']} (NPI: {summary['provider']['npi']})\n"
        human_readable += f"  Payer: {summary['payer']['name']}\n"
        human_readable += f"  Total Charge: ${summary['total_charge_amount']:.2f}\n"
        human_readable += f"  Line Items: {summary['line_item_count']}\n"
        
        if risk_flags:
            human_readable += f"\nRisk Flags ({len(risk_flags)}):\n"
            for flag in set(risk_flags):
                human_readable += f"  - {flag}\n"
        
        if risk_details:
            human_readable += f"\nRisk Details:\n"
            for detail in risk_details:
                human_readable += f"  - {detail}\n"
        
        return {
            "status": "success",
            "summary": summary,
            "human_readable_summary": human_readable,
            "risk_flags": list(set(risk_flags)),  # Remove duplicates
            "risk_details": risk_details,
            "line_item_count": len(line_items),
            "cpt_codes": cpt_codes,
            "hcpcs_codes": hcpcs_codes
        }
    except Exception as e:
        if logger:
            logger.error(f"Error summarizing claim: {e}", exc_info=True)
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "status": "error"
        }


@observe_tool_call(server_name="claims-edi-mcp") if OBSERVABILITY_AVAILABLE else lambda f: f
async def claims_plan_claim_adjustments(
    claim: Optional[Dict[str, Any]] = None,
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None,
    payer_rules: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a structured plan of potential claim adjustments (read-only planning tool).
    
    This tool analyzes a claim and suggests potential adjustments, code changes,
    or documentation needs. It does NOT write to external systems - this is a
    planning tool only.
    
    Args:
        claim: Normalized claim dictionary (from parse_edi_837 or other source)
        edi_content: EDI file content as string (alternative to claim)
        edi_file_path: Path to EDI file (alternative to claim or edi_content)
        payer_rules: Optional payer-specific rules (e.g., {"require_modifiers": True, "max_line_items": 10})
    
    Returns:
        Dictionary with structured adjustment plan
    """
    try:
        # Parse EDI if needed
        if claim is None:
            if edi_file_path:
                claim = parse_edi_837(edi_file_path)
            elif edi_content:
                claim = parse_edi_837(edi_content)
            else:
                if ERROR_HANDLING_AVAILABLE and ErrorCode:
                    error = McpError(
                        code=ErrorCode.BAD_REQUEST,
                        message="Either claim, edi_content, or edi_file_path must be provided",
                        details={"missing_fields": ["claim", "edi_content", "edi_file_path"]}
                    )
                    return format_error_response(error)
                return {
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Either claim, edi_content, or edi_file_path must be provided"
                    },
                    "status": "error"
                }
        
        # Extract claim information
        claim_data = claim.get("claim", {})
        line_items = claim.get("line_items", [])
        
        # Build adjustment plan
        adjustment_plan = {
            "claim_number": claim_data.get("claim_number", "unknown"),
            "review_status": "pending_review",
            "line_items_to_review": [],
            "suggested_code_changes": [],
            "documentation_needs": [],
            "potential_issues": []
        }
        
        # Analyze each line item
        for idx, line_item in enumerate(line_items):
            line_review = {
                "line_number": line_item.get("line_number", idx + 1),
                "procedure_code": line_item.get("procedure_code", ""),
                "issues": [],
                "suggested_changes": [],
                "review_priority": "normal"
            }
            
            # Check for missing modifiers
            modifier = line_item.get("procedure_modifier", "")
            proc_code = line_item.get("procedure_code", "")
            if not modifier and proc_code:
                # Some procedures may require modifiers - flag for review
                line_review["issues"].append("missing_modifier")
                line_review["suggested_changes"].append("Consider adding appropriate modifier if required by payer")
                adjustment_plan["potential_issues"].append(f"Line {idx + 1}: Missing modifier for {proc_code}")
            
            # Check for missing diagnosis codes
            diag_code = line_item.get("diagnosis_code", "")
            if not diag_code:
                line_review["issues"].append("missing_diagnosis_code")
                line_review["suggested_changes"].append("Add appropriate diagnosis code")
                line_review["review_priority"] = "high"
                adjustment_plan["documentation_needs"].append(f"Line {idx + 1}: Diagnosis code required")
            
            # Check for place of service consistency
            pos = line_item.get("place_of_service", "")
            claim_pos = claim_data.get("place_of_service", "")
            if pos and claim_pos and pos != claim_pos:
                line_review["issues"].append("inconsistent_place_of_service")
                line_review["suggested_changes"].append(f"Verify place of service: line has {pos}, claim has {claim_pos}")
                adjustment_plan["potential_issues"].append(f"Line {idx + 1}: Place of service inconsistency")
            
            # Check charge amount reasonableness
            charge_amount = line_item.get("charge_amount", 0.0)
            if charge_amount <= 0:
                line_review["issues"].append("zero_or_negative_charge")
                line_review["review_priority"] = "high"
                adjustment_plan["potential_issues"].append(f"Line {idx + 1}: Zero or negative charge amount")
            
            # Apply payer rules if provided
            if payer_rules:
                if payer_rules.get("require_modifiers", False) and not modifier:
                    line_review["issues"].append("payer_requires_modifier")
                    line_review["review_priority"] = "high"
                
                max_line_items = payer_rules.get("max_line_items")
                if max_line_items and len(line_items) > max_line_items:
                    adjustment_plan["potential_issues"].append(f"Exceeds payer maximum line items ({max_line_items})")
            
            if line_review["issues"]:
                adjustment_plan["line_items_to_review"].append(line_review)
        
        # Check for code changes
        cpt_codes = claim.get("cpt_codes", [])
        for code in cpt_codes:
            # Simplified check - in real implementation, would check against code sets
            if len(code) != 5 or not code.isdigit():
                adjustment_plan["suggested_code_changes"].append({
                    "current_code": code,
                    "issue": "Invalid CPT code format",
                    "suggestion": "Verify and correct CPT code"
                })
        
        # Summary
        total_issues = sum(len(item["issues"]) for item in adjustment_plan["line_items_to_review"])
        high_priority_count = sum(1 for item in adjustment_plan["line_items_to_review"] if item["review_priority"] == "high")
        
        adjustment_plan["summary"] = {
            "total_line_items": len(line_items),
            "line_items_requiring_review": len(adjustment_plan["line_items_to_review"]),
            "total_issues_found": total_issues,
            "high_priority_issues": high_priority_count,
            "suggested_code_changes_count": len(adjustment_plan["suggested_code_changes"]),
            "documentation_needs_count": len(adjustment_plan["documentation_needs"])
        }
        
        # Note: This is a read-only planning tool
        adjustment_plan["note"] = "This is a planning tool only. No changes have been made to external systems."
        
        return {
            "status": "success",
            "adjustment_plan": adjustment_plan
        }
    except Exception as e:
        if logger:
            logger.error(f"Error planning claim adjustments: {e}", exc_info=True)
        if ERROR_HANDLING_AVAILABLE and map_upstream_error:
            mcp_error = map_upstream_error(e)
            return format_error_response(mcp_error)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e) or "An unexpected error occurred"
            },
            "status": "error"
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("claims-edi-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="claims_parse_edi_837",
                description="Parse EDI 837 Professional Claim file into normalized JSON format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to edi_content)"
                        }
                    },
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_parse_edi_835",
                description="Parse EDI 835 Remittance Advice file into normalized JSON format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to edi_content)"
                        }
                    },
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_normalize_line_item",
                description="Normalize a claim line item to consistent format with standard fields",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "line_item": {
                            "type": "object",
                            "description": "Raw line item dictionary from parser"
                        }
                    },
                    "required": ["line_item"],
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_lookup_cpt_price",
                description="Lookup CPT code price from CMS Physician Fee Schedule",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT procedure code (5-digit, e.g., '99213')",
                            "pattern": "^[0-9]{5}$"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for fee schedule (default: current year)",
                            "minimum": 2000,
                            "maximum": 2100
                        },
                        "locality": {
                            "type": "string",
                            "description": "Locality code (default: '00' for national average)",
                            "default": "00"
                        }
                    },
                    "required": ["cpt_code"],
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_lookup_hcpcs_price",
                description="Lookup HCPCS code price from CMS fee schedules",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hcpcs_code": {
                            "type": "string",
                            "description": "HCPCS procedure code (5-character alphanumeric, e.g., 'A0425')",
                            "pattern": "^[A-Z][0-9A-Z]{4}$"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for fee schedule (default: current year)",
                            "minimum": 2000,
                            "maximum": 2100
                        }
                    },
                    "required": ["hcpcs_code"],
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_summarize_claim_with_risks",
                description="Generate a human-readable summary of a claim with risk flags and potential issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "object",
                            "description": "Normalized claim dictionary (from parse_edi_837 or other source)"
                        },
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string (alternative to claim)"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to claim or edi_content)"
                        }
                    },
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_plan_claim_adjustments",
                description="Generate a structured plan of potential claim adjustments (read-only planning tool)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "object",
                            "description": "Normalized claim dictionary (from parse_edi_837 or other source)"
                        },
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string (alternative to claim)"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to claim or edi_content)"
                        },
                        "payer_rules": {
                            "type": "object",
                            "description": "Optional payer-specific rules (e.g., require_modifiers, max_line_items)",
                            "properties": {
                                "require_modifiers": {
                                    "type": "boolean",
                                    "description": "Whether payer requires modifiers"
                                },
                                "max_line_items": {
                                    "type": "integer",
                                    "description": "Maximum number of line items allowed",
                                    "minimum": 1
                                }
                            }
                        }
                    },
                    "additionalProperties": false
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls with schema validation."""
        try:
            # Validate input against JSON schema
            if VALIDATION_AVAILABLE:
                try:
                    validate_tool_input(name, arguments)
                except ValidationError as ve:
                    # Return properly formatted validation error
                    error_response = format_error_response(ve)
                    return [TextContent(
                        type="text",
                        text=json.dumps(error_response, indent=2)
                    )]

            # Execute tool
            if name == "claims_parse_edi_837":
                result = await claims_parse_edi_837(**arguments)
            elif name == "claims_parse_edi_835":
                result = await claims_parse_edi_835(**arguments)
            elif name == "claims_normalize_line_item":
                result = await claims_normalize_line_item(**arguments)
            elif name == "claims_lookup_cpt_price":
                result = await claims_lookup_cpt_price(**arguments)
            elif name == "claims_lookup_hcpcs_price":
                result = await claims_lookup_hcpcs_price(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            # Validate output (only if strict mode enabled)
            if VALIDATION_AVAILABLE and isinstance(result, dict):
                try:
                    validate_tool_output(name, result)
                except ValidationError as ve:
                    # Log output validation error but don't fail the request
                    # (output validation is for dev/test, not production)
                    print(f"Warning: Output validation failed for {name}: {ve.message}", file=sys.stderr)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except ValidationError as ve:
            # Handle validation errors
            error_response = format_error_response(ve)
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
        except Exception as e:
            # Handle other errors
            error_response = format_error_response(e) if VALIDATION_AVAILABLE else {"error": str(e)}
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    async def main():
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    if __name__ == "__main__":
        asyncio.run(main())

else:
    # Fallback: Simple CLI interface for testing
    async def main():
        """Simple CLI interface for testing."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Claims/EDI MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "parse_837", "parse_835", "normalize", "lookup_cpt", "lookup_hcpcs"
        ])
        parser.add_argument("--edi_file", help="Path to EDI file")
        parser.add_argument("--cpt_code", help="CPT code")
        parser.add_argument("--hcpcs_code", help="HCPCS code")
        parser.add_argument("--year", type=int, help="Year for fee schedule")
        parser.add_argument("--locality", help="Locality code")
        parser.add_argument("--line_item", help="Line item JSON (for normalize)")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "parse_837":
                result = await claims_parse_edi_837(edi_file_path=args.edi_file)
            elif args.tool == "parse_835":
                result = await claims_parse_edi_835(edi_file_path=args.edi_file)
            elif args.tool == "normalize":
                if args.line_item:
                    line_item = json.loads(args.line_item)
                else:
                    line_item = {}
                result = await claims_normalize_line_item(line_item=line_item)
            elif args.tool == "lookup_cpt":
                result = await claims_lookup_cpt_price(
                    cpt_code=args.cpt_code,
                    year=args.year,
                    locality=args.locality
                )
            elif args.tool == "lookup_hcpcs":
                result = await claims_lookup_hcpcs_price(
                    hcpcs_code=args.hcpcs_code,
                    year=args.year
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

