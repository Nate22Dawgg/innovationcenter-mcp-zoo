"""
Shared pytest fixtures and configuration for MCP Zoo test suite.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return the fixtures directory."""
    return PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def vcr_cassettes_dir() -> Path:
    """Return the VCR cassettes directory."""
    cassettes_dir = PROJECT_ROOT / "tests" / "fixtures" / "vcr_cassettes"
    cassettes_dir.mkdir(parents=True, exist_ok=True)
    return cassettes_dir


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    # Store original env vars
    original_env = os.environ.copy()
    
    # Clear API keys to prevent accidental real API calls
    api_keys_to_clear = [
        "TURQUOISE_API_KEY",
        "BATCHDATA_API_KEY",
        "SP_GLOBAL_API_KEY",
        "CLINICAL_TRIALS_API_KEY",
        "PUBMED_API_KEY",
        "FDA_API_KEY",
    ]
    
    for key in api_keys_to_clear:
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    server = Mock()
    server.name = "test-server"
    server.list_tools = Mock(return_value=[])
    server.call_tool = Mock(return_value=[])
    return server


@pytest.fixture
def sample_tool_response() -> Dict[str, Any]:
    """Sample tool response structure."""
    return {
        "status": "success",
        "data": {},
        "count": 0,
    }


@pytest.fixture
def load_fixture(fixtures_dir: Path):
    """Helper fixture to load JSON fixtures."""
    def _load(name: str) -> Dict[str, Any]:
        fixture_path = fixtures_dir / f"{name}.json"
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")
        with open(fixture_path, "r") as f:
            return json.load(f)
    return _load


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": []}
        mock_response.text = json.dumps({"status": "success", "data": []})
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for API calls."""
    with patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": []}
        mock_response.text = json.dumps({"status": "success", "data": []})
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def sample_clinical_trial():
    """Sample clinical trial data."""
    return {
        "nct_id": "NCT01234567",
        "title": "Test Clinical Trial",
        "status": "Recruiting",
        "phase": "Phase 3",
        "condition": "Test Condition",
        "intervention": "Test Intervention",
    }


@pytest.fixture
def sample_hospital_price():
    """Sample hospital price data."""
    return {
        "hospital_id": "test_hospital_123",
        "hospital_name": "Test Hospital",
        "cpt_code": "99213",
        "price": 150.00,
        "location": "New York, NY",
    }


@pytest.fixture
def sample_claim_line_item():
    """Sample claim line item data."""
    return {
        "cpt_code": "99213",
        "units": 1,
        "charge_amount": 150.00,
        "allowed_amount": 120.00,
        "paid_amount": 100.00,
    }


@pytest.fixture
def sample_biotech_company():
    """Sample biotech company data."""
    return {
        "company_name": "Test Biotech Inc",
        "therapeutic_area": "Oncology",
        "stage": "Phase 3",
        "location": "Boston, MA",
        "pipeline_count": 5,
    }


@pytest.fixture
def sample_property():
    """Sample real estate property data."""
    return {
        "address": "123 Main St, New York, NY 10001",
        "property_id": "test_prop_123",
        "assessed_value": 500000,
        "tax_amount": 10000,
    }


@pytest.fixture
def sample_nhanes_dataset():
    """Sample NHANES dataset info."""
    return {
        "dataset": "demographics",
        "cycle": "2017-2018",
        "variables": ["RIDAGEYR", "RIAGENDR", "RIDRETH3"],
        "row_count": 1000,
    }


@pytest.fixture
def sample_pubmed_article():
    """Sample PubMed article data."""
    return {
        "pmid": "12345678",
        "title": "Test Article Title",
        "authors": ["Author 1", "Author 2"],
        "journal": "Test Journal",
        "year": 2023,
    }


@pytest.fixture
def sample_fda_drug():
    """Sample FDA drug data."""
    return {
        "application_number": "NDA123456",
        "brand_name": "Test Drug",
        "generic_name": "test_drug_generic",
        "manufacturer": "Test Pharma Inc",
    }

