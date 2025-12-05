#!/usr/bin/env python3
"""
Test script for clinical_trials_api.py

Tests both search_trials() and get_trial_detail() functions.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent))

from clinical_trials_api import search_trials, get_trial_detail


def test_search_trials():
    """Test the search_trials function."""
    print("=" * 60)
    print("Testing clinical_trials.search")
    print("=" * 60)
    
    try:
        # Search for pancreatic cancer trials
        params = {
            "condition": "pancreatic cancer",
            "max_results": 3
        }
        
        # Note: Our API uses "limit" not "max_results"
        if "max_results" in params:
            params["limit"] = params.pop("max_results")
        
        print(f"\nSearching with params: {json.dumps(params, indent=2)}")
        results = search_trials(params)
        
        print(f"\n✅ Search successful!")
        print(f"   Total trials found: {results.get('total', 0)}")
        print(f"   Trials returned: {results.get('count', 0)}")
        print(f"   Offset: {results.get('offset', 0)}")
        
        trials = results.get("trials", [])
        if trials:
            print(f"\n   First trial:")
            first_trial = trials[0]
            print(f"      NCT ID: {first_trial.get('nct_id')}")
            print(f"      Title: {first_trial.get('title', 'N/A')[:80]}...")
            print(f"      Status: {first_trial.get('status', 'N/A')}")
            print(f"      Phase: {first_trial.get('phase', 'N/A')}")
            
            # Return first NCT ID for detail test
            return first_trial.get("nct_id")
        else:
            print("\n   ⚠️  No trials returned")
            return None
            
    except Exception as e:
        print(f"\n❌ Search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_get_trial_detail(nct_id: str):
    """Test the get_trial_detail function."""
    print("\n" + "=" * 60)
    print("Testing clinical_trials.get_detail")
    print("=" * 60)
    
    if not nct_id:
        print("\n⚠️  Skipping detail test - no NCT ID available from search")
        return
    
    try:
        print(f"\nFetching details for: {nct_id}")
        detail = get_trial_detail(nct_id)
        
        print(f"\n✅ Detail retrieval successful!")
        print(f"\n   NCT ID: {detail.get('nct_id')}")
        print(f"   Brief Title: {detail.get('brief_title', 'N/A')[:80]}...")
        print(f"   Status: {detail.get('status', 'N/A')}")
        print(f"   Phase: {detail.get('phase', 'N/A')}")
        print(f"   Study Type: {detail.get('study_type', 'N/A')}")
        
        conditions = detail.get("conditions", [])
        if conditions:
            print(f"   Conditions ({len(conditions)}): {', '.join(conditions[:3])}")
            if len(conditions) > 3:
                print(f"      ... and {len(conditions) - 3} more")
        
        interventions = detail.get("interventions", [])
        if interventions:
            print(f"   Interventions ({len(interventions)}):")
            for interv in interventions[:3]:
                if isinstance(interv, dict):
                    print(f"      - {interv.get('name', 'N/A')} ({interv.get('type', 'N/A')})")
                else:
                    print(f"      - {interv}")
        
        locations = detail.get("locations", [])
        if locations:
            print(f"   Locations ({len(locations)}):")
            for loc in locations[:3]:
                if isinstance(loc, dict):
                    loc_str = ", ".join(filter(None, [
                        loc.get("city"),
                        loc.get("state"),
                        loc.get("country")
                    ]))
                    print(f"      - {loc_str}")
        
        enrollment = detail.get("enrollment", {})
        if enrollment:
            actual = enrollment.get("actual", 0)
            if actual:
                print(f"   Enrollment: {actual} participants")
        
        print(f"\n   URL: {detail.get('url', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Detail retrieval failed: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("🧪 Testing ClinicalTrials.gov API Implementation")
    print()
    
    # Test search
    nct_id = test_search_trials()
    
    # Test get detail if we have an NCT ID
    if nct_id:
        test_get_trial_detail(nct_id)
    else:
        # Try with a known NCT ID if search didn't return one
        print("\n" + "=" * 60)
        print("Testing with a known NCT ID (NCT00002540)")
        print("=" * 60)
        test_get_trial_detail("NCT00002540")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

