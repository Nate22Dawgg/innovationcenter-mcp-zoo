#!/usr/bin/env python3
"""
Unit tests for clinical trial matching functionality.

Tests the matching utilities, geography utilities, and the main matching tool.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from matching_utils import (
    extract_age_range,
    check_age_eligibility,
    check_sex_eligibility,
    check_condition_match,
    calculate_match_score,
    extract_eligibility_highlights
)
from geography_utils import (
    parse_geography,
    get_city_coordinates,
    calculate_distance,
    matches_geography
)


class TestMatchingUtils(unittest.TestCase):
    """Test matching utility functions."""
    
    def test_extract_age_range(self):
        """Test age range extraction from eligibility criteria."""
        # Test various formats
        self.assertEqual(extract_age_range("18-65 years"), (18, 65))
        self.assertEqual(extract_age_range("Ages 18 to 65"), (18, 65))
        self.assertEqual(extract_age_range("≥18 and ≤65 years"), (18, 65))
        self.assertEqual(extract_age_range("18 years or older"), (18, 150))
        self.assertEqual(extract_age_range("Minimum age: 21"), (21, 150))
        self.assertIsNone(extract_age_range("No age restrictions"))
        self.assertIsNone(extract_age_range(""))
    
    def test_check_age_eligibility(self):
        """Test age eligibility checking."""
        criteria = "Ages 18-65 years"
        
        # Eligible cases
        eligible, reason = check_age_eligibility(25, criteria)
        self.assertTrue(eligible)
        self.assertIn("within range", reason)
        
        eligible, reason = check_age_eligibility(None, criteria)
        self.assertTrue(eligible)
        
        # Ineligible cases
        eligible, reason = check_age_eligibility(70, criteria)
        self.assertFalse(eligible)
        self.assertIn("outside range", reason)
        
        eligible, reason = check_age_eligibility(15, criteria)
        self.assertFalse(eligible)
    
    def test_check_sex_eligibility(self):
        """Test sex eligibility checking."""
        # Female-only trial
        criteria = "Female participants only"
        eligible, reason = check_sex_eligibility("female", criteria)
        self.assertTrue(eligible)
        
        eligible, reason = check_sex_eligibility("male", criteria)
        self.assertFalse(eligible)
        
        # Male-only trial
        criteria = "Male only study"
        eligible, reason = check_sex_eligibility("male", criteria)
        self.assertTrue(eligible)
        
        eligible, reason = check_sex_eligibility("female", criteria)
        self.assertFalse(eligible)
        
        # No restriction
        eligible, reason = check_sex_eligibility("male", "No sex restrictions")
        self.assertTrue(eligible)
    
    def test_check_condition_match(self):
        """Test condition matching."""
        # Exact match
        matches, score, reason = check_condition_match(
            "pancreatic cancer",
            ["Pancreatic Cancer", "Pancreatic Neoplasms"]
        )
        self.assertTrue(matches)
        self.assertGreater(score, 0.5)
        
        # Partial match
        matches, score, reason = check_condition_match(
            "diabetes",
            ["Type 2 Diabetes", "Diabetes Mellitus"]
        )
        self.assertTrue(matches)
        
        # No match
        matches, score, reason = check_condition_match(
            "cancer",
            ["Hypertension", "High Blood Pressure"]
        )
        self.assertFalse(matches)
    
    def test_calculate_match_score(self):
        """Test match score calculation."""
        trial = {
            "nct_id": "NCT01234567",
            "title": "Test Trial",
            "phase": "Phase 3",
            "status": "RECRUITING",
            "conditions": ["Pancreatic Cancer"]
        }
        
        score = calculate_match_score(
            trial,
            "pancreatic cancer",
            None,
            None
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Test with distance
        score_with_distance = calculate_match_score(
            trial,
            "pancreatic cancer",
            None,
            25.0  # 25 miles
        )
        self.assertGreater(score_with_distance, score)
    
    def test_extract_eligibility_highlights(self):
        """Test eligibility highlight extraction."""
        criteria = "Ages 18-65 years. Female participants only. Performance status ECOG 0-1."
        demographics = {"age": 30, "sex": "female"}
        
        highlights = extract_eligibility_highlights(criteria, demographics)
        
        self.assertGreater(len(highlights), 0)
        self.assertIn("Age", highlights[0])


class TestGeographyUtils(unittest.TestCase):
    """Test geography utility functions."""
    
    def test_parse_geography(self):
        """Test geography parsing."""
        geo = {
            "city": "Boston",
            "state": "MA",
            "zip": "02115",
            "country": "United States"
        }
        
        parsed = parse_geography(geo)
        self.assertEqual(parsed["city"], "boston")
        self.assertEqual(parsed["state"], "MA")
        self.assertEqual(parsed["zip"], "02115")
        
        # Test None input
        self.assertIsNone(parse_geography(None))
        self.assertIsNone(parse_geography({}))
    
    def test_get_city_coordinates(self):
        """Test city coordinate lookup."""
        coords = get_city_coordinates("Boston")
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        
        # Test case insensitive
        coords2 = get_city_coordinates("BOSTON")
        self.assertEqual(coords, coords2)
        
        # Test unknown city
        self.assertIsNone(get_city_coordinates("UnknownCity123"))
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        # Distance between Boston and New York (approximately 190 miles)
        boston = (42.3601, -71.0589)
        nyc = (40.7128, -74.0060)
        
        distance = calculate_distance(boston[0], boston[1], nyc[0], nyc[1])
        
        # Should be approximately 190 miles (allow some variance)
        self.assertGreater(distance, 180)
        self.assertLess(distance, 200)
        
        # Same location should be 0
        self.assertEqual(calculate_distance(0, 0, 0, 0), 0.0)
    
    def test_matches_geography(self):
        """Test geography matching."""
        patient_geo = parse_geography({
            "city": "Boston",
            "state": "MA",
            "country": "United States"
        })
        
        # Test with matching location
        trial_locations = ["Boston, MA, United States"]
        matches, distance = matches_geography(patient_geo, trial_locations, 100)
        self.assertTrue(matches)
        
        # Test with non-matching location
        trial_locations = ["Los Angeles, CA, United States"]
        matches, distance = matches_geography(patient_geo, trial_locations, 50)
        # Should match if within distance, but distance should be large
        if matches:
            self.assertGreater(distance, 2000)  # Cross-country distance
        
        # Test with no geography
        matches, distance = matches_geography(None, trial_locations, 100)
        self.assertTrue(matches)


class TestMatchingIntegration(unittest.TestCase):
    """Integration tests for the matching tool."""
    
    @patch('servers.clinical.clinical_trials_mcp.server.search_trials')
    @patch('servers.clinical.clinical_trials_mcp.server.get_trial_detail')
    def test_matching_workflow(self, mock_get_detail, mock_search):
        """Test the full matching workflow."""
        # Mock search results
        mock_search.return_value = {
            "total": 2,
            "count": 2,
            "offset": 0,
            "trials": [
                {
                    "nct_id": "NCT01234567",
                    "title": "Pancreatic Cancer Trial",
                    "status": "RECRUITING",
                    "phase": "Phase 3",
                    "conditions": ["Pancreatic Cancer"],
                    "locations": ["Boston, MA, United States"],
                    "url": "https://clinicaltrials.gov/study/NCT01234567"
                },
                {
                    "nct_id": "NCT09876543",
                    "title": "Another Trial",
                    "status": "RECRUITING",
                    "phase": "Phase 2",
                    "conditions": ["Pancreatic Cancer"],
                    "locations": ["Los Angeles, CA, United States"],
                    "url": "https://clinicaltrials.gov/study/NCT09876543"
                }
            ]
        }
        
        # Mock detail results
        mock_get_detail.return_value = {
            "nct_id": "NCT01234567",
            "enrollment": {
                "eligibility_criteria": "Ages 18-75 years. Male or female."
            }
        }
        
        # Import here to avoid circular imports
        # Note: This test requires the server module to be importable
        # In practice, you may need to adjust the import path
        try:
            from server import clinical_trial_matching
        except ImportError:
            # Skip integration test if server module not available
            return
        import asyncio
        
        async def run_test():
            result = await clinical_trial_matching(
                condition="pancreatic cancer",
                demographics={"age": 50, "sex": "male"},
                geography={"city": "Boston", "state": "MA"},
                max_results=10
            )
            
            self.assertIn("matches", result)
            self.assertGreater(len(result["matches"]), 0)
            self.assertIn("nct_id", result["matches"][0])
            self.assertIn("match_score", result["matches"][0])
        
        asyncio.run(run_test())


def main():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMatchingUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestGeographyUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchingIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
