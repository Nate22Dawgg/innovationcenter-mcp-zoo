"""
Shared identifier normalization utilities.

Provides centralized normalization functions for identifiers used across MCP servers:
- Tickers (stock symbols)
- CIKs (SEC Central Index Keys)
- NCT IDs (ClinicalTrials.gov identifiers)
- CPT/HCPCS codes (medical procedure codes)
- NPI (National Provider Identifier)
- Addresses (optional)

These utilities ensure consistent identifier formats across cross-MCP workflows
and prevent identifier mismatches in orchestration scenarios.
"""

import re
from typing import Dict, Any, Optional, Union


def normalize_ticker(ticker: str) -> str:
    """
    Normalize a stock ticker symbol.
    
    - Converts to uppercase
    - Strips whitespace
    - Removes common prefixes/suffixes if present
    
    Args:
        ticker: Ticker symbol (e.g., "aapl", " MSFT ", "BRK.B")
    
    Returns:
        Normalized ticker (e.g., "AAPL", "MSFT", "BRK.B")
    
    Examples:
        >>> normalize_ticker("aapl")
        'AAPL'
        >>> normalize_ticker(" MSFT ")
        'MSFT'
        >>> normalize_ticker("brk.b")
        'BRK.B'
    """
    if not ticker:
        return ""
    
    # Strip whitespace and convert to uppercase
    normalized = ticker.strip().upper()
    
    return normalized


def normalize_cik(cik: Union[str, int]) -> str:
    """
    Normalize a SEC CIK (Central Index Key) to 10-digit zero-padded format.
    
    - Converts to string if numeric
    - Strips whitespace
    - Zero-pads to 10 digits
    
    Args:
        cik: CIK as string or integer (e.g., "320193", 320193, "0000320193")
    
    Returns:
        Zero-padded 10-digit CIK string (e.g., "0000320193")
    
    Examples:
        >>> normalize_cik("320193")
        '0000320193'
        >>> normalize_cik(320193)
        '0000320193'
        >>> normalize_cik("0000320193")
        '0000320193'
    """
    if cik is None:
        return ""
    
    # Convert to string and strip whitespace
    cik_str = str(cik).strip()
    
    if not cik_str:
        return ""
    
    # Try to parse as integer to remove leading zeros, then zero-pad
    try:
        cik_int = int(cik_str)
        return f"{cik_int:010d}"
    except (ValueError, TypeError):
        # If not numeric, return as-is (but still zero-pad if it's all digits)
        if cik_str.isdigit():
            return cik_str.zfill(10)
        return cik_str


def normalize_nct_id(nct_id: str) -> str:
    """
    Normalize a ClinicalTrials.gov NCT ID.
    
    - Ensures uppercase "NCT" prefix
    - Ensures exactly 8 digits after "NCT"
    - Strips whitespace
    
    Args:
        nct_id: NCT ID (e.g., "nct01234567", "NCT01234567", "NCT 01234567")
    
    Returns:
        Normalized NCT ID (e.g., "NCT01234567")
    
    Examples:
        >>> normalize_nct_id("nct01234567")
        'NCT01234567'
        >>> normalize_nct_id("NCT 01234567")
        'NCT01234567'
        >>> normalize_nct_id("NCT01234567")
        'NCT01234567'
    """
    if not nct_id:
        return ""
    
    # Strip whitespace and convert to uppercase
    normalized = nct_id.strip().upper()
    
    # Remove spaces between NCT and digits
    normalized = re.sub(r'NCT\s+', 'NCT', normalized)
    
    # Ensure it starts with NCT
    if not normalized.startswith("NCT"):
        # If it's just digits, add NCT prefix
        if normalized.isdigit():
            normalized = f"NCT{normalized}"
        else:
            return normalized  # Return as-is if malformed
    
    # Extract digits after NCT
    match = re.match(r'NCT(\d+)', normalized)
    if match:
        digits = match.group(1)
        # Ensure exactly 8 digits (pad with zeros if needed)
        if len(digits) < 8:
            digits = digits.zfill(8)
        elif len(digits) > 8:
            # Truncate to 8 digits if too long
            digits = digits[:8]
        return f"NCT{digits}"
    
    return normalized


def normalize_cpt_code(code: str) -> str:
    """
    Normalize a CPT (Current Procedural Terminology) code.
    
    - Strips whitespace
    - Removes modifiers (e.g., "-25", "-59")
    - Ensures 5-digit numeric format
    
    Args:
        code: CPT code (e.g., "99213", "99213-25", " 99213 ")
    
    Returns:
        Normalized CPT code (e.g., "99213")
    
    Examples:
        >>> normalize_cpt_code("99213")
        '99213'
        >>> normalize_cpt_code("99213-25")
        '99213'
        >>> normalize_cpt_code(" 99213 ")
        '99213'
    """
    if not code:
        return ""
    
    # Strip whitespace
    normalized = code.strip()
    
    # Remove modifiers (everything after first hyphen or space)
    normalized = normalized.split("-")[0].split()[0]
    
    # Extract only digits
    digits = re.sub(r'\D', '', normalized)
    
    # Ensure 5 digits (pad with zeros if needed, truncate if too long)
    if len(digits) < 5:
        digits = digits.zfill(5)
    elif len(digits) > 5:
        digits = digits[:5]
    
    return digits


def normalize_hcpcs_code(code: str) -> str:
    """
    Normalize an HCPCS (Healthcare Common Procedure Coding System) code.
    
    - Strips whitespace
    - Removes modifiers
    - Ensures uppercase
    - Ensures 5-character alphanumeric format
    
    Args:
        code: HCPCS code (e.g., "A0425", "a0425-25", " A0425 ")
    
    Returns:
        Normalized HCPCS code (e.g., "A0425")
    
    Examples:
        >>> normalize_hcpcs_code("A0425")
        'A0425'
        >>> normalize_hcpcs_code("a0425-25")
        'A0425'
        >>> normalize_hcpcs_code(" A0425 ")
        'A0425'
    """
    if not code:
        return ""
    
    # Strip whitespace and convert to uppercase
    normalized = code.strip().upper()
    
    # Remove modifiers (everything after first hyphen or space)
    normalized = normalized.split("-")[0].split()[0]
    
    # Extract alphanumeric characters only
    normalized = re.sub(r'[^A-Z0-9]', '', normalized)
    
    # Ensure 5 characters (pad with zeros if needed, truncate if too long)
    if len(normalized) < 5:
        # HCPCS codes typically start with a letter, pad with zeros if needed
        normalized = normalized.ljust(5, '0')
    elif len(normalized) > 5:
        normalized = normalized[:5]
    
    return normalized


def normalize_npi(npi: Union[str, int]) -> str:
    """
    Normalize an NPI (National Provider Identifier).
    
    - Converts to string if numeric
    - Strips whitespace and hyphens
    - Ensures 10-digit numeric format
    
    Args:
        npi: NPI as string or integer (e.g., "1234567890", 1234567890, "123-456-7890")
    
    Returns:
        Normalized 10-digit NPI string (e.g., "1234567890")
    
    Examples:
        >>> normalize_npi("1234567890")
        '1234567890'
        >>> normalize_npi("123-456-7890")
        '1234567890'
        >>> normalize_npi(1234567890)
        '1234567890'
    """
    if npi is None:
        return ""
    
    # Convert to string and strip whitespace
    npi_str = str(npi).strip()
    
    # Remove hyphens and spaces
    npi_str = re.sub(r'[-\s]', '', npi_str)
    
    # Extract only digits
    digits = re.sub(r'\D', '', npi_str)
    
    # Ensure exactly 10 digits (pad with zeros if needed, truncate if too long)
    if len(digits) < 10:
        digits = digits.zfill(10)
    elif len(digits) > 10:
        digits = digits[:10]
    
    return digits


def normalize_address(address: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize an address to a consistent dictionary format.
    
    - Handles both string and dictionary inputs
    - Normalizes field names (street, city, state, zip_code)
    - Uppercases state codes
    - Normalizes ZIP codes to 5 or 9 digits
    
    Args:
        address: Address as string or dictionary
    
    Returns:
        Normalized address dictionary with keys:
        {
            "street": str,
            "city": str,
            "state": str,
            "zip_code": str,
            "country": str (optional)
        }
    
    Examples:
        >>> normalize_address({"street": "123 Main St", "city": "Boston", "state": "ma", "zip": "02115"})
        {'street': '123 Main St', 'city': 'Boston', 'state': 'MA', 'zip_code': '02115', 'country': None}
    """
    if not address:
        return {
            "street": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "country": None
        }
    
    # If string, try to parse (simplified - full parsing would be more complex)
    if isinstance(address, str):
        # For now, return minimal structure - full address parsing is complex
        return {
            "street": address,
            "city": None,
            "state": None,
            "zip_code": None,
            "country": None
        }
    
    # If dictionary, normalize field names
    if isinstance(address, dict):
        normalized = {
            "street": address.get("street") or address.get("street_address") or address.get("address") or address.get("address_line_1"),
            "city": address.get("city"),
            "state": address.get("state") or address.get("state_code"),
            "zip_code": address.get("zip_code") or address.get("zip") or address.get("postal_code"),
            "country": address.get("country") or address.get("country_code")
        }
        
        # Normalize state to uppercase
        if normalized["state"]:
            normalized["state"] = str(normalized["state"]).strip().upper()
        
        # Normalize ZIP code (remove hyphens, ensure 5 or 9 digits)
        if normalized["zip_code"]:
            zip_str = str(normalized["zip_code"]).strip()
            zip_str = re.sub(r'[-\s]', '', zip_str)
            if zip_str.isdigit():
                if len(zip_str) == 9:
                    normalized["zip_code"] = f"{zip_str[:5]}-{zip_str[5:]}"
                elif len(zip_str) == 5:
                    normalized["zip_code"] = zip_str
                elif len(zip_str) > 5:
                    normalized["zip_code"] = zip_str[:5]
                else:
                    normalized["zip_code"] = zip_str.zfill(5)
            else:
                normalized["zip_code"] = zip_str
        
        # Clean up None values
        for key, value in normalized.items():
            if value == "":
                normalized[key] = None
        
        return normalized
    
    # Fallback
    return {
        "street": None,
        "city": None,
        "state": None,
        "zip_code": None,
        "country": None
    }
