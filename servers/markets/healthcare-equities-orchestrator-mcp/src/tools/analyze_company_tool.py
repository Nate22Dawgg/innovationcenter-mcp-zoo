"""
Tool for analyzing companies across markets and clinical domains.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.clients.mcp_orchestrator_client import MCPOrchestratorClient
from common.errors import ErrorCode, format_error_response, map_upstream_error, ValidationError
from common.logging import get_logger
from common.identifiers import normalize_ticker, normalize_cik

logger = get_logger(__name__)


def analyze_company_across_markets_and_clinical(
    client: Optional[MCPOrchestratorClient],
    config_error_payload: Optional[Dict[str, Any]] = None,
    identifier: Dict[str, Any] = None,
    include_financials: bool = True,
    include_clinical: bool = True,
    include_sec: bool = True
) -> Dict[str, Any]:
    """
    Analyze a company across markets and clinical domains.
    
    This tool orchestrates calls to multiple MCP servers:
    - biotech-markets-mcp: For company profiles, financials, and pipeline
    - sec-edgar-mcp: For SEC filings and company information
    - clinical-trials-mcp or biomcp-mcp: For clinical trial data
    
    Args:
        client: Initialized orchestrator client instance
        config_error_payload: Error payload if configuration is invalid
        identifier: Company identifier (must include at least one of: ticker, company_name, cik)
        include_financials: Whether to include financial data
        include_clinical: Whether to include clinical trial data
        include_sec: Whether to include SEC filing data
    
    Returns:
        Dictionary with combined analysis across all domains
    """
    # Check if service is configured
    if config_error_payload is not None:
        logger.warning("Tool called but service is not configured")
        return config_error_payload
    
    if client is None:
        return {
            "error": {
                "code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
                "message": "Service is not configured"
            }
        }
    
    # Input validation
    if not identifier:
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": "identifier is required",
                "details": {"field": "identifier", "value": identifier}
            }
        }
    
    # Normalize and validate identifiers
    ticker_raw = identifier.get("ticker")
    company_name = identifier.get("company_name")
    cik_raw = identifier.get("cik")
    
    # Normalize identifiers
    ticker = normalize_ticker(ticker_raw) if ticker_raw else None
    cik = normalize_cik(cik_raw) if cik_raw else None
    
    if not ticker and not company_name and not cik:
        return {
            "error": {
                "code": ErrorCode.BAD_REQUEST.value,
                "message": "At least one of ticker, company_name, or cik must be provided in identifier",
                "details": {"identifier": identifier}
            }
        }
    
    try:
        # Build normalized identifier dict
        normalized_identifier = {}
        if company_name:
            normalized_identifier["company_name"] = company_name
        if ticker:
            normalized_identifier["ticker"] = ticker
        if cik:
            normalized_identifier["cik"] = cik
        
        # Call the orchestrator client
        logger.info(f"Analyzing company with identifier: {normalized_identifier}")
        result = client.analyze_company(
            identifier=normalized_identifier,
            include_financials=include_financials,
            include_clinical=include_clinical,
            include_sec=include_sec
        )
        
        logger.info("Company analysis completed successfully")
        return result
        
    except Exception as e:
        # Map upstream errors to standardized MCP errors
        mcp_error = map_upstream_error(e)
        logger.error(f"Company analysis failed: {mcp_error.message}")
        
        # Return structured error response
        return format_error_response(
            error=mcp_error,
            include_traceback=False
        )["error"]
