"""
SEC EDGAR API client for biotech company filings and financial data.

Provides functions to search company filings, extract financial information,
and find IPO filings (S-1 forms).
"""

import time
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.cache import get_cache, build_cache_key
from common.http import get, CallOptions, call_upstream
from common.errors import ApiError, ErrorCode, map_upstream_error
from common.identifiers import normalize_cik, normalize_ticker

# SEC EDGAR API base URL
SEC_BASE_URL = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# Required User-Agent header (SEC requirement)
USER_AGENT = "MCP Biotech Markets Server (contact@example.com)"

# Initialize cache
_cache = get_cache()


def _get_headers() -> Dict[str, str]:
    """Get headers with required User-Agent for SEC API."""
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }


def _rate_limit():
    """Rate limit: SEC allows 10 requests per second."""
    time.sleep(0.11)  # Slightly more than 0.1s to be safe


def search_company_cik(company_name: str) -> Optional[str]:
    """
    Search for company CIK (Central Index Key) by name.
    
    Args:
        company_name: Company name to search for
    
    Returns:
        CIK string (10-digit zero-padded) or None if not found
    """
    # Check cache first (24 hour TTL for CIK lookups)
    cache_key = build_cache_key(
        "biotech-markets-mcp",
        "search_company_cik",
        {"company_name": company_name}
    )
    cached_result = _cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    _rate_limit()
    
    try:
        # Get company tickers JSON
        response = get(
            url=COMPANY_TICKERS_URL,
            upstream="sec_edgar",
            timeout=10.0,
            headers=_get_headers()
        )
        data = response.json()
        
        company_name_lower = company_name.lower()
        
        # Search through tickers
        for ticker_data in data.values():
            if isinstance(ticker_data, dict):
                title = ticker_data.get("title", "").lower()
                if company_name_lower in title or title in company_name_lower:
                    cik = str(ticker_data.get("cik_str", ""))
                    if cik:
                        result = normalize_cik(cik)  # Zero-pad to 10 digits
                        # Cache result (24 hours)
                        _cache.set(cache_key, result, ttl_seconds=24 * 60 * 60)
                        return result
        
        # Cache None result too (shorter TTL - 1 hour)
        _cache.set(cache_key, None, ttl_seconds=60 * 60)
        return None
    except ApiError as e:
        # Re-raise ApiError as-is (already standardized)
        raise
    except Exception as e:
        # Map unexpected errors to structured errors
        mapped_error = map_upstream_error(e)
        if mapped_error:
            raise mapped_error
        print(f"Error searching for CIK: {e}")
        return None


def search_company_filings(company_name: str, form_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for company filings by name and optional form type.
    
    Args:
        company_name: Company name
        form_type: Optional form type filter (e.g., "S-1", "10-Q", "10-K")
        limit: Maximum number of filings to return
    
    Returns:
        List of filing dictionaries
    """
    cik = search_company_cik(company_name)
    if not cik:
        return []
    
    return get_filings_by_cik(cik, form_type=form_type, limit=limit)


def get_filings_by_cik(cik: str, form_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get filings for a company by CIK.
    
    Args:
        cik: Company CIK (10-digit zero-padded)
        form_type: Optional form type filter
        limit: Maximum number of filings
    
    Returns:
        List of filing dictionaries
    """
    # Check cache first (12 hour TTL for filings)
    cache_key = build_cache_key(
        "biotech-markets-mcp",
        "get_filings_by_cik",
        {"cik": cik, "form_type": form_type, "limit": limit}
    )
    cached_result = _cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    _rate_limit()
    
    try:
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": form_type if form_type else "",
            "count": limit,
            "output": "json"
        }
        
        response = get(
            url=CIK_LOOKUP_URL,
            upstream="sec_edgar",
            timeout=10.0,
            headers=_get_headers(),
            params=params
        )
        
        # SEC returns HTML or JSON depending on params
        # Try to parse as JSON first
        try:
            data = response.json()
            filings = data.get("filings", {}).get("recent", {})
            
            forms = filings.get("form", [])
            dates = filings.get("reportDate", [])
            descriptions = filings.get("description", [])
            accession_numbers = filings.get("accessionNumber", [])
            
            result = []
            for i in range(min(len(forms), limit)):
                if form_type and forms[i] != form_type:
                    continue
                
                result.append({
                    "form_type": forms[i],
                    "filing_date": dates[i] if i < len(dates) else "",
                    "description": descriptions[i] if i < len(descriptions) else "",
                    "accession_number": accession_numbers[i] if i < len(accession_numbers) else "",
                    "cik": cik
                })
            
            # Cache result (12 hours)
            _cache.set(cache_key, result, ttl_seconds=12 * 60 * 60)
            return result
        except ValueError:
            # If not JSON, parse HTML (simplified)
            # For now, return empty list - full HTML parsing would be complex
            result = []
            _cache.set(cache_key, result, ttl_seconds=12 * 60 * 60)
            return result
    except ApiError as e:
        # Re-raise ApiError as-is (already standardized)
        raise
    except Exception as e:
        # Map unexpected errors to structured errors
        mapped_error = map_upstream_error(e)
        if mapped_error:
            raise mapped_error
        print(f"Error getting filings: {e}")
        return []


def get_filing_content(cik: str, accession_number: str) -> Optional[Dict[str, Any]]:
    """
    Get content of a specific filing.
    
    Args:
        cik: Company CIK
        accession_number: Filing accession number (e.g., "0001234567-24-000001")
    
    Returns:
        Dictionary with filing content and metadata
    """
    # Check cache first (24 hour TTL for filing content)
    cache_key = build_cache_key(
        "biotech-markets-mcp",
        "get_filing_content",
        {"cik": cik, "accession_number": accession_number}
    )
    cached_result = _cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    _rate_limit()
    
    # Convert accession number to URL format
    # Format: 0001234567-24-000001 -> 0001234567/24-000001
    parts = accession_number.split("-")
    if len(parts) >= 3:
        url_path = f"{parts[0]}/{parts[1]}-{parts[2]}"
    else:
        url_path = accession_number
    
    try:
        url = f"{SEC_BASE_URL}/files/data/{cik}/{accession_number}/{accession_number}.txt"
        
        response = get(
            url=url,
            upstream="sec_edgar",
            timeout=30.0,
            headers=_get_headers()
        )
        
        content = response.text
        
        result = {
            "cik": cik,
            "accession_number": accession_number,
            "content": content[:10000],  # Limit content size
            "content_length": len(content),
            "url": url
        }
        
        # Cache result (24 hours)
        _cache.set(cache_key, result, ttl_seconds=24 * 60 * 60)
        return result
    except ApiError as e:
        # Re-raise ApiError as-is (already standardized)
        raise
    except Exception as e:
        # Map unexpected errors to structured errors
        mapped_error = map_upstream_error(e)
        if mapped_error:
            raise mapped_error
        print(f"Error getting filing content: {e}")
        return None


def extract_financials(filing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract financial information from a filing (simplified).
    
    Note: Full financial extraction requires parsing XBRL/HTML which is complex.
    This is a simplified version that looks for common patterns.
    
    Args:
        filing: Filing dictionary (from get_filing_content)
    
    Returns:
        Dictionary with extracted financial data
    """
    content = filing.get("content", "")
    if not content:
        return {"error": "No content available"}
    
    # Simplified extraction - look for common financial terms
    # In production, would use proper XBRL parsing
    
    financials = {
        "revenue": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "cash": None
    }
    
    # Look for patterns (very simplified)
    revenue_patterns = [
        r"revenue[:\s]+[\$]?([\d,]+)",
        r"total revenue[:\s]+[\$]?([\d,]+)",
        r"net sales[:\s]+[\$]?([\d,]+)"
    ]
    
    for pattern in revenue_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                financials["revenue"] = int(match.group(1).replace(",", ""))
                break
            except ValueError:
                pass
    
    return financials


def get_ipo_filings(company_name: str) -> List[Dict[str, Any]]:
    """
    Get IPO filings (S-1 forms) for a company.
    
    Args:
        company_name: Company name
    
    Returns:
        List of S-1 filing dictionaries
    """
    filings = search_company_filings(company_name, form_type="S-1", limit=10)
    
    # Enrich with additional details
    enriched = []
    for filing in filings:
        enriched.append({
            "form_type": filing.get("form_type", ""),
            "filing_date": filing.get("filing_date", ""),
            "description": filing.get("description", ""),
            "accession_number": filing.get("accession_number", ""),
            "cik": filing.get("cik", ""),
            "is_ipo": True
        })
    
    return enriched


def get_investors_from_filings(company_name: str) -> List[Dict[str, Any]]:
    """
    Extract investor information from SEC filings (proxy statements, S-1).
    
    Note: This is limited with free sources. Full extraction requires parsing
    complex filing documents. This returns basic filing info that may contain
    investor data.
    
    Args:
        company_name: Company name
    
    Returns:
        List of investor-related information (limited)
    """
    # Search for proxy statements (DEF 14A) and S-1 filings
    proxy_filings = search_company_filings(company_name, form_type="DEF 14A", limit=5)
    s1_filings = get_ipo_filings(company_name)
    
    investors = []
    
    # Note: Actual investor extraction would require parsing filing content
    # For now, return filing references that may contain investor info
    for filing in proxy_filings + s1_filings:
        investors.append({
            "source_filing": filing.get("form_type", ""),
            "filing_date": filing.get("filing_date", ""),
            "accession_number": filing.get("accession_number", ""),
            "note": "Investor data may be available in filing content. Full extraction requires parsing filing documents."
        })
    
    return investors

