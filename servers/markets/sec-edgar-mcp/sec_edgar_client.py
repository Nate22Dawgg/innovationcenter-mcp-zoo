"""
SEC EDGAR API client for comprehensive filing access and company data.

Uses free SEC EDGAR API (data.sec.gov) - no authentication required.
Rate limit: 10 requests per second (enforced).
"""

import requests
import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


# SEC EDGAR API base URLs
SEC_BASE_URL = "https://data.sec.gov"
SEC_EDGAR_URL = "https://www.sec.gov"
COMPANY_TICKERS_URL = f"{SEC_EDGAR_URL}/files/company_tickers.json"
CIK_LOOKUP_URL = f"{SEC_EDGAR_URL}/cgi-bin/browse-edgar"

# Required User-Agent header (SEC requirement)
USER_AGENT = "MCP SEC EDGAR Server (contact@example.com)"


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
    _rate_limit()
    
    try:
        # Get company tickers JSON
        response = requests.get(COMPANY_TICKERS_URL, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        company_name_lower = company_name.lower()
        
        # Search through tickers
        for ticker_data in data.values():
            if isinstance(ticker_data, dict):
                title = ticker_data.get("title", "").lower()
                if company_name_lower in title or title in company_name_lower:
                    cik = str(ticker_data.get("cik_str", ""))
                    if cik:
                        return cik.zfill(10)  # Zero-pad to 10 digits
        
        return None
    except Exception as e:
        print(f"Error searching for CIK: {e}")
        return None


def get_company_ticker_info(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get company information by ticker symbol.
    
    Args:
        ticker: Ticker symbol (e.g., "AAPL")
    
    Returns:
        Dictionary with company info or None
    """
    _rate_limit()
    
    try:
        response = requests.get(COMPANY_TICKERS_URL, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        ticker_upper = ticker.upper()
        
        for ticker_data in data.values():
            if isinstance(ticker_data, dict):
                if ticker_data.get("ticker", "").upper() == ticker_upper:
                    return {
                        "cik": str(ticker_data.get("cik_str", "")).zfill(10),
                        "ticker": ticker_data.get("ticker", ""),
                        "title": ticker_data.get("title", ""),
                        "exchange": ticker_data.get("exchange", "")
                    }
        
        return None
    except Exception as e:
        print(f"Error getting ticker info: {e}")
        return None


def get_company_submissions(cik: str) -> Dict[str, Any]:
    """
    Get company submissions index (comprehensive company data).
    
    Args:
        cik: Company CIK (10-digit zero-padded)
    
    Returns:
        Dictionary with company submissions data
    """
    _rate_limit()
    
    try:
        url = f"{SEC_BASE_URL}/submissions/CIK{cik}.json"
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting submissions: {e}")
        return {}


def search_company_filings(
    company_name: str,
    form_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
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
    _rate_limit()
    
    try:
        # Get submissions to access filings
        submissions = get_company_submissions(cik)
        
        if not submissions or "filings" not in submissions:
            return []
        
        filings_data = submissions["filings"]
        recent = filings_data.get("recent", {})
        
        forms = recent.get("form", [])
        dates = recent.get("reportDate", [])
        descriptions = recent.get("description", [])
        accession_numbers = recent.get("accessionNumber", [])
        file_numbers = recent.get("fileNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        
        result = []
        for i in range(min(len(forms), limit * 2)):  # Get more to filter
            if form_type and forms[i] != form_type:
                continue
            
            result.append({
                "form_type": forms[i],
                "filing_date": dates[i] if i < len(dates) else "",
                "report_date": dates[i] if i < len(dates) else "",
                "description": descriptions[i] if i < len(descriptions) else "",
                "accession_number": accession_numbers[i] if i < len(accession_numbers) else "",
                "file_number": file_numbers[i] if i < len(file_numbers) else "",
                "primary_document": primary_documents[i] if i < len(primary_documents) else "",
                "cik": cik
            })
            
            if len(result) >= limit:
                break
        
        return result
    except Exception as e:
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
    _rate_limit()
    
    try:
        # Convert accession number to URL format
        # Format: 0001234567-24-000001 -> 0001234567/24-000001
        parts = accession_number.split("-")
        if len(parts) >= 3:
            url_path = f"{parts[0]}/{parts[1]}-{parts[2]}"
        else:
            url_path = accession_number
        
        # Try to get the filing document
        # First, try to get the index file to find the primary document
        index_url = f"{SEC_BASE_URL}/files/data/{cik}/{accession_number}/{accession_number}-index.html"
        
        # For now, try the .txt file directly
        url = f"{SEC_BASE_URL}/files/data/{cik}/{accession_number}/{accession_number}.txt"
        
        response = requests.get(url, headers=_get_headers(), timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        return {
            "cik": cik,
            "accession_number": accession_number,
            "content": content,
            "content_length": len(content),
            "url": url
        }
    except Exception as e:
        print(f"Error getting filing content: {e}")
        return None


def search_filings_by_keyword(
    keyword: str,
    form_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search filings by keyword (simplified - searches company names and descriptions).
    
    Note: Full-text search requires downloading and parsing filing content.
    This is a simplified version that searches company names.
    
    Args:
        keyword: Keyword to search for
        form_type: Optional form type filter
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum number of results
    
    Returns:
        List of matching filings
    """
    _rate_limit()
    
    try:
        # Get all companies and search by name
        response = requests.get(COMPANY_TICKERS_URL, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        keyword_lower = keyword.lower()
        results = []
        
        for ticker_data in data.values():
            if isinstance(ticker_data, dict):
                title = ticker_data.get("title", "").lower()
                if keyword_lower in title:
                    cik = str(ticker_data.get("cik_str", "")).zfill(10)
                    
                    # Get recent filings
                    filings = get_filings_by_cik(cik, form_type=form_type, limit=5)
                    
                    # Filter by date if provided
                    for filing in filings:
                        filing_date = filing.get("filing_date", "")
                        if start_date and filing_date < start_date:
                            continue
                        if end_date and filing_date > end_date:
                            continue
                        
                        results.append({
                            **filing,
                            "company_name": ticker_data.get("title", "")
                        })
                        
                        if len(results) >= limit:
                            break
                    
                    if len(results) >= limit:
                        break
        
        return results[:limit]
    except Exception as e:
        print(f"Error searching filings: {e}")
        return []


def extract_financial_data(filing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract financial information from a filing (10-K, 10-Q, etc.).
    
    Note: This is a simplified extraction using pattern matching.
    For comprehensive financial data, parse XBRL files directly.
    
    Args:
        filing: Filing dictionary (from get_filing_content)
    
    Returns:
        Dictionary with extracted financial data
    """
    content = filing.get("content", "")
    if not content:
        return {"error": "No content available"}
    
    financials = {
        "revenue": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "cash": None,
        "ebitda": None,
        "operating_income": None,
        "diluted_earnings_per_share": None
    }
    
    # Look for common financial patterns (simplified)
    patterns = {
        "revenue": [
            r"(?:total\s+)?revenue[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?",
            r"net\s+sales[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?",
            r"revenue[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "net_income": [
            r"net\s+income[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?",
            r"net\s+earnings[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "total_assets": [
            r"total\s+assets[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "total_liabilities": [
            r"total\s+liabilities[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "cash": [
            r"cash\s+and\s+cash\s+equivalents[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?",
            r"cash[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "ebitda": [
            r"ebitda[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "operating_income": [
            r"operating\s+income[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)\s*(?:million|billion|thousand)?"
        ],
        "diluted_earnings_per_share": [
            r"diluted\s+earnings\s+per\s+share[:\s]+[\$]?([\d,]+(?:\.[\d]+)?)"
        ]
    }
    
    def parse_value(match_str: str) -> Optional[float]:
        """Parse a value string, handling millions/billions/thousands."""
        try:
            # Remove commas and $ signs
            clean = match_str.replace(",", "").replace("$", "").strip().lower()
            
            # Check for scale indicators
            multiplier = 1.0
            if "billion" in clean:
                multiplier = 1_000_000_000
                clean = clean.replace("billion", "")
            elif "million" in clean:
                multiplier = 1_000_000
                clean = clean.replace("million", "")
            elif "thousand" in clean:
                multiplier = 1_000
                clean = clean.replace("thousand", "")
            
            value = float(clean.strip())
            return value * multiplier
        except (ValueError, AttributeError):
            return None
    
    # Search for each financial metric
    for metric, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = parse_value(match.group(1))
                if value:
                    financials[metric] = value
                    break
    
    return financials

