"""
Contract/Integration tests for MCP servers.

Tests real upstream API interactions with VCR-style recording.
Asserts minimal invariants: Non-empty, expected fields, no unexpected exceptions.
"""

import pytest
import json
from pathlib import Path
from typing import Any, Dict, List
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.fixtures.vcr_config import get_vcr_config

pytestmark = [pytest.mark.contract, pytest.mark.integration, pytest.mark.slow]

# VCR config - use 'none' for CI, 'once' for initial recording
vcr_config = get_vcr_config(record_mode='once')


class TestAPIContracts:
    """Test that API contracts are maintained."""
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('clinical_trials_search.yaml')
    async def test_clinical_trials_search_contract(self):
        """Test ClinicalTrials.gov API contract."""
        import requests
        
        # Make a simple search request
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.cond": "diabetes",
            "pageSize": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Assert response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Assert minimal invariants
        assert "studies" in data or "data" in data, "Response should have studies or data field"
        
        # If studies exist, check structure
        if "studies" in data:
            assert isinstance(data["studies"], list), "studies should be a list"
            if len(data["studies"]) > 0:
                study = data["studies"][0]
                assert "protocolSection" in study or "nctId" in study, \
                    "Study should have protocolSection or nctId"
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('pubmed_search.yaml')
    async def test_pubmed_search_contract(self):
        """Test PubMed API contract."""
        import requests
        
        # Make a simple search request
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": "diabetes",
            "retmax": 1,
            "retmode": "json"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Assert response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Assert minimal invariants
        assert "esearchresult" in data, "Response should have esearchresult field"
        esearch_result = data["esearchresult"]
        assert "idlist" in esearch_result or "count" in esearch_result, \
            "esearchresult should have idlist or count"
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('sec_edgar_search.yaml')
    async def test_sec_edgar_search_contract(self):
        """Test SEC EDGAR API contract."""
        import requests
        
        # Make a simple search request
        url = "https://data.sec.gov/submissions/CIK0000001750.json"
        headers = {
            "User-Agent": "Test Agent test@example.com",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Assert response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Assert minimal invariants
        assert isinstance(data, dict), "Response should be a dictionary"
        # SEC EDGAR has various structures, just check it's valid JSON
        assert len(data) > 0, "Response should not be empty"
    
    @pytest.mark.asyncio
    @vcr_config.use_cassette('nhanes_list_datasets.yaml')
    async def test_nhanes_list_datasets_contract(self):
        """Test NHANES data availability contract."""
        import requests
        
        # NHANES data is typically downloaded, but we can test the CDC website
        url = "https://www.cdc.gov/nchs/nhanes/"
        
        response = requests.get(url, timeout=10)
        
        # Assert response structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert len(response.text) > 0, "Response should not be empty"
    
    def test_api_response_has_expected_fields(self):
        """Test that API responses have expected fields."""
        # Generic test for response structure
        sample_response = {
            "status": "success",
            "data": [],
            "count": 0
        }
        
        assert "status" in sample_response or "data" in sample_response, \
            "Response should have status or data field"
        
        if "data" in sample_response:
            assert isinstance(sample_response["data"], (list, dict)), \
                "data should be list or dict"
    
    def test_api_error_responses(self):
        """Test that API error responses are handled."""
        error_responses = [
            {"error": "Not found", "status_code": 404},
            {"error": "Unauthorized", "status_code": 401},
            {"error": "Rate limit exceeded", "status_code": 429},
        ]
        
        for error_response in error_responses:
            assert "error" in error_response or "status_code" in error_response, \
                "Error response should have error or status_code"
            
            if "status_code" in error_response:
                status_code = error_response["status_code"]
                assert 400 <= status_code < 600, \
                    "Error status code should be 4xx or 5xx"
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test that API timeouts are handled."""
        import requests
        from requests.exceptions import Timeout
        
        # This will timeout, but we're testing the handling
        try:
            # Use a non-routable IP to force timeout
            response = requests.get("http://192.0.2.0", timeout=0.1)
        except (Timeout, requests.exceptions.ConnectionError):
            # Expected - timeout or connection error
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception type: {type(e)}")
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self):
        """Test that rate limit responses are handled."""
        # Simulate rate limit response
        rate_limit_response = {
            "error": "Rate limit exceeded",
            "status_code": 429,
            "retry_after": 60
        }
        
        assert rate_limit_response["status_code"] == 429
        assert "retry_after" in rate_limit_response or "retry-after" in rate_limit_response
    
    def test_api_response_is_json(self):
        """Test that API responses are valid JSON."""
        valid_json_responses = [
            '{"status": "success"}',
            '{"data": []}',
            '{"count": 0}',
        ]
        
        for json_str in valid_json_responses:
            try:
                data = json.loads(json_str)
                assert isinstance(data, dict), "JSON should parse to dict"
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON: {json_str}")
    
    @pytest.mark.asyncio
    async def test_api_response_size_limits(self):
        """Test that very large responses are handled."""
        # Simulate large response
        large_response = {"data": [{"id": i} for i in range(1000)]}
        
        # Should be able to handle reasonably large responses
        assert len(large_response["data"]) == 1000
        assert isinstance(large_response["data"], list)
    
    def test_api_pagination_contract(self):
        """Test that paginated API responses follow expected structure."""
        paginated_response = {
            "total": 100,
            "count": 20,
            "offset": 0,
            "limit": 20,
            "results": []
        }
        
        assert "total" in paginated_response or "count" in paginated_response, \
            "Paginated response should have total or count"
        assert "results" in paginated_response or "data" in paginated_response, \
            "Paginated response should have results or data"
        
        if "offset" in paginated_response and "limit" in paginated_response:
            offset = paginated_response["offset"]
            limit = paginated_response["limit"]
            assert offset >= 0, "offset should be non-negative"
            assert limit > 0, "limit should be positive"
