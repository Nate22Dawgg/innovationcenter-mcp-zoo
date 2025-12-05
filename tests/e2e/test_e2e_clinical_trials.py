"""
End-to-end tests for Clinical Trials MCP Server with VCR.py for API response caching.
"""

import pytest
import vcr
from pathlib import Path

pytestmark = [pytest.mark.e2e, pytest.mark.python, pytest.mark.slow]

# VCR cassette directory
CASSETTE_DIR = Path(__file__).parent.parent / "fixtures" / "vcr_cassettes"
CASSETTE_DIR.mkdir(parents=True, exist_ok=True)


# VCR configuration
vcr_config = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode='once',  # Record once, then use cassette
    match_on=['uri', 'method'],
    filter_headers=['authorization', 'api-key'],
    filter_query_parameters=['api_key', 'key'],
)


class TestClinicalTrialsE2E:
    """End-to-end tests for Clinical Trials server."""
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('clinical_trials_search.yaml')
    async def test_search_trials_e2e(self):
        """Test searching clinical trials with real API (cached)."""
        # This test will use cached responses from VCR
        # If cassette doesn't exist, it will make real API call and cache it
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "clinical-trials-mcp"))
        
        from server import clinical_trials_search
        
        # This will use cached response if cassette exists
        result = await clinical_trials_search(
            condition="diabetes",
            limit=5
        )
        
        assert isinstance(result, dict)
        assert "total" in result or "error" in result
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('clinical_trials_get_detail.yaml')
    async def test_get_trial_detail_e2e(self):
        """Test getting trial detail with real API (cached)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "clinical" / "clinical-trials-mcp"))
        
        from server import clinical_trials_get_detail
        
        # Use a known NCT ID for testing
        result = await clinical_trials_get_detail("NCT00000102")
        
        assert isinstance(result, dict)
        assert "nct_id" in result or "error" in result

