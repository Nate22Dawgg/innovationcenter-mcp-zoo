"""
ClinicalTrials.gov API client for biotech company pipeline tracking.

This module provides functions to search for clinical trials by company/sponsor name
and extract pipeline information. Reuses the existing clinical_trials_api module.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directories to path to import clinical_trials_api
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "clinical" / "clinical-trials-mcp"))

try:
    from clinical_trials_api import search_trials, get_trial_detail
except ImportError:
    # Fallback: direct API calls if import fails
    import requests
    API_BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    def search_trials(params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback search_trials implementation."""
        query_parts = []
        if params.get("condition"):
            query_parts.append(f"AREA[Condition] {params['condition']}")
        if params.get("intervention"):
            query_parts.append(f"AREA[InterventionName] {params['intervention']}")
        if params.get("location"):
            query_parts.append(f"AREA[LocationCountry] {params['location']}")
        
        query_expr = " AND ".join(query_parts) if query_parts else "*"
        limit = min(max(1, params.get("limit", 20)), 100)
        
        url = f"{API_BASE_URL}/studies"
        api_params = {
            "query.cond": query_expr,
            "pageSize": limit,
            "format": "json"
        }
        
        response = requests.get(url, params=api_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        trials = []
        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            
            sponsor = ""
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            if isinstance(lead_sponsor, dict):
                sponsor = lead_sponsor.get("name", "")
            
            trials.append({
                "nct_id": identification.get("nctId", ""),
                "title": identification.get("briefTitle", ""),
                "status": status.get("overallStatus", ""),
                "phase": _normalize_phase(design.get("phases", [])),
                "lead_sponsor": sponsor
            })
        
        return {
            "total": data.get("totalCount", len(trials)),
            "count": len(trials),
            "offset": params.get("offset", 0),
            "trials": trials
        }
    
    def _normalize_phase(phases: List[str]) -> str:
        """Normalize phase list to a single string."""
        if not phases:
            return "N/A"
        phase_map = {
            "PHASE1": "Phase 1",
            "PHASE2": "Phase 2",
            "PHASE3": "Phase 3",
            "PHASE4": "Phase 4",
            "NA": "N/A"
        }
        normalized = [phase_map.get(p.upper(), p) for p in phases if isinstance(p, str)]
        return ", ".join(normalized) if normalized else "N/A"


def get_company_trials(company_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all clinical trials for a specific company/sponsor.
    
    Args:
        company_name: Company name to search for (e.g., "Moderna", "Pfizer")
        limit: Maximum number of trials to return
    
    Returns:
        List of trial dictionaries with NCT ID, title, phase, status, etc.
    """
    # ClinicalTrials.gov API doesn't directly support sponsor search in query
    # We need to search and filter by sponsor name
    # Try multiple search strategies
    
    all_trials = []
    
    # Strategy 1: Search by company name as intervention (drugs they're developing)
    # This is less reliable but can catch some trials
    try:
        result = search_trials({
            "intervention": company_name,
            "limit": limit
        })
        all_trials.extend(result.get("trials", []))
    except Exception:
        pass
    
    # Strategy 2: Search broadly and filter by sponsor
    # Note: This is limited - we'd need to fetch many trials and filter
    # For now, we'll return what we can find
    
    # Filter trials by sponsor name (fuzzy matching)
    company_lower = company_name.lower()
    filtered_trials = []
    seen_nct_ids = set()
    
    for trial in all_trials:
        nct_id = trial.get("nct_id", "")
        if nct_id in seen_nct_ids:
            continue
        seen_nct_ids.add(nct_id)
        
        sponsor = trial.get("lead_sponsor", "").lower()
        if company_lower in sponsor or sponsor in company_lower:
            filtered_trials.append(trial)
    
    return filtered_trials[:limit]


def get_pipeline_drugs(company_name: str) -> List[Dict[str, Any]]:
    """
    Get pipeline drugs for a company from clinical trials.
    
    Args:
        company_name: Company name
    
    Returns:
        List of drugs with phase information
    """
    trials = get_company_trials(company_name, limit=100)
    
    # Extract unique drugs/interventions
    drugs = {}
    
    for trial in trials:
        # Get detailed trial info to extract interventions
        nct_id = trial.get("nct_id", "")
        if not nct_id:
            continue
        
        try:
            detail = get_trial_detail(nct_id)
            interventions = detail.get("interventions", [])
            
            for interv in interventions:
                if isinstance(interv, dict):
                    drug_name = interv.get("name", "")
                else:
                    drug_name = str(interv)
                
                if drug_name and drug_name.lower() not in ["placebo", "control"]:
                    phase = trial.get("phase", "N/A")
                    status = trial.get("status", "")
                    
                    # Track drug with latest phase
                    if drug_name not in drugs:
                        drugs[drug_name] = {
                            "name": drug_name,
                            "phases": set(),
                            "statuses": set(),
                            "nct_ids": []
                        }
                    
                    drugs[drug_name]["phases"].add(phase)
                    drugs[drug_name]["statuses"].add(status)
                    drugs[drug_name]["nct_ids"].append(nct_id)
        except Exception:
            # If detail fetch fails, use basic info
            pass
    
    # Convert to list format
    pipeline = []
    for drug_name, info in drugs.items():
        pipeline.append({
            "drug_name": drug_name,
            "phases": sorted(list(info["phases"])),
            "latest_phase": max(info["phases"], key=lambda p: _phase_order(p)) if info["phases"] else "N/A",
            "statuses": list(info["statuses"]),
            "trial_count": len(info["nct_ids"]),
            "nct_ids": info["nct_ids"][:5]  # Limit to first 5
        })
    
    # Sort by phase (later phases first)
    pipeline.sort(key=lambda x: _phase_order(x["latest_phase"]), reverse=True)
    
    return pipeline


def get_target_exposure(target: str) -> List[Dict[str, Any]]:
    """
    Get companies working on a specific target (e.g., "PD-1", "HER2").
    
    Args:
        target: Target name or identifier
    
    Returns:
        List of companies with trials for this target
    """
    # Search for trials with target in intervention or condition
    result = search_trials({
        "intervention": target,
        "limit": 100
    })
    
    trials = result.get("trials", [])
    
    # Group by company/sponsor
    company_trials = {}
    
    for trial in trials:
        sponsor = trial.get("lead_sponsor", "")
        if not sponsor:
            continue
        
        if sponsor not in company_trials:
            company_trials[sponsor] = {
                "company_name": sponsor,
                "trials": [],
                "phases": set()
            }
        
        company_trials[sponsor]["trials"].append(trial)
        phase = trial.get("phase", "N/A")
        if phase != "N/A":
            company_trials[sponsor]["phases"].add(phase)
    
    # Convert to list
    exposure = []
    for sponsor, info in company_trials.items():
        exposure.append({
            "company_name": sponsor,
            "trial_count": len(info["trials"]),
            "phases": sorted(list(info["phases"]), key=_phase_order, reverse=True),
            "latest_phase": max(info["phases"], key=_phase_order) if info["phases"] else "N/A",
            "sample_trials": info["trials"][:3]  # Sample of trials
        })
    
    # Sort by latest phase and trial count
    exposure.sort(key=lambda x: (_phase_order(x["latest_phase"]), x["trial_count"]), reverse=True)
    
    return exposure


def _phase_order(phase: str) -> int:
    """Get numeric order for phase (higher = later phase)."""
    order_map = {
        "N/A": 0,
        "Early Phase 1": 1,
        "Phase 1": 2,
        "Phase 2": 3,
        "Phase 3": 4,
        "Phase 4": 5
    }
    return order_map.get(phase, 0)

