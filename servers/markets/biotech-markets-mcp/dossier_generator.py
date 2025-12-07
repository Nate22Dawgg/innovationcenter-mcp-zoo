"""
Biotech company dossier generator.

This module provides functions to generate comprehensive biotech company dossiers
by aggregating data from multiple sources (ClinicalTrials.gov, SEC EDGAR, PubMed).
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import get_cache, build_cache_key
from common.errors import ErrorCode, McpError, map_upstream_error

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from company_aggregator import get_profile, _normalize_company_name
from clinical_trials_client import get_pipeline_drugs, get_company_trials
from sec_edgar_client import (
    search_company_cik,
    search_company_filings,
    get_ipo_filings,
    get_investors_from_filings
)
from pubmed_client import search_company_publications
from yfinance_client import get_timeseries

# Initialize cache
_cache = get_cache()


def _calculate_risk_flags(
    dossier: Dict[str, Any],
    financial_summary: Dict[str, Any],
    pipeline: List[Dict[str, Any]]
) -> List[str]:
    """
    Calculate risk flags based on dossier data.
    
    Args:
        dossier: Dossier data
        financial_summary: Financial summary data
        pipeline: Pipeline data
    
    Returns:
        List of risk flag strings
    """
    risk_flags = []
    
    # Financial risks
    if financial_summary.get("runway_months") is not None:
        if financial_summary["runway_months"] < 6:
            risk_flags.append("Low cash runway (<6 months)")
        elif financial_summary["runway_months"] < 12:
            risk_flags.append("Limited cash runway (<12 months)")
    
    if financial_summary.get("burn_rate") and financial_summary.get("cash_on_hand"):
        if financial_summary["cash_on_hand"] / financial_summary["burn_rate"] < 6:
            risk_flags.append("High burn rate relative to cash")
    
    # Pipeline risks
    if not pipeline or len(pipeline) == 0:
        risk_flags.append("No active pipeline drugs")
    else:
        # Check for late-stage pipeline
        has_late_stage = any(
            drug.get("latest_phase") in ["Phase 3", "NDA", "Approved"]
            for drug in pipeline
        )
        if not has_late_stage:
            risk_flags.append("No late-stage pipeline drugs")
        
        # Check for multiple early-stage only
        early_stage_only = all(
            drug.get("latest_phase") in ["Phase 1", "Phase 2", "Preclinical", "IND"]
            for drug in pipeline
        )
        if early_stage_only and len(pipeline) > 3:
            risk_flags.append("Heavy reliance on early-stage pipeline")
    
    # Trial status risks
    trials_summary = dossier.get("trials_summary", {})
    if trials_summary.get("active_trials", 0) == 0:
        risk_flags.append("No active clinical trials")
    
    # IPO status
    if not financial_summary.get("has_ipo"):
        risk_flags.append("Private company (limited public financial data)")
    
    # Data quality risks
    data_quality = dossier.get("metadata", {}).get("data_quality", {})
    if "error" in str(data_quality.get("sec_edgar", "")).lower():
        risk_flags.append("Limited SEC filing data available")
    
    return risk_flags


def _get_financial_summary(
    company_name: str,
    ticker: Optional[str],
    cik: Optional[str],
    include_financials: bool
) -> Dict[str, Any]:
    """
    Get financial summary from SEC filings and market data.
    
    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        cik: SEC CIK
        include_financials: Whether to include financial data
    
    Returns:
        Financial summary dictionary
    """
    financial_summary = {
        "market_cap": None,
        "revenue": None,
        "cash_on_hand": None,
        "burn_rate": None,
        "runway_months": None,
        "has_ipo": False,
        "ipo_date": None,
        "exchange": None,
        "latest_filing_date": None,
        "filing_count": 0
    }
    
    if not include_financials:
        return financial_summary
    
    try:
        # Get IPO filings
        ipo_filings = get_ipo_filings(company_name)
        if ipo_filings:
            financial_summary["has_ipo"] = True
            # Get the earliest IPO filing date
            ipo_dates = [
                filing.get("filing_date")
                for filing in ipo_filings
                if filing.get("filing_date")
            ]
            if ipo_dates:
                financial_summary["ipo_date"] = min(ipo_dates)
        
        # Get filings count
        filings = search_company_filings(company_name, limit=100)
        financial_summary["filing_count"] = len(filings)
        if filings:
            filing_dates = [
                f.get("filing_date")
                for f in filings
                if f.get("filing_date")
            ]
            if filing_dates:
                financial_summary["latest_filing_date"] = max(filing_dates)
        
        # Try to get market cap from yfinance if ticker available
        if ticker:
            try:
                # Get recent stock info
                ticker_obj = __import__("yfinance").Ticker(ticker)
                info = ticker_obj.info
                
                if "marketCap" in info and info["marketCap"]:
                    financial_summary["market_cap"] = float(info["marketCap"])
                
                if "totalRevenue" in info and info["totalRevenue"]:
                    financial_summary["revenue"] = float(info["totalRevenue"])
                
                if "totalCash" in info and info["totalCash"]:
                    financial_summary["cash_on_hand"] = float(info["totalCash"])
                
                if "exchange" in info:
                    financial_summary["exchange"] = info["exchange"]
            except Exception:
                # yfinance errors are non-critical
                pass
    
    except Exception as e:
        # Map upstream errors but don't fail the whole dossier
        mcp_error = map_upstream_error(e)
        # Log but continue
        pass
    
    return financial_summary


async def generate_biotech_company_dossier(
    company_identifier: Dict[str, Optional[str]],
    include_publications: bool = True,
    include_trials: bool = True,
    include_financials: bool = True,
    max_publications: int = 10,
    max_trials: int = 20
) -> Dict[str, Any]:
    """
    Generate a comprehensive biotech company dossier.
    
    This function orchestrates multiple upstream queries:
    - SEC/financial info
    - Clinical trials / pipeline drugs
    - Publications (PubMed)
    
    Args:
        company_identifier: Dict with ticker, cik, and/or company_name
        include_publications: Whether to include PubMed publications
        include_trials: Whether to include detailed trial information
        include_financials: Whether to include financial information
        max_publications: Maximum number of publications to include
        max_trials: Maximum number of trials to include
    
    Returns:
        BiotechCompanyDossier dictionary
    """
    ticker = company_identifier.get("ticker")
    cik = company_identifier.get("cik")
    company_name = company_identifier.get("company_name")
    
    # Determine company name
    if not company_name:
        if ticker:
            # Try to resolve ticker to company name (simplified - in production would use API)
            company_name = ticker
        elif cik:
            # Try to resolve CIK to company name
            company_name = f"CIK-{cik}"
        else:
            raise McpError(
                code=ErrorCode.BAD_REQUEST,
                message="At least one of ticker, cik, or company_name must be provided",
                details={"company_identifier": company_identifier}
            )
    
    # Build cache key
    cache_key = build_cache_key(
        "biotech-markets-mcp",
        "generate_biotech_company_dossier",
        {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "include_publications": include_publications,
            "include_trials": include_trials,
            "include_financials": include_financials
        }
    )
    
    # Check cache (24 hour TTL for dossiers)
    cached_dossier = _cache.get(cache_key)
    if cached_dossier:
        return cached_dossier
    
    # Normalize company name
    normalized_name = _normalize_company_name(company_name)
    
    # Initialize dossier structure
    dossier = {
        "company_name": company_name,
        "normalized_name": normalized_name,
        "identifiers": {
            "ticker": ticker,
            "cik": None,
            "isin": None,
            "cik_formatted": None
        },
        "pipeline": [],
        "financial_summary": {},
        "risk_flags": [],
        "publications": [],
        "trials_summary": {
            "total_trials": 0,
            "active_trials": 0,
            "completed_trials": 0,
            "phase_distribution": {}
        },
        "investors": [],
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "data_sources": [],
            "data_quality": {}
        }
    }
    
    # Get CIK if not provided
    if not cik:
        try:
            cik = search_company_cik(company_name)
            if cik:
                dossier["identifiers"]["cik"] = cik
                # Format CIK as 10-digit zero-padded
                try:
                    cik_int = int(cik)
                    dossier["identifiers"]["cik_formatted"] = f"{cik_int:010d}"
                except (ValueError, TypeError):
                    dossier["identifiers"]["cik_formatted"] = cik
        except Exception as e:
            dossier["metadata"]["data_quality"]["sec_edgar"] = f"error: {str(e)}"
    
    # Get pipeline drugs
    try:
        pipeline = get_pipeline_drugs(company_name)
        dossier["pipeline"] = pipeline[:50]  # Limit to 50
        dossier["metadata"]["data_sources"].append("ClinicalTrials.gov")
        dossier["metadata"]["data_quality"]["clinical_trials"] = "available"
    except Exception as e:
        dossier["metadata"]["data_quality"]["clinical_trials"] = f"error: {str(e)}"
    
    # Get clinical trials summary
    if include_trials:
        try:
            trials = get_company_trials(company_name, limit=max_trials * 2)
            # get_company_trials returns a list directly
            if isinstance(trials, list):
                dossier["trials_summary"]["total_trials"] = len(trials)
                
                # Count active vs completed
                for trial in trials:
                    status = trial.get("status", "").lower()
                    if "active" in status or "recruiting" in status:
                        dossier["trials_summary"]["active_trials"] += 1
                    elif "completed" in status or "terminated" in status:
                        dossier["trials_summary"]["completed_trials"] += 1
                    
                    # Phase distribution
                    phase = trial.get("phase", "")
                    if phase:
                        dossier["trials_summary"]["phase_distribution"][phase] = \
                            dossier["trials_summary"]["phase_distribution"].get(phase, 0) + 1
        except Exception as e:
            dossier["metadata"]["data_quality"]["trials"] = f"error: {str(e)}"
    
    # Get financial summary
    dossier["financial_summary"] = _get_financial_summary(
        company_name,
        ticker,
        cik or dossier["identifiers"]["cik"],
        include_financials
    )
    if include_financials:
        dossier["metadata"]["data_sources"].append("SEC EDGAR")
        if ticker:
            dossier["metadata"]["data_sources"].append("Yahoo Finance")
    
    # Get publications
    if include_publications:
        try:
            publications = search_company_publications(company_name, limit=max_publications)
            dossier["publications"] = publications[:max_publications]
            dossier["metadata"]["data_sources"].append("PubMed")
            dossier["metadata"]["data_quality"]["pubmed"] = "available"
        except Exception as e:
            dossier["metadata"]["data_quality"]["pubmed"] = f"error: {str(e)}"
    
    # Get investors
    try:
        investors = get_investors_from_filings(company_name)
        dossier["investors"] = investors[:20]  # Limit to 20
    except Exception as e:
        dossier["metadata"]["data_quality"]["investors"] = f"error: {str(e)}"
    
    # Calculate risk flags
    dossier["risk_flags"] = _calculate_risk_flags(
        dossier,
        dossier["financial_summary"],
        dossier["pipeline"]
    )
    
    # Cache the dossier (24 hours)
    _cache.set(cache_key, dossier, ttl_seconds=24 * 60 * 60)
    
    return dossier
