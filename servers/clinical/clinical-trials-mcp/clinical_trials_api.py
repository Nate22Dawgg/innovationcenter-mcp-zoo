"""
ClinicalTrials.gov API client for searching and retrieving clinical trials data.

This module provides functions to interact with the official ClinicalTrials.gov API v2.
It normalizes responses into clean JSON structures matching our schema definitions.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common.http import get
from common.errors import ApiError, map_upstream_error
from common.cache import get_cache, build_cache_key


# ClinicalTrials.gov API base URL
API_BASE_URL = "https://clinicaltrials.gov/api/v2"


def search_trials(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for clinical trials using ClinicalTrials.gov API.
    
    Args:
        params: Dictionary with search parameters:
            - condition (str, optional): Medical condition or disease
            - intervention (str, optional): Intervention type
            - location (str, optional): Geographic location
            - status (str, optional): Recruitment status
            - phase (str, optional): Trial phase
            - study_type (str, optional): Type of study
            - limit (int, optional): Max results (1-100, default: 20)
            - offset (int, optional): Pagination offset (default: 0)
    
    Returns:
        Dictionary with:
            - total: Total number of matching trials
            - count: Number of trials in this response
            - offset: Offset used
            - trials: List of simplified trial objects
    """
    # Build query parameters for API
    query_parts = []
    
    if params.get("condition"):
        query_parts.append(f"AREA[Condition] {params['condition']}")
    
    if params.get("intervention"):
        query_parts.append(f"AREA[InterventionName] {params['intervention']}")
    
    if params.get("location"):
        query_parts.append(f"AREA[LocationCountry] {params['location']}")
    
    if params.get("status"):
        status_map = {
            "recruiting": "RECRUITING",
            "not yet recruiting": "NOT_YET_RECRUITING",
            "active": "ACTIVE_NOT_RECRUITING",
            "completed": "COMPLETED",
            "suspended": "SUSPENDED",
            "terminated": "TERMINATED",
            "withdrawn": "WITHDRAWN"
        }
        status = status_map.get(params["status"], params["status"].upper())
        query_parts.append(f"AREA[OverallStatus] {status}")
    
    if params.get("phase"):
        phase_map = {
            "Phase 1": "PHASE1",
            "Phase 2": "PHASE2",
            "Phase 3": "PHASE3",
            "Phase 4": "PHASE4",
            "N/A": "NA"
        }
        phase = phase_map.get(params["phase"], params["phase"].upper().replace(" ", ""))
        query_parts.append(f"AREA[Phase] {phase}")
    
    if params.get("study_type"):
        study_type_map = {
            "Interventional": "INTERVENTIONAL",
            "Observational": "OBSERVATIONAL",
            "Expanded Access": "EXPANDED_ACCESS"
        }
        study_type = study_type_map.get(params["study_type"], params["study_type"].upper())
        query_parts.append(f"AREA[StudyType] {study_type}")
    
    query_expr = " AND ".join(query_parts) if query_parts else "*"
    
    # Get pagination parameters
    limit = min(max(1, params.get("limit", 20)), 100)
    offset = max(0, params.get("offset", 0))
    
    # Check cache first (6 hour TTL for trial searches - data updates regularly)
    cache = get_cache()
    cache_key = build_cache_key(
        server_name="clinical-trials-mcp",
        tool_name="search_trials",
        args=params
    )
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Make API request
    url = f"{API_BASE_URL}/studies"
    api_params = {
        "query.cond": query_expr,
        "pageSize": limit,
        "pageToken": str(offset // limit) if offset > 0 else "0",
        "format": "json"
    }
    
    try:
        response = get(
            url=url,
            upstream="clinicaltrials",
            timeout=30.0,
            params=api_params
        )
        data = response.json()
        
        # Normalize response to our schema format
        trials = []
        studies = data.get("studies", [])
        
        for study in studies:
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            
            # Extract conditions
            conditions = []
            for cond in protocol.get("conditionsModule", {}).get("conditions", []):
                if isinstance(cond, dict):
                    conditions.append(cond.get("name", ""))
                else:
                    conditions.append(str(cond))
            
            # Extract interventions
            interventions = []
            for interv in protocol.get("armsInterventionsModule", {}).get("interventions", []):
                if isinstance(interv, dict):
                    interventions.append(interv.get("name", ""))
                else:
                    interventions.append(str(interv))
            
            # Extract locations
            locations = []
            for loc in protocol.get("contactsLocationsModule", {}).get("locations", []):
                if isinstance(loc, dict):
                    loc_str = ", ".join(filter(None, [
                        loc.get("city"),
                        loc.get("state"),
                        loc.get("country")
                    ]))
                    if loc_str:
                        locations.append(loc_str)
            
            # Extract sponsor
            sponsor = ""
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            if isinstance(lead_sponsor, dict):
                sponsor = lead_sponsor.get("name", "")
            
            # Extract dates
            start_date = status.get("startDateStruct", {}).get("date", "")
            completion_date = status.get("completionDateStruct", {}).get("date", "")
            
            # Normalize dates to ISO format if possible
            if start_date:
                start_date = _normalize_date(start_date)
            if completion_date:
                completion_date = _normalize_date(completion_date)
            
            trial_obj = {
                "nct_id": identification.get("nctId", ""),
                "title": identification.get("briefTitle", ""),
                "status": status.get("overallStatus", ""),
                "phase": _normalize_phase(design.get("phases", [])),
                "conditions": conditions,
                "interventions": interventions,
                "locations": locations[:5],  # Limit to first 5 locations
                "lead_sponsor": sponsor,
                "start_date": start_date if start_date else None,
                "completion_date": completion_date if completion_date else None,
                "url": f"https://clinicaltrials.gov/study/{identification.get('nctId', '')}"
            }
            trials.append(trial_obj)
        
        # Get total count (approximate - API doesn't always provide exact)
        total = data.get("totalCount", len(trials))
        
        result = {
            "total": total,
            "count": len(trials),
            "offset": offset,
            "trials": trials
        }
        
        # Cache result with 6 hour TTL (trial searches update regularly but not constantly)
        cache.set(cache_key, result, ttl_seconds=6 * 60 * 60)
        
        return result
        
    except ApiError as e:
        # Re-raise ApiError as-is (already standardized)
        raise
    except (KeyError, ValueError) as e:
        raise ApiError(
            message=f"Failed to parse API response: {str(e)}",
            original_error=e
        )
    except Exception as e:
        # Map unexpected errors to structured errors
        mapped_error = map_upstream_error(e)
        if mapped_error:
            raise mapped_error
        raise ApiError(
            message=f"Failed to search clinical trials: {str(e)}",
            original_error=e
        )


def get_trial_detail(nct_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific clinical trial.
    
    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., "NCT01234567")
    
    Returns:
        Dictionary with detailed trial information including:
            - nct_id, titles, descriptions, status, phase
            - conditions, interventions, outcomes
            - enrollment, locations, contacts
            - dates, eligibility criteria, etc.
    """
    # Validate NCT ID format
    if not nct_id.startswith("NCT") or len(nct_id) != 11:
        raise ValueError(f"Invalid NCT ID format: {nct_id}")
    
    # Check cache first (24 hour TTL for trial details - change infrequently)
    cache = get_cache()
    cache_key = build_cache_key(
        server_name="clinical-trials-mcp",
        tool_name="get_trial_detail",
        args={"nct_id": nct_id}
    )
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    url = f"{API_BASE_URL}/studies/{nct_id}"
    
    try:
        response = get(
            url=url,
            upstream="clinicaltrials",
            timeout=30.0,
            params={"format": "json"}
        )
        data = response.json()
        
        # Extract study data
        study = data.get("protocolSection", {})
        if not study:
            raise ValueError(f"No protocol section found for {nct_id}")
        
        identification = study.get("identificationModule", {})
        status_module = study.get("statusModule", {})
        design = study.get("designModule", {})
        eligibility = study.get("eligibilityModule", {})
        description = study.get("descriptionModule", {})
        conditions = study.get("conditionsModule", {})
        interventions_module = study.get("armsInterventionsModule", {})
        outcomes = study.get("outcomesModule", {})
        contacts_locations = study.get("contactsLocationsModule", {})
        sponsor = study.get("sponsorCollaboratorsModule", {})
        references = study.get("referencesModule", {})
        
        # Extract conditions
        conditions_list = []
        for cond in conditions.get("conditions", []):
            if isinstance(cond, dict):
                conditions_list.append(cond.get("name", ""))
            else:
                conditions_list.append(str(cond))
        
        # Extract interventions with details
        interventions_list = []
        for interv in interventions_module.get("interventions", []):
            if isinstance(interv, dict):
                interventions_list.append({
                    "name": interv.get("name", ""),
                    "type": interv.get("type", ""),
                    "description": interv.get("description", "")
                })
            else:
                interventions_list.append({"name": str(interv)})
        
        # Extract outcomes
        outcomes_list = []
        for outcome in outcomes.get("primaryOutcomes", []):
            if isinstance(outcome, dict):
                outcomes_list.append({
                    "type": "primary",
                    "title": outcome.get("measure", ""),
                    "description": outcome.get("description", ""),
                    "time_frame": outcome.get("timeFrame", "")
                })
        for outcome in outcomes.get("secondaryOutcomes", []):
            if isinstance(outcome, dict):
                outcomes_list.append({
                    "type": "secondary",
                    "title": outcome.get("measure", ""),
                    "description": outcome.get("description", ""),
                    "time_frame": outcome.get("timeFrame", "")
                })
        
        # Extract locations with details
        locations_list = []
        for loc in contacts_locations.get("locations", []):
            if isinstance(loc, dict):
                locations_list.append({
                    "name": loc.get("name", ""),
                    "city": loc.get("city", ""),
                    "state": loc.get("state", ""),
                    "zip": loc.get("zip", ""),
                    "country": loc.get("country", ""),
                    "status": loc.get("status", "")
                })
        
        # Extract contacts
        contacts_list = []
        for contact in contacts_locations.get("centralContacts", []):
            if isinstance(contact, dict):
                contacts_list.append({
                    "name": contact.get("name", ""),
                    "role": contact.get("role", ""),
                    "phone": contact.get("phone", ""),
                    "email": contact.get("email", "")
                })
        
        # Build detailed response
        detail = {
            "nct_id": identification.get("nctId", ""),
            "brief_title": identification.get("briefTitle", ""),
            "official_title": identification.get("officialTitle", ""),
            "summary": description.get("briefSummary", ""),
            "detailed_description": description.get("detailedDescription", ""),
            "status": status_module.get("overallStatus", ""),
            "phase": _normalize_phase(design.get("phases", [])),
            "study_type": design.get("studyType", ""),
            "conditions": conditions_list,
            "interventions": interventions_list,
            "outcomes": outcomes_list,
            "enrollment": {
                "target": eligibility.get("eligibilityModule", {}).get("samplingMethod", ""),
                "actual": status_module.get("enrollmentInfo", {}).get("count", 0) if isinstance(status_module.get("enrollmentInfo"), dict) else 0,
                "eligibility_criteria": eligibility.get("eligibilityCriteria", "")
            },
            "locations": locations_list,
            "contacts": contacts_list,
            "sponsor": {
                "lead": sponsor.get("leadSponsor", {}).get("name", "") if isinstance(sponsor.get("leadSponsor"), dict) else "",
                "collaborators": [c.get("name", "") for c in sponsor.get("collaborators", []) if isinstance(c, dict)]
            },
            "dates": {
                "start_date": _normalize_date(status_module.get("startDateStruct", {}).get("date", "")) if isinstance(status_module.get("startDateStruct"), dict) else None,
                "completion_date": _normalize_date(status_module.get("completionDateStruct", {}).get("date", "")) if isinstance(status_module.get("completionDateStruct"), dict) else None,
                "primary_completion_date": _normalize_date(status_module.get("primaryCompletionDateStruct", {}).get("date", "")) if isinstance(status_module.get("primaryCompletionDateStruct"), dict) else None
            },
            "references": {
                "references": [r.get("citation", "") for r in references.get("references", []) if isinstance(r, dict)]
            },
            "url": f"https://clinicaltrials.gov/study/{identification.get('nctId', '')}"
        }
        
        # Cache result with 24 hour TTL (trial details change infrequently)
        cache.set(cache_key, detail, ttl_seconds=24 * 60 * 60)
        
        return detail
        
    except ApiError as e:
        # Re-raise ApiError as-is (already standardized)
        raise
    except (KeyError, ValueError) as e:
        raise ApiError(
            message=f"Failed to parse API response: {str(e)}",
            original_error=e
        )
    except Exception as e:
        # Map unexpected errors to structured errors
        mapped_error = map_upstream_error(e)
        if mapped_error:
            raise mapped_error
        raise ApiError(
            message=f"Failed to get trial detail: {str(e)}",
            original_error=e
        )


def _normalize_phase(phases: List[str]) -> str:
    """Normalize phase list to a single string."""
    if not phases:
        return "N/A"
    
    phase_map = {
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
        "NA": "N/A",
        "EARLY_PHASE1": "Early Phase 1",
        "NOT_APPLICABLE": "N/A"
    }
    
    normalized = []
    for phase in phases:
        if isinstance(phase, str):
            normalized.append(phase_map.get(phase.upper(), phase))
        else:
            normalized.append(str(phase))
    
    if len(normalized) == 1:
        return normalized[0]
    elif len(normalized) > 1:
        return ", ".join(normalized)
    else:
        return "N/A"


def _normalize_date(date_str: str) -> Optional[str]:
    """Normalize date string to ISO 8601 format (YYYY-MM-DD)."""
    if not date_str:
        return None
    
    # Try to parse common date formats
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If parsing fails, return as-is (let schema validation handle it)
    return date_str

