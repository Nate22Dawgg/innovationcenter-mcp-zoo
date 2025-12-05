# Testing Guide for MCP Zoo

This directory contains comprehensive test suites for all MCP servers in the innovationcenter-mcp-zoo repository.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual tools
├── integration/       # Integration tests for server startup
├── e2e/              # End-to-end tests with real API calls (cached)
├── fixtures/         # Mock data and VCR cassettes
│   ├── vcr_cassettes/  # Cached API responses
│   └── *.json         # Sample response data
├── conftest.py       # Shared pytest fixtures
└── README.md         # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual tool functions in isolation
- Use mocks to avoid real API calls
- Fast execution
- Test error handling and edge cases

### Integration Tests (`tests/integration/`)
- Test server initialization and startup
- Verify tool registration
- Test server configuration

### End-to-End Tests (`tests/e2e/`)
- Test real API interactions
- Use VCR.py to cache responses
- Slower execution
- Verify actual API integration

## Running Tests

### Install Test Dependencies

```bash
pip install -r tests/requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only
pytest tests/e2e/ -m e2e
```

### Run Tests for Specific Server

```bash
# Clinical Trials
pytest tests/unit/test_clinical_trials.py

# NHANES
pytest tests/unit/test_nhanes.py

# Hospital Pricing
pytest tests/unit/test_hospital_pricing.py

# Claims/EDI
pytest tests/unit/test_claims_edi.py

# Biotech Markets
pytest tests/unit/test_biotech_markets.py

# Real Estate
pytest tests/unit/test_real_estate.py
```

### Run with Coverage

```bash
pytest --cov=servers --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

## Test Markers

Tests are marked with categories for easy filtering:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_api_key` - Tests requiring API keys
- `@pytest.mark.python` - Python-based servers
- `@pytest.mark.typescript` - TypeScript-based servers

Example:
```bash
# Run only fast unit tests
pytest -m "unit and not slow"
```

## VCR.py for API Response Caching

E2E tests use VCR.py to cache API responses, avoiding:
- Rate limiting
- Network dependencies
- Cost from API calls
- Flaky tests due to network issues

### Recording New Cassettes

When adding new E2E tests:

1. First run will make real API calls and record responses
2. Subsequent runs use cached responses
3. Cassettes are stored in `tests/fixtures/vcr_cassettes/`

### Updating Cassettes

To update cached responses:

```python
from tests.fixtures.vcr_config import get_vcr_config

vcr_config = get_vcr_config(record_mode='all')
```

Then run tests to re-record all interactions.

## Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import patch, Mock

pytestmark = [pytest.mark.unit, pytest.mark.python]

class TestMyServer:
    @pytest.mark.asyncio
    async def test_my_tool(self):
        from server import my_tool
        
        with patch("server.external_api_call") as mock_api:
            mock_api.return_value = {"status": "success"}
            
            result = await my_tool(param="value")
            
            assert "status" in result
```

### Integration Test Template

```python
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.python]

class TestMyServerStartup:
    @pytest.mark.asyncio
    async def test_server_startup(self):
        with patch("mcp.server.Server"):
            import server
            assert True  # Server imported successfully
```

### E2E Test Template

```python
import pytest
from tests.fixtures.vcr_config import get_vcr_config

vcr_config = get_vcr_config()
pytestmark = [pytest.mark.e2e, pytest.mark.python, pytest.mark.slow]

class TestMyServerE2E:
    @pytest.mark.asyncio
    @vcr_config.use_cassette('my_test.yaml')
    async def test_my_tool_e2e(self):
        from server import my_tool
        
        result = await my_tool(param="value")
        assert isinstance(result, dict)
```

## TypeScript Server Testing

TypeScript servers (PubMed, FDA) have placeholder tests in Python. For full testing:

1. Navigate to server directory:
   ```bash
   cd servers/misc/pubmed-mcp
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run TypeScript tests (if configured):
   ```bash
   npm test
   ```

## CI/CD Integration

Tests are designed to run in CI environments:

- No API keys required (uses mocks and cached responses)
- Fast execution (unit tests run quickly)
- Deterministic (cached responses ensure consistency)
- Parallel execution supported (`pytest-xdist`)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r tests/requirements-test.txt
      - run: pytest
```

## Best Practices

1. **Use Mocks for Unit Tests**: Avoid real API calls in unit tests
2. **Cache Real API Calls**: Use VCR.py for E2E tests
3. **Test Error Cases**: Include error handling tests
4. **Keep Tests Fast**: Unit tests should run in < 1 second each
5. **Isolate Tests**: Each test should be independent
6. **Use Fixtures**: Share common test data via fixtures
7. **Mark Tests Appropriately**: Use markers for easy filtering

## Troubleshooting

### Import Errors

If you see import errors, ensure the server directory is in Python path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "servers" / "server-name"))
```

### VCR Cassette Issues

If cassettes are outdated:
1. Delete the cassette file
2. Re-run the test to record a new one
3. Commit the new cassette

### MCP SDK Not Found

Install MCP SDK:
```bash
pip install mcp>=0.1.0
```

## Coverage Goals

- **Unit Tests**: 80%+ coverage for tool functions
- **Integration Tests**: All servers should have startup tests
- **E2E Tests**: At least one E2E test per server

## Contributing

When adding new servers or tools:

1. Add unit tests in `tests/unit/test_<server_name>.py`
2. Add integration test in `tests/integration/test_server_startup.py`
3. Add at least one E2E test in `tests/e2e/`
4. Update this README if needed

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [VCR.py Documentation](https://vcrpy.readthedocs.io/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

