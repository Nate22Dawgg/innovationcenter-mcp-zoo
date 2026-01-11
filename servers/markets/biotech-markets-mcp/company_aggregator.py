"""
Company data aggregator for biotech markets.

Aggregates data from multiple sources (ClinicalTrials.gov, SEC EDGAR, PubMed)
into unified company profiles.
"""

from typing import Dict, List, Optional, Any
from difflib import SequenceMatcher

import sys
from pathlib import Path

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from clinical_trials_client import get_company_trials, get_pipeline_drugs
from sec_edgar_client import (
    search_company_filings,
    get_ipo_filings,
    get_investors_from_filings,
    search_company_cik
)
from pubmed_client import search_company_publications
from common.cache import get_cache, build_cache_key


# Initialize cache
_cache = get_cache()


def _fuzzy_match(name1: str, name2: str, threshold: float = 0.7) -> bool:
    """Check if two company names are similar (fuzzy matching)."""
    name1_clean = name1.lower().strip()
    name2_clean = name2.lower().strip()
    
    # Exact match
    if name1_clean == name2_clean:
        return True
    
    # Check if one contains the other
    if name1_clean in name2_clean or name2_clean in name1_clean:
        return True
    
    # Use sequence matcher for similarity
    similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()
    return similarity >= threshold


def _normalize_company_name(company_name: str) -> str:
    """Normalize company name for matching."""
    # Remove common suffixes/prefixes
    suffixes = ["inc", "inc.", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "pharma", "pharmaceuticals", "therapeutics", "biotech", "biotechnology"]
    
    name_lower = company_name.lower().strip()
    
    for suffix in suffixes:
        if name_lower.endswith(f" {suffix}"):
            name_lower = name_lower[:-len(f" {suffix}")].strip()
        elif name_lower.endswith(f", {suffix}"):
            name_lower = name_lower[:-len(f", {suffix}")].strip()
    
    return name_lower


def get_profile(company_name: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Get unified company profile aggregating data from all sources.
    
    Args:
        company_name: Company name
        use_cache: Whether to use cached data
    
    Returns:
        Unified company profile dictionary
    """
    # Check cache (24 hour TTL for company profiles)
    if use_cache:
        cache_key = build_cache_key(
            server_name="biotech-markets-mcp",
            tool_name="get_profile",
            args={"company_name": company_name}
        )
        cached = _cache.get(cache_key)
        if cached:
            return cached
    
    profile = {
        "company_name": company_name,
        "normalized_name": _normalize_company_name(company_name),
        "sources": {
            "clinical_trials": {},
            "sec_edgar": {},
            "pubmed": {}
        },
        "pipeline": [],
        "trials": [],
        "filings": [],
        "publications": [],
        "financials": {},
        "investors": [],
        "ipo_info": [],
        "data_quality": {
            "clinical_trials": "available",
            "sec_edgar": "available",
            "pubmed": "available"
        }
    }
    
    # Get ClinicalTrials.gov data
    try:
        trials = get_company_trials(company_name, limit=50)
        profile["trials"] = trials[:20]  # Limit to 20
        
        pipeline = get_pipeline_drugs(company_name)
        profile["pipeline"] = pipeline
        
        profile["sources"]["clinical_trials"] = {
            "trial_count": len(trials),
            "pipeline_drug_count": len(pipeline)
        }
    except Exception as e:
        profile["data_quality"]["clinical_trials"] = f"error: {str(e)}"
        profile["sources"]["clinical_trials"] = {"error": str(e)}
    
    # Get SEC EDGAR data
    try:
        cik = search_company_cik(company_name)
        if cik:
            profile["cik"] = cik
            
            filings = search_company_filings(company_name, limit=10)
            profile["filings"] = filings
            
            ipo_filings = get_ipo_filings(company_name)
            profile["ipo_info"] = ipo_filings
            
            investors = get_investors_from_filings(company_name)
            profile["investors"] = investors
            
            profile["sources"]["sec_edgar"] = {
                "cik": cik,
                "filing_count": len(filings),
                "ipo_filing_count": len(ipo_filings)
            }
        else:
            profile["data_quality"]["sec_edgar"] = "company_not_found"
            profile["sources"]["sec_edgar"] = {"note": "Company not found in SEC database"}
    except Exception as e:
        profile["data_quality"]["sec_edgar"] = f"error: {str(e)}"
        profile["sources"]["sec_edgar"] = {"error": str(e)}
    
    # Get PubMed data
    try:
        publications = search_company_publications(company_name, limit=10)
        profile["publications"] = publications
        
        profile["sources"]["pubmed"] = {
            "publication_count": len(publications)
        }
    except Exception as e:
        profile["data_quality"]["pubmed"] = f"error: {str(e)}"
        profile["sources"]["pubmed"] = {"error": str(e)}
    
    # Calculate summary statistics
    profile["summary"] = {
        "total_trials": len(profile["trials"]),
        "pipeline_drugs": len(profile["pipeline"]),
        "total_filings": len(profile["filings"]),
        "total_publications": len(profile["publications"]),
        "has_ipo_info": len(profile["ipo_info"]) > 0,
        "has_investor_info": len(profile["investors"]) > 0
    }
    
    # Cache the result with 24 hour TTL (company profiles update daily)
    if use_cache:
        cache_key = build_cache_key(
            server_name="biotech-markets-mcp",
            tool_name="get_profile",
            args={"company_name": company_name}
        )
        _cache.set(cache_key, profile, ttl_seconds=24 * 60 * 60)
    
    return profile


def search_companies(
    therapeutic_area: Optional[str] = None,
    stage: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for biotech companies by criteria.
    
    Args:
        therapeutic_area: Therapeutic area (e.g., "oncology", "diabetes")
        stage: Development stage (e.g., "Phase 3", "Phase 2")
        location: Geographic location
        limit: Maximum number of companies to return
    
    Returns:
        List of company dictionaries
    """
    from clinical_trials_client import search_trials
    
    # Build search parameters
    search_params = {}
    if therapeutic_area:
        search_params["condition"] = therapeutic_area
    if location:
        search_params["location"] = location
    if stage:
        search_params["phase"] = stage
    
    search_params["limit"] = min(limit * 2, 100)  # Get more trials to extract companies
    
    # Search clinical trials
    try:
        result = search_trials(search_params)
        trials = result.get("trials", [])
        
        # Extract unique companies from sponsors
        companies = {}
        
        for trial in trials:
            sponsor = trial.get("lead_sponsor", "")
            if not sponsor or sponsor.lower() in ["unknown", "n/a", ""]:
                continue
            
            # Normalize company name
            normalized = _normalize_company_name(sponsor)
            
            if normalized not in companies:
                companies[normalized] = {
                    "company_name": sponsor,
                    "normalized_name": normalized,
                    "trial_count": 0,
                    "phases": set(),
                    "therapeutic_areas": set(),
                    "sample_trials": []
                }
            
            companies[normalized]["trial_count"] += 1
            
            phase = trial.get("phase", "")
            if phase and phase != "N/A":
                companies[normalized]["phases"].add(phase)
            
            conditions = trial.get("conditions", [])
            for condition in conditions:
                if condition:
                    companies[normalized]["therapeutic_areas"].add(condition)
            
            if len(companies[normalized]["sample_trials"]) < 3:
                companies[normalized]["sample_trials"].append(trial)
        
        # Convert to list
        company_list = []
        for normalized, info in companies.items():
            company_list.append({
                "company_name": info["company_name"],
                "normalized_name": normalized,
                "trial_count": info["trial_count"],
                "phases": sorted(list(info["phases"])),
                "therapeutic_areas": list(info["therapeutic_areas"])[:5],  # Top 5
                "sample_trials": info["sample_trials"]
            })
        
        # Sort by trial count
        company_list.sort(key=lambda x: x["trial_count"], reverse=True)
        
        return company_list[:limit]
        
    except Exception as e:
        return [{"error": str(e)}]

