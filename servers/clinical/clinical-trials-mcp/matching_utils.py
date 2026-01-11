"""
Eligibility matching utilities for clinical trial matching.

Provides functions for filtering and scoring trials based on patient demographics
and eligibility criteria.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime


def extract_age_range(criteria_text: str) -> Optional[Tuple[int, int]]:
    """
    Extract age range from eligibility criteria text.
    
    Args:
        criteria_text: Eligibility criteria text
    
    Returns:
        Tuple of (min_age, max_age) or None if not found
    """
    if not criteria_text:
        return None
    
    # Common patterns: "18 years", "18-65 years", "≥18", "18 to 65"
    patterns = [
        r'(\d+)\s*-\s*(\d+)\s*years?',
        r'(\d+)\s+to\s+(\d+)\s*years?',
        r'ages?\s+(\d+)\s*-\s*(\d+)',
        r'≥\s*(\d+)\s*and\s*≤\s*(\d+)',
        r'(\d+)\s*to\s*(\d+)\s*years?\s*old',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, criteria_text, re.IGNORECASE)
        if match:
            try:
                min_age = int(match.group(1))
                max_age = int(match.group(2))
                return (min_age, max_age)
            except (ValueError, IndexError):
                continue
    
    # Single age patterns: "≥18", "18 years or older"
    single_patterns = [
        r'≥\s*(\d+)\s*years?',
        r'(\d+)\s*years?\s*or\s*older',
        r'minimum\s*age[:\s]+(\d+)',
    ]
    
    for pattern in single_patterns:
        match = re.search(pattern, criteria_text, re.IGNORECASE)
        if match:
            try:
                min_age = int(match.group(1))
                return (min_age, 150)  # Assume no upper limit
            except (ValueError, IndexError):
                continue
    
    return None


def check_age_eligibility(
    patient_age: Optional[int],
    eligibility_criteria: Optional[str]
) -> Tuple[bool, str]:
    """
    Check if patient age matches trial eligibility.
    
    Args:
        patient_age: Patient age in years
        eligibility_criteria: Eligibility criteria text
    
    Returns:
        Tuple of (is_eligible, reason)
    """
    if patient_age is None:
        return (True, "Age not specified")
    
    if not eligibility_criteria:
        return (True, "No age criteria specified")
    
    age_range = extract_age_range(eligibility_criteria)
    if not age_range:
        return (True, "Age criteria not found in eligibility text")
    
    min_age, max_age = age_range
    if min_age <= patient_age <= max_age:
        return (True, f"Age {patient_age} within range {min_age}-{max_age}")
    else:
        return (False, f"Age {patient_age} outside range {min_age}-{max_age}")


def check_sex_eligibility(
    patient_sex: Optional[str],
    eligibility_criteria: Optional[str]
) -> Tuple[bool, str]:
    """
    Check if patient sex matches trial eligibility.
    
    Args:
        patient_sex: Patient sex ("male", "female", "all")
        eligibility_criteria: Eligibility criteria text
    
    Returns:
        Tuple of (is_eligible, reason)
    """
    if not patient_sex or patient_sex.lower() == "all":
        return (True, "Sex not restricted")
    
    if not eligibility_criteria:
        return (True, "No sex criteria specified")
    
    criteria_lower = eligibility_criteria.lower()
    patient_sex_lower = patient_sex.lower()
    
    # Check for explicit exclusions
    if patient_sex_lower == "male":
        if "female only" in criteria_lower or "women only" in criteria_lower:
            return (False, "Trial is for females only")
    elif patient_sex_lower == "female":
        if "male only" in criteria_lower or "men only" in criteria_lower:
            return (False, "Trial is for males only")
    
    # Check for inclusions
    if patient_sex_lower == "male" and ("male" in criteria_lower or "men" in criteria_lower):
        return (True, "Male eligible")
    if patient_sex_lower == "female" and ("female" in criteria_lower or "women" in criteria_lower):
        return (True, "Female eligible")
    
    # If no explicit restriction found, assume eligible
    return (True, "Sex criteria not explicitly restrictive")


def check_condition_match(
    patient_condition: str,
    trial_conditions: List[str]
) -> Tuple[bool, float, str]:
    """
    Check if patient condition matches trial conditions.
    
    Args:
        patient_condition: Patient's condition description
        trial_conditions: List of trial condition names
    
    Returns:
        Tuple of (matches, match_score, reason)
        match_score: 0.0-1.0 indicating match quality
    """
    if not trial_conditions:
        return (False, 0.0, "No conditions specified")
    
    patient_condition_lower = patient_condition.lower()
    
    # Extract key terms from patient condition
    patient_terms = set(re.findall(r'\b\w+\b', patient_condition_lower))
    
    best_match_score = 0.0
    best_match_reason = ""
    
    for trial_condition in trial_conditions:
        trial_condition_lower = trial_condition.lower()
        trial_terms = set(re.findall(r'\b\w+\b', trial_condition_lower))
        
        # Calculate overlap
        if patient_terms and trial_terms:
            overlap = len(patient_terms & trial_terms)
            total_unique = len(patient_terms | trial_terms)
            score = overlap / total_unique if total_unique > 0 else 0.0
            
            # Boost score for exact or near-exact matches
            if patient_condition_lower in trial_condition_lower or trial_condition_lower in patient_condition_lower:
                score = min(1.0, score + 0.3)
            
            if score > best_match_score:
                best_match_score = score
                best_match_reason = f"Matches condition: {trial_condition}"
    
    # Consider it a match if score > 0.3
    is_match = best_match_score > 0.3
    
    return (is_match, best_match_score, best_match_reason if is_match else "Condition mismatch")


def calculate_match_score(
    trial: Dict[str, Any],
    patient_condition: str,
    demographics: Optional[Dict[str, Any]],
    distance_miles: Optional[float],
    phase_weights: Dict[str, float] = None
) -> float:
    """
    Calculate overall match score for a trial (0-100).
    
    Args:
        trial: Trial data dictionary
        patient_condition: Patient's condition
        demographics: Patient demographics
        distance_miles: Distance to trial in miles
        phase_weights: Optional weights for different phases
    
    Returns:
        Match score from 0-100
    """
    if phase_weights is None:
        phase_weights = {
            "Phase 3": 1.0,
            "Phase 2": 0.8,
            "Phase 1": 0.6,
            "Phase 4": 0.7,
            "Early Phase 1": 0.5,
            "N/A": 0.4
        }
    
    score = 50.0  # Base score
    
    # Condition match (0-30 points)
    condition_match, condition_score, _ = check_condition_match(
        patient_condition, trial.get("conditions", [])
    )
    if condition_match:
        score += condition_score * 30
    
    # Phase weight (0-20 points)
    phase = trial.get("phase", "N/A")
    phase_weight = phase_weights.get(phase, 0.4)
    score += phase_weight * 20
    
    # Status (0-10 points) - prefer recruiting
    status = trial.get("status", "").lower()
    if "recruiting" in status:
        score += 10
    elif "not yet recruiting" in status:
        score += 7
    elif "active" in status:
        score += 5
    
    # Distance (0-20 points) - closer is better
    if distance_miles is not None:
        if distance_miles <= 25:
            score += 20
        elif distance_miles <= 50:
            score += 15
        elif distance_miles <= 100:
            score += 10
        elif distance_miles <= 200:
            score += 5
    else:
        # No distance info, give moderate score
        score += 10
    
    # Recency (0-10 points) - prefer recently updated
    # This would require last update date, which we may not have
    # For now, skip this component
    
    # Cap at 100
    return min(100.0, max(0.0, score))


def extract_eligibility_highlights(
    eligibility_criteria: Optional[str],
    demographics: Optional[Dict[str, Any]]
) -> List[str]:
    """
    Extract key eligibility highlights relevant to the patient.
    
    Args:
        eligibility_criteria: Full eligibility criteria text
        demographics: Patient demographics
    
    Returns:
        List of highlight strings
    """
    highlights = []
    
    if not eligibility_criteria:
        return highlights
    
    # Extract age range
    age_range = extract_age_range(eligibility_criteria)
    if age_range:
        min_age, max_age = age_range
        highlights.append(f"Age: {min_age}-{max_age} years")
    
    # Extract sex requirements
    criteria_lower = eligibility_criteria.lower()
    if "male only" in criteria_lower or "men only" in criteria_lower:
        highlights.append("Male participants only")
    elif "female only" in criteria_lower or "women only" in criteria_lower:
        highlights.append("Female participants only")
    
    # Look for key inclusion/exclusion terms
    if "biomarker" in criteria_lower or "mutation" in criteria_lower:
        highlights.append("Biomarker/mutation requirements may apply")
    
    if "performance status" in criteria_lower or "ecog" in criteria_lower:
        highlights.append("Performance status requirements")
    
    return highlights[:3]  # Limit to 3 highlights
