"""
ClinicalTrials.gov MCP Server

Provides tools for searching and retrieving clinical trials data.
"""

from .clinical_trials_api import search_trials, get_trial_detail

__all__ = ["search_trials", "get_trial_detail"]

