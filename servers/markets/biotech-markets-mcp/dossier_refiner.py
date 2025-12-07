"""
Biotech company dossier refiner.

This module provides functions to refine and analyze biotech company dossiers
based on new questions or focus areas, without making new API calls.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artifact_store import get_artifact_store


def _extract_pipeline_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about the pipeline."""
    insights = []
    pipeline = dossier.get("pipeline", [])
    
    if not pipeline:
        insights.append("No pipeline drugs identified")
        return insights
    
    insights.append(f"Company has {len(pipeline)} pipeline drug(s)")
    
    # Count by phase
    phase_counts = {}
    for drug in pipeline:
        latest_phase = drug.get("latest_phase", "Unknown")
        phase_counts[latest_phase] = phase_counts.get(latest_phase, 0) + 1
    
    if phase_counts:
        phase_summary = ", ".join([f"{count} in {phase}" for phase, count in phase_counts.items()])
        insights.append(f"Pipeline distribution: {phase_summary}")
    
    # Check for late-stage
    late_stage = [d for d in pipeline if d.get("latest_phase") in ["Phase 3", "NDA", "Approved"]]
    if late_stage:
        insights.append(f"{len(late_stage)} late-stage drug(s) in pipeline")
    else:
        insights.append("No late-stage drugs in pipeline")
    
    return insights


def _extract_financial_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about financials."""
    insights = []
    financial = dossier.get("financial_summary", {})
    
    if financial.get("has_ipo"):
        insights.append("Company is publicly traded")
        if financial.get("exchange"):
            insights.append(f"Traded on {financial['exchange']}")
        if financial.get("ipo_date"):
            insights.append(f"IPO date: {financial['ipo_date']}")
    else:
        insights.append("Company is private (limited public financial data)")
    
    if financial.get("market_cap"):
        market_cap_billions = financial["market_cap"] / 1e9
        insights.append(f"Market cap: ${market_cap_billions:.2f}B")
    
    if financial.get("revenue"):
        revenue_millions = financial["revenue"] / 1e6
        insights.append(f"Revenue: ${revenue_millions:.2f}M")
    
    if financial.get("runway_months"):
        insights.append(f"Estimated cash runway: {financial['runway_months']} months")
    
    if financial.get("filing_count", 0) > 0:
        insights.append(f"{financial['filing_count']} SEC filing(s) on record")
    
    return insights


def _extract_risk_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about risks."""
    insights = []
    risk_flags = dossier.get("risk_flags", [])
    
    if not risk_flags:
        insights.append("No major risk flags identified")
    else:
        insights.append(f"{len(risk_flags)} risk flag(s) identified:")
        for flag in risk_flags:
            insights.append(f"  - {flag}")
    
    return insights


def _extract_trials_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about clinical trials."""
    insights = []
    trials_summary = dossier.get("trials_summary", {})
    
    total = trials_summary.get("total_trials", 0)
    active = trials_summary.get("active_trials", 0)
    completed = trials_summary.get("completed_trials", 0)
    
    insights.append(f"Total clinical trials: {total}")
    insights.append(f"Active trials: {active}")
    insights.append(f"Completed trials: {completed}")
    
    phase_dist = trials_summary.get("phase_distribution", {})
    if phase_dist:
        phase_summary = ", ".join([f"{count} {phase}" for phase, count in phase_dist.items()])
        insights.append(f"Phase distribution: {phase_summary}")
    
    return insights


def _extract_publications_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about publications."""
    insights = []
    publications = dossier.get("publications", [])
    
    if not publications:
        insights.append("No recent publications found")
    else:
        insights.append(f"{len(publications)} recent publication(s) found")
        
        # Count by year if available
        years = {}
        for pub in publications:
            pub_date = pub.get("pub_date", "")
            if pub_date and len(pub_date) >= 4:
                year = pub_date[:4]
                years[year] = years.get(year, 0) + 1
        
        if years:
            year_summary = ", ".join([f"{count} in {year}" for year, count in sorted(years.items(), reverse=True)[:3]])
            insights.append(f"Publication timeline: {year_summary}")
    
    return insights


def _extract_investors_insights(dossier: Dict[str, Any]) -> List[str]:
    """Extract insights about investors."""
    insights = []
    investors = dossier.get("investors", [])
    
    if not investors:
        insights.append("No investor information available")
    else:
        insights.append(f"{len(investors)} investor(s) identified")
        # List first few
        for investor in investors[:5]:
            name = investor.get("name", "Unknown")
            investor_type = investor.get("type", "")
            if investor_type:
                insights.append(f"  - {name} ({investor_type})")
            else:
                insights.append(f"  - {name}")
    
    return insights


def _answer_question(dossier: Dict[str, Any], question: str) -> tuple[str, List[str]]:
    """
    Answer a question based on the dossier.
    
    Args:
        dossier: Dossier data
        question: Question to answer
    
    Returns:
        Tuple of (summary text, key insights)
    """
    question_lower = question.lower()
    insights = []
    
    # Route to appropriate extractor based on question keywords
    if any(word in question_lower for word in ["pipeline", "drug", "compound", "development"]):
        insights.extend(_extract_pipeline_insights(dossier))
    
    if any(word in question_lower for word in ["financial", "revenue", "cash", "ipo", "market cap"]):
        insights.extend(_extract_financial_insights(dossier))
    
    if any(word in question_lower for word in ["risk", "concern", "warning", "flag"]):
        insights.extend(_extract_risk_insights(dossier))
    
    if any(word in question_lower for word in ["trial", "clinical", "study"]):
        insights.extend(_extract_trials_insights(dossier))
    
    if any(word in question_lower for word in ["publication", "paper", "research"]):
        insights.extend(_extract_publications_insights(dossier))
    
    if any(word in question_lower for word in ["investor", "backer", "funding"]):
        insights.extend(_extract_investors_insights(dossier))
    
    # If no specific keywords matched, provide general summary
    if not insights:
        insights.extend(_extract_pipeline_insights(dossier))
        insights.extend(_extract_financial_insights(dossier))
        insights.extend(_extract_risk_insights(dossier))
    
    # Generate summary text
    summary = f"Based on the dossier for {dossier.get('company_name', 'the company')}:\n\n"
    summary += "\n".join(insights)
    
    return summary, insights


async def refine_biotech_dossier(
    dossier: Optional[Dict[str, Any]] = None,
    dossier_id: Optional[str] = None,
    new_question: Optional[str] = None,
    focus_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Refine a biotech company dossier based on a question or focus areas.
    
    This function does not make new API calls; it analyzes the existing dossier
    to answer questions or focus on specific areas.
    
    Args:
        dossier: Full dossier object (if provided, dossier_id is ignored)
        dossier_id: Reference ID of stored dossier artifact
        new_question: New question to answer based on the dossier
        focus_areas: Specific areas to focus on (e.g., ['pipeline', 'financials'])
    
    Returns:
        Refined dossier with summary and insights
    """
    # Get dossier
    if dossier:
        source_dossier = dossier
        used_cached = False
    elif dossier_id:
        artifact_store = get_artifact_store()
        source_dossier = artifact_store.get(dossier_id)
        if not source_dossier:
            from common.errors import ErrorCode, McpError
            raise McpError(
                code=ErrorCode.NOT_FOUND,
                message=f"Dossier artifact not found: {dossier_id}",
                details={"dossier_id": dossier_id}
            )
        used_cached = True
    else:
        from common.errors import ErrorCode, McpError
        raise McpError(
            code=ErrorCode.BAD_REQUEST,
            message="Either dossier or dossier_id must be provided",
            details={}
        )
    
    # Determine focus areas
    if focus_areas is None:
        focus_areas = []
    
    # Extract insights based on focus areas or question
    all_insights = []
    focus_areas_covered = []
    
    if new_question:
        summary, insights = _answer_question(source_dossier, new_question)
        all_insights.extend(insights)
        focus_areas_covered.append("question_answered")
    else:
        # Focus on specific areas
        if not focus_areas or "pipeline" in focus_areas:
            all_insights.extend(_extract_pipeline_insights(source_dossier))
            focus_areas_covered.append("pipeline")
        
        if not focus_areas or "financials" in focus_areas:
            all_insights.extend(_extract_financial_insights(source_dossier))
            focus_areas_covered.append("financials")
        
        if not focus_areas or "risks" in focus_areas:
            all_insights.extend(_extract_risk_insights(source_dossier))
            focus_areas_covered.append("risks")
        
        if not focus_areas or "trials" in focus_areas:
            all_insights.extend(_extract_trials_insights(source_dossier))
            focus_areas_covered.append("trials")
        
        if not focus_areas or "publications" in focus_areas:
            all_insights.extend(_extract_publications_insights(source_dossier))
            focus_areas_covered.append("publications")
        
        if not focus_areas or "investors" in focus_areas:
            all_insights.extend(_extract_investors_insights(source_dossier))
            focus_areas_covered.append("investors")
        
        # Generate summary
        summary = f"Analysis of {source_dossier.get('company_name', 'the company')} dossier:\n\n"
        summary += "\n".join(all_insights)
    
    # Create refined dossier (copy of original with metadata)
    refined_dossier = source_dossier.copy()
    refined_dossier["metadata"] = refined_dossier.get("metadata", {}).copy()
    refined_dossier["metadata"]["refined_at"] = datetime.utcnow().isoformat() + "Z"
    if new_question:
        refined_dossier["metadata"]["refinement_question"] = new_question
    if focus_areas:
        refined_dossier["metadata"]["focus_areas"] = focus_areas
    
    return {
        "refined_dossier": refined_dossier,
        "summary": summary,
        "key_insights": all_insights,
        "focus_areas_covered": focus_areas_covered,
        "metadata": {
            "refined_at": datetime.utcnow().isoformat() + "Z",
            "question": new_question,
            "used_cached_dossier": used_cached
        }
    }
