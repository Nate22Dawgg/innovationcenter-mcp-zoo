#!/usr/bin/env python3
"""
Hospital Pricing MCP Server

MCP server for accessing hospital price transparency data via Turquoise Health API.
Provides tools for searching, comparing, and estimating hospital procedure prices.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading and common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from turquoise_client import TurquoiseHealthClient
from config import load_config, HospitalPricesConfig
from common.config import validate_config_or_raise, ConfigValidationError

# Import DCAP for tool discovery (https://github.com/boorich/dcap)
from common.dcap import (
    register_tools_with_dcap,
    ToolMetadata,
    ToolSignature,
    DCAP_ENABLED,
)

# Import CMS fee schedule functions from claims-edi-mcp for macro tool
try:
    # Add claims-edi-mcp to path
    claims_edi_path = Path(__file__).parent.parent.parent / "claims" / "claims-edi-mcp"
    if claims_edi_path.exists():
        sys.path.insert(0, str(claims_edi_path))
        from cms_fee_schedules import lookup_cpt_price, lookup_hcpcs_price
        CMS_FEE_SCHEDULES_AVAILABLE = True
    else:
        CMS_FEE_SCHEDULES_AVAILABLE = False
        print("Warning: claims-edi-mcp not found. CMS fee schedule lookups will be unavailable.", file=sys.stderr)
except ImportError as e:
    CMS_FEE_SCHEDULES_AVAILABLE = False
    print(f"Warning: Could not import CMS fee schedule functions: {e}", file=sys.stderr)

# Import validation utilities
try:
    from common.validation import validate_tool_input, validate_tool_output
    from common.errors import ValidationError, format_error_response
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("Warning: Common validation module not found. Schema validation will be skipped.", file=sys.stderr)

# Import standardized error handling
try:
    from common.errors import (
        McpError,
        map_upstream_error,
        format_error_response,
        ErrorCode,
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    McpError = Exception
    map_upstream_error = None
    format_error_response = None
    ErrorCode = None

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


# Initialize configuration and client
_config: Optional[HospitalPricesConfig] = None
_config_error_payload: Optional[Dict[str, Any]] = None
_client: Optional[TurquoiseHealthClient] = None


def get_config() -> HospitalPricesConfig:
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_client() -> TurquoiseHealthClient:
    """
    Get or create Turquoise Health API client.
    
    Raises:
        ValueError: If TURQUOISE_API_KEY is not set (fail-closed behavior)
    """
    global _client, _config_error_payload
    
    # Check for configuration errors first
    if _config_error_payload:
        error = McpError(
            code=ErrorCode.SERVICE_NOT_CONFIGURED,
            message="Service configuration is incomplete or invalid.",
            details=_config_error_payload.get("issues", [])
        ) if ERROR_HANDLING_AVAILABLE and ErrorCode else None
        if error:
            raise error
        raise ValueError("Service configuration is incomplete or invalid.")
    
    if _client is None:
        config = get_config()
        # Use config's API key
        if not config.turquoise_api_key:
            raise ValueError(
                "TURQUOISE_API_KEY environment variable is required. "
                "The service cannot function without this key. "
                "Please set TURQUOISE_API_KEY in your environment or configuration."
            )
        _client = TurquoiseHealthClient(api_key=config.turquoise_api_key)
    return _client


# Tool implementations
async def hospital_prices_search_procedure(
    cpt_code: str,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    zip_code: Optional[str] = None,
    state: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search for hospital procedure prices by CPT code and location.
    
    Args:
        cpt_code: CPT or HCPCS procedure code (e.g., "99213")
        location: Location string (city, state or zip code)
        radius: Search radius in miles (default: 25)
        zip_code: ZIP code for location-based search
        state: US state code (2 letters)
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with search results containing hospitals and prices
    """
    try:
        client = get_client()
        result = client.search_procedure_price(
            cpt_code=cpt_code,
            location=location,
            radius=radius,
            zip_code=zip_code,
            state=state
        )
        
        # Apply limit if specified
        if limit and limit > 0:
            result["prices"] = result["prices"][:limit]
            result["count"] = len(result["prices"])
        
        return result
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
            "count": 0,
            "total": 0,
            "prices": []
        }


async def hospital_prices_get_rates(
    hospital_id: str,
    cpt_codes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get hospital rate sheet for a specific hospital and optional CPT codes.
    
    Args:
        hospital_id: Turquoise Health hospital identifier
        cpt_codes: Optional list of CPT codes to filter rates
    
    Returns:
        Dictionary with hospital information and rates
    """
    try:
        client = get_client()
        result = client.get_hospital_rates(
            hospital_id=hospital_id,
            cpt_codes=cpt_codes
        )
        return result
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
            "hospital_id": hospital_id,
            "count": 0,
            "prices": []
        }


async def hospital_prices_compare(
    cpt_code: str,
    location: str,
    limit: int = 10,
    zip_code: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare prices for a procedure across multiple facilities.
    
    Args:
        cpt_code: CPT or HCPCS procedure code
        location: Location string (city, state or zip code)
        limit: Maximum number of results to return (default: 10)
        zip_code: ZIP code for location-based search
        state: US state code (2 letters)
    
    Returns:
        Dictionary with ranked list of facilities by price
    """
    try:
        client = get_client()
        result = client.compare_prices(
            cpt_code=cpt_code,
            location=location,
            limit=limit,
            zip_code=zip_code,
            state=state
        )
        return result
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
            "procedure_code": cpt_code,
            "count": 0,
            "comparisons": []
        }


async def hospital_prices_estimate_cash(
    cpt_code: str,
    location: str,
    zip_code: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Estimate cash price range for a procedure in a location.
    
    Args:
        cpt_code: CPT or HCPCS procedure code
        location: Location string (city, state or zip code)
        zip_code: ZIP code for location-based search
        state: US state code (2 letters)
    
    Returns:
        Dictionary with estimated cash price range and statistics
    """
    try:
        client = get_client()
        result = client.estimate_cash_price(
            cpt_code=cpt_code,
            location=location,
            zip_code=zip_code,
            state=state
        )
        return result
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
            "procedure_code": cpt_code,
            "location": location,
            "estimate": {}
        }


async def hospital_prices_estimate_patient_out_of_pocket(
    procedure_codes: List[str],
    hospital_id: str,
    insurance_type: Optional[str] = None,
    deductible: Optional[float] = None,
    coinsurance_percent: Optional[float] = None,
    out_of_pocket_max: Optional[float] = None,
    copay: Optional[float] = None
) -> Dict[str, Any]:
    """
    Estimate patient out-of-pocket costs for procedures at a specific hospital.
    
    This tool uses existing hospital pricing data to compute reasonable estimated
    ranges for patient out-of-pocket costs based on insurance benefit parameters.
    
    Args:
        procedure_codes: List of CPT/HCPCS procedure codes
        hospital_id: Turquoise Health hospital identifier
        insurance_type: Insurance type (e.g., "PPO", "HMO", "self-pay")
        deductible: Annual deductible amount (if applicable)
        coinsurance_percent: Coinsurance percentage (e.g., 20.0 for 20%)
        out_of_pocket_max: Annual out-of-pocket maximum
        copay: Fixed copay amount (if applicable)
    
    Returns:
        Dictionary with estimated OOP costs, assumptions, and risk flags
    """
    try:
        client = get_client()
        
        # Get hospital rates for the procedure codes
        rates_result = client.get_hospital_rates(
            hospital_id=hospital_id,
            cpt_codes=procedure_codes
        )
        
        assumptions = []
        risk_flags = []
        estimated_oop_min = None
        estimated_oop_max = None
        line_item_estimates = []
        
        # Process each procedure code
        prices = rates_result.get("prices", [])
        if not prices:
            risk_flags.append("no_pricing_data_available")
            assumptions.append("No pricing data found for the specified hospital and procedure codes")
        
        total_estimated_min = 0.0
        total_estimated_max = 0.0
        
        for price_info in prices:
            proc_code = price_info.get("procedure_code", "")
            pricing = price_info.get("pricing", {})
            
            # Get insurance price if available, otherwise cash price
            base_price = pricing.get("insurance_price") or pricing.get("cash_price")
            
            if base_price is None:
                risk_flags.append(f"missing_price_for_{proc_code}")
                continue
            
            # Calculate OOP based on insurance type and benefits
            line_oop_min = None
            line_oop_max = None
            line_assumptions = []
            
            if insurance_type and insurance_type.lower() == "self-pay":
                # Self-pay: patient pays full cash price
                line_oop_min = base_price
                line_oop_max = base_price
                line_assumptions.append("Self-pay: patient responsible for full cash price")
            elif insurance_type and insurance_type.lower() in ("ppo", "hmo", "epo"):
                # Insurance: calculate based on deductible, coinsurance, OOP max
                remaining_deductible = deductible or 0.0
                coinsurance = coinsurance_percent or 0.0
                oop_max = out_of_pocket_max or float('inf')
                
                if copay:
                    # Fixed copay
                    line_oop_min = copay
                    line_oop_max = copay
                    line_assumptions.append(f"Fixed copay: ${copay:.2f}")
                else:
                    # Calculate based on deductible and coinsurance
                    if remaining_deductible > 0:
                        # Patient pays deductible portion
                        deductible_portion = min(base_price, remaining_deductible)
                        remaining_after_deductible = max(0, base_price - remaining_deductible)
                        
                        # Coinsurance on remaining amount
                        coinsurance_portion = remaining_after_deductible * (coinsurance / 100.0) if coinsurance > 0 else 0
                        
                        line_oop_min = deductible_portion + coinsurance_portion
                        line_oop_max = min(line_oop_min, oop_max)
                        
                        line_assumptions.append(f"Deductible: ${deductible:.2f}, Coinsurance: {coinsurance}%")
                    else:
                        # Deductible met, only coinsurance applies
                        coinsurance_portion = base_price * (coinsurance / 100.0) if coinsurance > 0 else 0
                        line_oop_min = coinsurance_portion
                        line_oop_max = min(coinsurance_portion, oop_max)
                        line_assumptions.append(f"Coinsurance: {coinsurance}%")
            else:
                # Insurance type unknown or not specified
                risk_flags.append("benefits_unknown")
                # Conservative estimate: assume patient pays 20-40% of insurance price
                line_oop_min = base_price * 0.20
                line_oop_max = base_price * 0.40
                line_assumptions.append("Insurance benefits unknown: estimated 20-40% of billed amount")
            
            if line_oop_min is not None:
                total_estimated_min += line_oop_min
                total_estimated_max += line_oop_max or line_oop_min
                
                line_item_estimates.append({
                    "procedure_code": proc_code,
                    "estimated_oop_min": round(line_oop_min, 2),
                    "estimated_oop_max": round(line_oop_max or line_oop_min, 2),
                    "base_price": round(base_price, 2),
                    "assumptions": line_assumptions
                })
        
        estimated_oop_min = round(total_estimated_min, 2) if total_estimated_min > 0 else None
        estimated_oop_max = round(total_estimated_max, 2) if total_estimated_max > 0 else None
        
        # Add general assumptions
        if not insurance_type:
            assumptions.append("Insurance type not specified: estimates may vary significantly")
            risk_flags.append("insurance_type_unknown")
        
        if deductible is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Deductible not provided: estimates assume deductible already met or not applicable")
        
        if coinsurance_percent is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Coinsurance not provided: estimates may be inaccurate")
            risk_flags.append("coinsurance_unknown")
        
        if out_of_pocket_max is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Out-of-pocket maximum not provided: estimates may exceed actual OOP max")
            risk_flags.append("oop_max_unknown")
        
        # Check for out-of-network risk
        # Note: This is a simplified check - real implementation would verify network status
        assumptions.append("Network status not verified: patient may be out-of-network, increasing costs")
        risk_flags.append("out_of_network_risk")
        
        return {
            "hospital_id": hospital_id,
            "procedure_codes": procedure_codes,
            "estimated_oop_min": estimated_oop_min,
            "estimated_oop_max": estimated_oop_max,
            "assumptions": assumptions,
            "risk_flags": list(set(risk_flags)),  # Remove duplicates
            "line_item_estimates": line_item_estimates,
            "insurance_type": insurance_type or "unknown",
            "data_source": "Turquoise Health API"
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
            "hospital_id": hospital_id,
            "procedure_codes": procedure_codes,
            "estimated_oop_min": None,
            "estimated_oop_max": None,
            "assumptions": [],
            "risk_flags": ["calculation_error"]
        }


async def patient_oop_estimate_macro(
    procedure_codes: List[str],
    patient_demographics: Optional[Dict[str, Any]] = None,
    facility: Optional[Dict[str, Any]] = None,
    insurance_plan: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Macro tool: Estimate patient out-of-pocket costs using both hospital pricing 
    and CMS fee schedule data.
    
    This tool combines:
    - Hospital pricing data from Turquoise Health API
    - CMS fee schedule data from claims-edi-mcp
    - Insurance benefit parameters to calculate OOP estimates
    
    Args:
        procedure_codes: List of CPT/HCPCS procedure codes
        patient_demographics: Optional patient demographics (age, zip_code, state)
        facility: Optional facility identifier or location (hospital_id or address info)
        insurance_plan: Optional insurance plan parameters (type, deductible, coinsurance, etc.)
    
    Returns:
        Dictionary with comprehensive OOP estimates, price components, assumptions, and risk flags
    """
    try:
        client = get_client()
        assumptions = []
        risk_flags = []
        data_sources = []
        procedure_summary = []
        line_item_estimates = []
        
        # Extract parameters
        insurance_type = insurance_plan.get("insurance_type") if insurance_plan else None
        deductible = insurance_plan.get("deductible") if insurance_plan else None
        deductible_met = insurance_plan.get("deductible_met", False) if insurance_plan else False
        coinsurance_percent = insurance_plan.get("coinsurance_percent") if insurance_plan else None
        copay = insurance_plan.get("copay") if insurance_plan else None
        out_of_pocket_max = insurance_plan.get("out_of_pocket_max") if insurance_plan else None
        
        # Get facility identifier
        hospital_id = None
        if facility:
            hospital_id = facility.get("hospital_id")
            if not hospital_id and facility.get("zip_code"):
                # Could search for hospital by location, but for now require hospital_id
                risk_flags.append("facility_location_search_not_implemented")
        
        if not hospital_id:
            risk_flags.append("hospital_id_missing")
            assumptions.append("Hospital identifier not provided: using geographic averages")
        
        # Get patient location for geographic context
        patient_zip = None
        patient_state = None
        if patient_demographics:
            patient_zip = patient_demographics.get("zip_code")
            patient_state = patient_demographics.get("state")
        
        # Determine locality for CMS fee schedule (use state if available)
        locality = None
        if patient_state:
            # CMS uses locality codes, but for simplicity we'll use "00" (national average)
            # In production, this could map state to locality code
            locality = "00"
        
        total_oop_min = 0.0
        total_oop_max = 0.0
        total_oop_likely = 0.0
        
        hospital_pricing_data = {}
        cms_fee_schedule_data = {}
        
        # Step 1: Get hospital pricing data
        if hospital_id:
            try:
                rates_result = client.get_hospital_rates(
                    hospital_id=hospital_id,
                    cpt_codes=procedure_codes
                )
                hospital_pricing_data = rates_result
                data_sources.append("Turquoise Health API")
            except Exception as e:
                risk_flags.append("hospital_pricing_unavailable")
                assumptions.append(f"Hospital pricing data unavailable: {str(e)}")
        else:
            risk_flags.append("hospital_pricing_skipped_no_facility")
            assumptions.append("Hospital pricing skipped: no facility identifier provided")
        
        # Step 2: Get CMS fee schedule data for each procedure code
        for proc_code in procedure_codes:
            # Determine if CPT or HCPCS
            is_cpt = proc_code.isdigit() and len(proc_code) == 5
            is_hcpcs = not is_cpt and len(proc_code) == 5 and proc_code[0].isalpha()
            
            code_type = "CPT" if is_cpt else "HCPCS" if is_hcpcs else "UNKNOWN"
            
            cms_price_data = None
            description = ""
            
            if CMS_FEE_SCHEDULES_AVAILABLE:
                try:
                    if is_cpt:
                        cms_result = lookup_cpt_price(
                            cpt_code=proc_code,
                            year=None,  # Use current year
                            locality=locality
                        )
                        if cms_result.get("status") == "found":
                            cms_price_data = {
                                "facility_price": cms_result.get("facility_price"),
                                "non_facility_price": cms_result.get("non_facility_price"),
                                "description": cms_result.get("description", "")
                            }
                            description = cms_result.get("description", "")
                            cms_fee_schedule_data[proc_code] = cms_price_data
                            if "CMS Fee Schedule" not in data_sources:
                                data_sources.append("CMS Fee Schedule")
                    elif is_hcpcs:
                        cms_result = lookup_hcpcs_price(
                            hcpcs_code=proc_code,
                            year=None
                        )
                        if cms_result.get("status") == "found":
                            cms_price_data = {
                                "price": cms_result.get("price"),
                                "description": cms_result.get("description", "")
                            }
                            description = cms_result.get("description", "")
                            cms_fee_schedule_data[proc_code] = cms_price_data
                            if "CMS Fee Schedule" not in data_sources:
                                data_sources.append("CMS Fee Schedule")
                except Exception as e:
                    risk_flags.append(f"cms_lookup_failed_{proc_code}")
                    assumptions.append(f"CMS fee schedule lookup failed for {proc_code}: {str(e)}")
            
            if not cms_price_data:
                risk_flags.append(f"cms_data_missing_{proc_code}")
            
            # Step 3: Get hospital pricing for this procedure
            hospital_price_data = None
            if hospital_pricing_data and "prices" in hospital_pricing_data:
                for price_info in hospital_pricing_data.get("prices", []):
                    if price_info.get("procedure_code") == proc_code:
                        hospital_price_data = price_info.get("pricing", {})
                        break
            
            # Step 4: Determine base price (prefer hospital negotiated rate, fallback to CMS)
            base_price = None
            price_source = None
            
            if hospital_price_data:
                # Prefer negotiated insurance rate, then cash price
                base_price = hospital_price_data.get("insurance_price") or hospital_price_data.get("cash_price")
                if base_price:
                    price_source = "hospital_pricing"
            
            if not base_price and cms_price_data:
                # Use CMS facility price (for hospital setting)
                if "facility_price" in cms_price_data:
                    base_price = cms_price_data["facility_price"]
                elif "price" in cms_price_data:
                    base_price = cms_price_data["price"]
                if base_price:
                    price_source = "cms_fee_schedule"
            
            if not base_price:
                risk_flags.append(f"no_pricing_data_{proc_code}")
                assumptions.append(f"No pricing data available for procedure {proc_code}")
                continue
            
            # Step 5: Calculate OOP based on insurance benefits
            line_oop_min = None
            line_oop_max = None
            line_oop_likely = None
            line_assumptions = []
            
            if insurance_type and insurance_type.lower() == "self-pay":
                # Self-pay: patient pays full cash price
                cash_price = hospital_price_data.get("cash_price") if hospital_price_data else base_price
                line_oop_min = cash_price
                line_oop_max = cash_price
                line_oop_likely = cash_price
                line_assumptions.append("Self-pay: patient responsible for full cash price")
            elif insurance_type and insurance_type.lower() in ("ppo", "hmo", "epo", "pos", "medicare", "medicaid"):
                # Insurance: calculate based on deductible, coinsurance, OOP max
                remaining_deductible = deductible if deductible and not deductible_met else 0.0
                coinsurance = coinsurance_percent or 0.0
                oop_max = out_of_pocket_max or float('inf')
                
                if copay:
                    # Fixed copay
                    line_oop_min = copay
                    line_oop_max = copay
                    line_oop_likely = copay
                    line_assumptions.append(f"Fixed copay: ${copay:.2f}")
                else:
                    # Calculate based on deductible and coinsurance
                    if remaining_deductible > 0:
                        # Patient pays deductible portion
                        deductible_portion = min(base_price, remaining_deductible)
                        remaining_after_deductible = max(0, base_price - remaining_deductible)
                        
                        # Coinsurance on remaining amount
                        coinsurance_portion = remaining_after_deductible * (coinsurance / 100.0) if coinsurance > 0 else 0
                        
                        line_oop_min = deductible_portion + coinsurance_portion
                        line_oop_max = min(line_oop_min, oop_max)
                        line_oop_likely = line_oop_min  # For deductible phase, min = likely
                        
                        line_assumptions.append(f"Deductible: ${deductible:.2f} remaining, Coinsurance: {coinsurance}%")
                    else:
                        # Deductible met, only coinsurance applies
                        coinsurance_portion = base_price * (coinsurance / 100.0) if coinsurance > 0 else 0
                        line_oop_min = coinsurance_portion
                        line_oop_max = min(coinsurance_portion, oop_max)
                        line_oop_likely = coinsurance_portion
                        line_assumptions.append(f"Coinsurance: {coinsurance}%")
            else:
                # Insurance type unknown or not specified
                risk_flags.append("benefits_unknown")
                # Conservative estimate: assume patient pays 20-40% of insurance price
                line_oop_min = base_price * 0.20
                line_oop_max = base_price * 0.40
                line_oop_likely = base_price * 0.30
                line_assumptions.append("Insurance benefits unknown: estimated 20-40% of billed amount")
            
            if line_oop_min is not None:
                total_oop_min += line_oop_min
                total_oop_max += line_oop_max or line_oop_min
                total_oop_likely += line_oop_likely or ((line_oop_min + (line_oop_max or line_oop_min)) / 2)
                
                line_item_estimates.append({
                    "procedure_code": proc_code,
                    "estimated_oop_min": round(line_oop_min, 2),
                    "estimated_oop_max": round(line_oop_max or line_oop_min, 2),
                    "estimated_oop_likely": round(line_oop_likely or ((line_oop_min + (line_oop_max or line_oop_min)) / 2), 2),
                    "base_price": round(base_price, 2),
                    "price_source": price_source or "unknown",
                    "assumptions": line_assumptions
                })
            
            # Add to procedure summary
            procedure_summary.append({
                "procedure_code": proc_code,
                "description": description or f"Procedure {proc_code}",
                "code_type": code_type
            })
        
        # Aggregate price components
        hospital_cash_min = None
        hospital_cash_max = None
        hospital_negotiated_min = None
        hospital_negotiated_max = None
        
        if hospital_pricing_data and "prices" in hospital_pricing_data:
            cash_prices = []
            negotiated_prices = []
            for price_info in hospital_pricing_data.get("prices", []):
                pricing = price_info.get("pricing", {})
                if pricing.get("cash_price"):
                    cash_prices.append(pricing["cash_price"])
                if pricing.get("insurance_price"):
                    negotiated_prices.append(pricing["insurance_price"])
            
            if cash_prices:
                hospital_cash_min = min(cash_prices)
                hospital_cash_max = max(cash_prices)
            if negotiated_prices:
                hospital_negotiated_min = min(negotiated_prices)
                hospital_negotiated_max = max(negotiated_prices)
        
        # Calculate allowed amount range (typically 80-120% of CMS fee schedule or negotiated rate)
        allowed_min = None
        allowed_max = None
        allowed_likely = None
        
        if hospital_negotiated_min and hospital_negotiated_max:
            # Use negotiated rates as allowed amounts
            allowed_min = hospital_negotiated_min * 0.95  # 5% below min
            allowed_max = hospital_negotiated_max * 1.05   # 5% above max
            allowed_likely = (hospital_negotiated_min + hospital_negotiated_max) / 2
        elif cms_fee_schedule_data:
            # Fallback to CMS fee schedule
            cms_prices = []
            for proc_code in procedure_codes:
                if proc_code in cms_fee_schedule_data:
                    price = cms_fee_schedule_data[proc_code].get("facility_price") or cms_fee_schedule_data[proc_code].get("price")
                    if price:
                        cms_prices.append(price)
            if cms_prices:
                allowed_min = min(cms_prices) * 0.90
                allowed_max = max(cms_prices) * 1.10
                allowed_likely = sum(cms_prices) / len(cms_prices)
        
        # Calculate plan pay range (allowed amount - patient responsibility)
        plan_pay_min = None
        plan_pay_max = None
        plan_pay_likely = None
        
        if allowed_min and total_oop_max:
            plan_pay_min = max(0, allowed_min - total_oop_max)
            plan_pay_max = max(0, (allowed_max or allowed_min) - total_oop_min)
            plan_pay_likely = max(0, (allowed_likely or allowed_min) - total_oop_likely)
        
        # Add general assumptions
        if not insurance_type:
            assumptions.append("Insurance type not specified: estimates may vary significantly")
            risk_flags.append("insurance_type_unknown")
        
        if deductible is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Deductible not provided: estimates assume deductible already met or not applicable")
        
        if coinsurance_percent is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Coinsurance not provided: estimates may be inaccurate")
            risk_flags.append("coinsurance_unknown")
        
        if out_of_pocket_max is None and insurance_type and insurance_type.lower() != "self-pay":
            assumptions.append("Out-of-pocket maximum not provided: estimates may exceed actual OOP max")
            risk_flags.append("oop_max_unknown")
        
        # Check for out-of-network risk
        assumptions.append("Network status not verified: patient may be out-of-network, increasing costs")
        risk_flags.append("out_of_network_risk")
        
        if not data_sources:
            data_sources.append("Limited data available")
            risk_flags.append("insufficient_data")
        
        return {
            "procedure_summary": procedure_summary,
            "price_components": {
                "hospital_pricing": {
                    "cash_price_min": round(hospital_cash_min, 2) if hospital_cash_min else None,
                    "cash_price_max": round(hospital_cash_max, 2) if hospital_cash_max else None,
                    "negotiated_rate_min": round(hospital_negotiated_min, 2) if hospital_negotiated_min else None,
                    "negotiated_rate_max": round(hospital_negotiated_max, 2) if hospital_negotiated_max else None,
                    "data_available": bool(hospital_pricing_data and "prices" in hospital_pricing_data)
                },
                "cms_fee_schedule": {
                    "facility_price": None,  # Would aggregate if needed
                    "non_facility_price": None,  # Would aggregate if needed
                    "data_available": CMS_FEE_SCHEDULES_AVAILABLE and not any(
                        "cms_data_missing" in str(flag) or "cms_lookup_failed" in str(flag) for flag in risk_flags
                    )
                },
                "allowed_amount_range": {
                    "min": round(allowed_min, 2) if allowed_min else None,
                    "max": round(allowed_max, 2) if allowed_max else None,
                    "likely": round(allowed_likely, 2) if allowed_likely else None
                },
                "plan_pay_range": {
                    "min": round(plan_pay_min, 2) if plan_pay_min else None,
                    "max": round(plan_pay_max, 2) if plan_pay_max else None,
                    "likely": round(plan_pay_likely, 2) if plan_pay_likely else None
                },
                "patient_pay_range": {
                    "min": round(total_oop_min, 2) if total_oop_min > 0 else None,
                    "max": round(total_oop_max, 2) if total_oop_max > 0 else None,
                    "likely": round(total_oop_likely, 2) if total_oop_likely > 0 else None
                }
            },
            "assumptions": assumptions,
            "risk_flags": list(set(risk_flags)),  # Remove duplicates
            "line_item_estimates": line_item_estimates,
            "total_estimated_oop": {
                "min": round(total_oop_min, 2) if total_oop_min > 0 else None,
                "max": round(total_oop_max, 2) if total_oop_max > 0 else None,
                "likely": round(total_oop_likely, 2) if total_oop_likely > 0 else None
            },
            "data_sources": data_sources,
            "facility_id": hospital_id,
            "insurance_type": insurance_type or "unknown"
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
            "procedure_summary": [],
            "price_components": {},
            "assumptions": [],
            "risk_flags": ["calculation_error"],
            "line_item_estimates": [],
            "total_estimated_oop": {"min": None, "max": None, "likely": None},
            "data_sources": [],
            "facility_id": None,
            "insurance_type": "unknown"
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("hospital-pricing-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="hospital_prices_search_procedure",
                description="Search for hospital procedure prices by CPT code and location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code (e.g., '99213')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in miles (default: 25)",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 200
                        }
                    },
                    "required": ["cpt_code"]
                }
            ),
            Tool(
                name="hospital_prices_get_rates",
                description="Get hospital rate sheet for a specific hospital and optional CPT codes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hospital_id": {
                            "type": "string",
                            "description": "Turquoise Health hospital identifier"
                        },
                        "cpt_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of CPT codes to filter rates"
                        }
                    },
                    "required": ["hospital_id"]
                }
            ),
            Tool(
                name="hospital_prices_compare",
                description="Compare prices for a procedure across multiple facilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        }
                    },
                    "required": ["cpt_code", "location"]
                }
            ),
            Tool(
                name="hospital_prices_estimate_cash",
                description="Estimate cash price range for a procedure in a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT or HCPCS procedure code"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location string (city, state or zip code)"
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "ZIP code for location-based search"
                        },
                        "state": {
                            "type": "string",
                            "description": "US state code (2 letters)"
                        }
                    },
                    "required": ["cpt_code", "location"]
                }
            ),
            Tool(
                name="hospital_prices_estimate_patient_out_of_pocket",
                description="Estimate patient out-of-pocket costs for procedures at a specific hospital based on insurance benefits",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "procedure_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of CPT/HCPCS procedure codes"
                        },
                        "hospital_id": {
                            "type": "string",
                            "description": "Turquoise Health hospital identifier"
                        },
                        "insurance_type": {
                            "type": "string",
                            "description": "Insurance type (e.g., 'PPO', 'HMO', 'self-pay')",
                            "enum": ["PPO", "HMO", "EPO", "self-pay"]
                        },
                        "deductible": {
                            "type": "number",
                            "description": "Annual deductible amount (if applicable)",
                            "minimum": 0
                        },
                        "coinsurance_percent": {
                            "type": "number",
                            "description": "Coinsurance percentage (e.g., 20.0 for 20%)",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "out_of_pocket_max": {
                            "type": "number",
                            "description": "Annual out-of-pocket maximum",
                            "minimum": 0
                        },
                        "copay": {
                            "type": "number",
                            "description": "Fixed copay amount (if applicable)",
                            "minimum": 0
                        }
                    },
                    "required": ["procedure_codes", "hospital_id"]
                }
            ),
            Tool(
                name="patient_oop_estimate_macro",
                description="Macro tool: Estimate patient out-of-pocket costs using both hospital pricing and CMS fee schedule data. Combines Turquoise Health API pricing with CMS fee schedules for comprehensive OOP estimates.",
                inputSchema=load_schema("schemas/patient_oop_estimate.json")
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
            if name == "hospital_prices_search_procedure":
                result = await hospital_prices_search_procedure(**arguments)
            elif name == "hospital_prices_get_rates":
                result = await hospital_prices_get_rates(**arguments)
            elif name == "hospital_prices_compare":
                result = await hospital_prices_compare(**arguments)
            elif name == "hospital_prices_estimate_cash":
                result = await hospital_prices_estimate_cash(**arguments)
            elif name == "hospital_prices_estimate_patient_out_of_pocket":
                result = await hospital_prices_estimate_patient_out_of_pocket(**arguments)
            elif name == "patient_oop_estimate_macro":
                result = await patient_oop_estimate_macro(**arguments)
            else:
                # Unknown tool - return structured error
                if ERROR_HANDLING_AVAILABLE and ErrorCode:
                    from common.errors import McpError
                    error = McpError(
                        code=ErrorCode.BAD_REQUEST,
                        message=f"Unknown tool: {name}",
                        details={"tool_name": name}
                    )
                    result = format_error_response(error)
                else:
                    result = {"error": {"code": "BAD_REQUEST", "message": f"Unknown tool: {name}"}}
            
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
            if VALIDATION_AVAILABLE:
                error_response = format_error_response(ve)
            else:
                error_response = {"error": {"code": "VALIDATION_ERROR", "message": str(ve)}}
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
        except Exception as e:
            # Catch any unexpected errors and return structured response
            if ERROR_HANDLING_AVAILABLE and map_upstream_error:
                mcp_error = map_upstream_error(e)
                error_response = format_error_response(mcp_error)
            else:
                error_response = {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(e) or "An unexpected error occurred"
                    }
                }
            return [TextContent(
                type="text",
                text=json.dumps(error_response, indent=2)
            )]
    
    # DCAP v3.1 Tool Metadata for semantic discovery
    DCAP_TOOLS = [
        ToolMetadata(
            name="hospital_prices_search_procedure",
            description="Search for hospital procedure prices by CPT code and location",
            triggers=["hospital prices", "procedure cost", "CPT price", "medical prices"],
            signature=ToolSignature(input="ProcedureQuery", output="Maybe<PriceList>", cost=0)
        ),
        ToolMetadata(
            name="hospital_prices_get_rates",
            description="Get hospital rate sheet for a specific hospital",
            triggers=["hospital rates", "rate sheet", "hospital pricing"],
            signature=ToolSignature(input="HospitalQuery", output="Maybe<RateSheet>", cost=0)
        ),
        ToolMetadata(
            name="hospital_prices_compare",
            description="Compare prices for a procedure across multiple facilities",
            triggers=["compare prices", "price comparison", "cheapest hospital"],
            signature=ToolSignature(input="CompareQuery", output="Maybe<PriceComparison>", cost=0)
        ),
        ToolMetadata(
            name="hospital_prices_estimate_cash",
            description="Estimate cash price range for a procedure in a location",
            triggers=["cash price", "self-pay price", "uninsured cost"],
            signature=ToolSignature(input="EstimateQuery", output="Maybe<CashEstimate>", cost=0)
        ),
        ToolMetadata(
            name="hospital_prices_estimate_patient_out_of_pocket",
            description="Estimate patient out-of-pocket costs based on insurance benefits",
            triggers=["out-of-pocket", "OOP estimate", "patient cost", "insurance cost"],
            signature=ToolSignature(input="OOPQuery", output="Maybe<OOPEstimate>", cost=0)
        ),
        ToolMetadata(
            name="patient_oop_estimate_macro",
            description="Comprehensive OOP estimate using hospital pricing and CMS fee schedules",
            triggers=["full OOP estimate", "comprehensive cost", "CMS pricing"],
            signature=ToolSignature(input="MacroQuery", output="Maybe<ComprehensiveOOP>", cost=0)
        ),
    ]

    async def main():
        """Run the MCP server."""
        global _config_error_payload
        
        # Load and validate configuration (fail-fast by default)
        try:
            config = load_config()
            is_valid, error_payload = validate_config_or_raise(config, fail_fast=True)
            if not is_valid:
                _config_error_payload = error_payload
        except ConfigValidationError as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Register tools with DCAP for dynamic discovery
        if DCAP_ENABLED:
            registered = register_tools_with_dcap(
                server_id="hospital-prices-mcp",
                tools=DCAP_TOOLS,
                base_command="python servers/pricing/hospital-prices-mcp/server.py"
            )
            print(f"DCAP: Registered {registered} tools with relay", file=sys.stderr)
        
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
        
        parser = argparse.ArgumentParser(description="Hospital Pricing MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "search", "get_rates", "compare", "estimate"
        ])
        parser.add_argument("--cpt_code", help="CPT code")
        parser.add_argument("--location", help="Location")
        parser.add_argument("--hospital_id", help="Hospital ID")
        parser.add_argument("--radius", type=int, help="Radius in miles")
        parser.add_argument("--limit", type=int, default=10, help="Result limit")
        parser.add_argument("--zip_code", help="ZIP code")
        parser.add_argument("--state", help="State code")
        parser.add_argument("--cpt_codes", nargs="+", help="List of CPT codes")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "search":
                result = await hospital_prices_search_procedure(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    radius=args.radius,
                    zip_code=args.zip_code,
                    state=args.state,
                    limit=args.limit
                )
            elif args.tool == "get_rates":
                result = await hospital_prices_get_rates(
                    hospital_id=args.hospital_id,
                    cpt_codes=args.cpt_codes
                )
            elif args.tool == "compare":
                result = await hospital_prices_compare(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    limit=args.limit,
                    zip_code=args.zip_code,
                    state=args.state
                )
            elif args.tool == "estimate":
                result = await hospital_prices_estimate_cash(
                    cpt_code=args.cpt_code,
                    location=args.location,
                    zip_code=args.zip_code,
                    state=args.state
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

