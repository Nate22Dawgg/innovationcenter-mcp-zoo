"""
CMS Fee Schedule Integration

This module provides functions to lookup CPT and HCPCS codes in CMS (Centers for 
Medicare & Medicaid Services) fee schedules, including the Physician Fee Schedule.

Data Sources:
- CMS Physician Fee Schedule: https://www.cms.gov/medicare/physician-fee-schedule
- CMS HCPCS Codes: https://www.cms.gov/medicare/coding-billing/medicare-coding
"""

import os
import json
import csv
import requests
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


# Base directory for cached CMS data
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# CMS Fee Schedule URLs (these are examples - actual URLs may vary)
CMS_PFS_BASE_URL = "https://www.cms.gov/medicare/physician-fee-schedule"
CMS_HCPCS_BASE_URL = "https://www.cms.gov/medicare/coding-billing/medicare-coding"


def lookup_cpt_price(
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
        Dictionary with price information:
        {
            "cpt_code": "...",
            "year": int,
            "locality": str,
            "facility_price": float,
            "non_facility_price": float,
            "description": str,
            "status": "found" | "not_found" | "error"
        }
    """
    if not cpt_code or len(cpt_code) != 5 or not cpt_code.isdigit():
        return {
            "cpt_code": cpt_code,
            "status": "error",
            "error": "Invalid CPT code format (must be 5 digits)"
        }
    
    if year is None:
        year = datetime.now().year
    
    if locality is None:
        locality = "00"  # National average
    
    # Try to load from cache
    cache_file = DATA_DIR / f"pfs_{year}_{locality}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                fee_schedule = json.load(f)
                if cpt_code in fee_schedule:
                    return {
                        "cpt_code": cpt_code,
                        "year": year,
                        "locality": locality,
                        "facility_price": fee_schedule[cpt_code].get("facility_price", 0.0),
                        "non_facility_price": fee_schedule[cpt_code].get("non_facility_price", 0.0),
                        "description": fee_schedule[cpt_code].get("description", ""),
                        "status": "found"
                    }
        except Exception as e:
            pass  # Fall through to download
    
    # If not in cache, try to download
    try:
        download_fee_schedule(year, locality)
        # Retry lookup after download
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                fee_schedule = json.load(f)
                if cpt_code in fee_schedule:
                    return {
                        "cpt_code": cpt_code,
                        "year": year,
                        "locality": locality,
                        "facility_price": fee_schedule[cpt_code].get("facility_price", 0.0),
                        "non_facility_price": fee_schedule[cpt_code].get("non_facility_price", 0.0),
                        "description": fee_schedule[cpt_code].get("description", ""),
                        "status": "found"
                    }
    except Exception as e:
        pass
    
    # Not found
    return {
        "cpt_code": cpt_code,
        "year": year,
        "locality": locality,
        "status": "not_found",
        "message": "CPT code not found in fee schedule. Fee schedules must be downloaded from CMS."
    }


def lookup_hcpcs_price(
    hcpcs_code: str,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lookup HCPCS code price from CMS fee schedules.
    
    Args:
        hcpcs_code: HCPCS procedure code (5-character alphanumeric, e.g., "A0425")
        year: Year for fee schedule (default: current year)
        
    Returns:
        Dictionary with price information:
        {
            "hcpcs_code": "...",
            "year": int,
            "price": float,
            "description": str,
            "status": "found" | "not_found" | "error"
        }
    """
    if not hcpcs_code or len(hcpcs_code) != 5:
        return {
            "hcpcs_code": hcpcs_code,
            "status": "error",
            "error": "Invalid HCPCS code format (must be 5 characters)"
        }
    
    if year is None:
        year = datetime.now().year
    
    # Try to load from cache
    cache_file = DATA_DIR / f"hcpcs_{year}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                fee_schedule = json.load(f)
                if hcpcs_code in fee_schedule:
                    return {
                        "hcpcs_code": hcpcs_code,
                        "year": year,
                        "price": fee_schedule[hcpcs_code].get("price", 0.0),
                        "description": fee_schedule[hcpcs_code].get("description", ""),
                        "status": "found"
                    }
        except Exception as e:
            pass  # Fall through to download
    
    # If not in cache, try to download
    try:
        download_hcpcs_schedule(year)
        # Retry lookup after download
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                fee_schedule = json.load(f)
                if hcpcs_code in fee_schedule:
                    return {
                        "hcpcs_code": hcpcs_code,
                        "year": year,
                        "price": fee_schedule[hcpcs_code].get("price", 0.0),
                        "description": fee_schedule[hcpcs_code].get("description", ""),
                        "status": "found"
                    }
    except Exception as e:
        pass
    
    # Not found
    return {
        "hcpcs_code": hcpcs_code,
        "year": year,
        "status": "not_found",
        "message": "HCPCS code not found in fee schedule. Fee schedules must be downloaded from CMS."
    }


def download_fee_schedule(year: int, locality: str = "00") -> bool:
    """
    Download CMS Physician Fee Schedule for a given year and locality.
    
    Note: This is a placeholder. Actual implementation would:
    1. Navigate to CMS website
    2. Download the appropriate CSV/Excel file
    3. Parse and cache locally
    
    Args:
        year: Year for fee schedule
        locality: Locality code (default: "00" for national)
        
    Returns:
        True if download successful, False otherwise
    """
    cache_file = DATA_DIR / f"pfs_{year}_{locality}.json"
    
    # If already cached, skip
    if cache_file.exists():
        return True
    
    # NOTE: Actual implementation would download from CMS
    # For now, create an empty cache file structure
    fee_schedule = {}
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(fee_schedule, f, indent=2)
        
        # Log that manual download is required
        readme_file = DATA_DIR / "README.md"
        if not readme_file.exists():
            with open(readme_file, 'w') as f:
                f.write(f"""# CMS Fee Schedule Data

## Download Instructions

CMS fee schedules must be downloaded manually from:
- Physician Fee Schedule: {CMS_PFS_BASE_URL}
- HCPCS Codes: {CMS_HCPCS_BASE_URL}

## File Format

Fee schedule files should be saved as JSON in the following format:

### Physician Fee Schedule (pfs_YYYY_LOCALITY.json)
```json
{{
  "99213": {{
    "facility_price": 75.50,
    "non_facility_price": 100.25,
    "description": "Office or other outpatient visit"
  }}
}}
```

### HCPCS Schedule (hcpcs_YYYY.json)
```json
{{
  "A0425": {{
    "price": 25.00,
    "description": "Ambulance service"
  }}
}}
```

## Update Frequency

CMS fee schedules are updated annually. Update files at the beginning of each year.
""")
        
        return True
    except Exception as e:
        return False


def download_hcpcs_schedule(year: int) -> bool:
    """
    Download CMS HCPCS fee schedule for a given year.
    
    Note: This is a placeholder. Actual implementation would download from CMS.
    
    Args:
        year: Year for fee schedule
        
    Returns:
        True if download successful, False otherwise
    """
    cache_file = DATA_DIR / f"hcpcs_{year}.json"
    
    # If already cached, skip
    if cache_file.exists():
        return True
    
    # NOTE: Actual implementation would download from CMS
    # For now, create an empty cache file structure
    fee_schedule = {}
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(fee_schedule, f, indent=2)
        return True
    except Exception as e:
        return False


def get_available_years() -> list:
    """Get list of years with cached fee schedules."""
    years = set()
    
    for file in DATA_DIR.glob("pfs_*.json"):
        parts = file.stem.split("_")
        if len(parts) >= 2:
            try:
                years.add(int(parts[1]))
            except ValueError:
                pass
    
    for file in DATA_DIR.glob("hcpcs_*.json"):
        parts = file.stem.split("_")
        if len(parts) >= 2:
            try:
                years.add(int(parts[1]))
            except ValueError:
                pass
    
    return sorted(list(years), reverse=True)

