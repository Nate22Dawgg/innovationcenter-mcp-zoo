# Contributing to Innovation Center MCP Zoo

Thank you for your interest in contributing to the Innovation Center MCP Zoo! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [CI/CD Requirements](#cicd-requirements)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Registry Updates](#registry-updates)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Development Setup

### Prerequisites

- **Python** 3.8 or higher
- **Node.js** 20 or higher (for TypeScript-based MCP servers)
- **Git**
- **Docker** (optional, for testing Docker builds)

### Local Development

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/innovationcenter-mcp-zoo.git
   cd innovationcenter-mcp-zoo
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Validate the registry**:
   ```bash
   python scripts/validate_registry.py
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## CI/CD Requirements

All contributions must pass CI/CD validation before being merged. The CI pipeline runs automatically on every push and pull request.

### Validation Checks

The CI pipeline includes the following checks:

1. **Registry Validation** (`registry-validation`)
   - Validates `registry/tools_registry.json` structure
   - Checks required fields, allowed values, and consistency
   - Validates domain references against `registry/domains_taxonomy.json`
   - Verifies schema file existence and validity

2. **Schema Validation** (`schema-validation`)
   - Validates all JSON Schema files in `schemas/`
   - Ensures schemas conform to JSON Schema Draft 7 specification

3. **Python Tests** (`python-tests`)
   - Runs pytest test suite
   - Tests on Python 3.8, 3.9, 3.10, and 3.11
   - Includes unit, integration, and e2e tests

4. **TypeScript Tests** (`typescript-tests`)
   - Runs tests for TypeScript-based MCP servers:
     - `servers/misc/pubmed-mcp`
     - `servers/misc/fda-mcp`
     - `servers/real-estate/real-estate-mcp`

5. **Link Checking** (`link-checking`)
   - Validates all external links in markdown files
   - Ensures no broken URLs in documentation

### Pre-commit Checklist

Before submitting a pull request, ensure:

- [ ] Registry validation passes: `python scripts/validate_registry.py`
- [ ] All Python tests pass: `pytest tests/ -v`
- [ ] TypeScript tests pass (if applicable): `npm test` in server directories
- [ ] Code follows style guidelines (black, ruff for Python; ESLint for TypeScript)
- [ ] Documentation is updated
- [ ] No broken links in markdown files

### CI Failure

If CI fails:

1. Review the error messages in the GitHub Actions logs
2. Fix the issues locally
3. Re-run validation: `python scripts/validate_registry.py`
4. Push your fixes

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(registry): add new clinical trials tool

Add support for searching clinical trials by condition and phase.
Updates registry with new tool entry and schema.
```

## Code Style and Standards

### Python

- Follow PEP 8 style guide
- Use `black` for code formatting: `black .`
- Use `ruff` for linting: `ruff check .`
- Type hints are encouraged for new code
- Maximum line length: 100 characters

### TypeScript

- Follow ESLint configuration in each server directory
- Use TypeScript strict mode
- Prefer async/await over promises
- Maximum line length: 100 characters

### JSON

- Use 2-space indentation
- Trailing commas are allowed
- Sort keys alphabetically in registry files

## Testing

### Python Tests

Tests are organized in the `tests/` directory:

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for server startup
- `tests/e2e/` - End-to-end tests with real API calls (cached)

Run tests:
```bash
# All tests
pytest tests/ -v

# Specific test type
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# With coverage
pytest tests/ --cov=servers --cov-report=html
```

### TypeScript Tests

For TypeScript-based servers, run tests in the server directory:

```bash
cd servers/misc/pubmed-mcp
npm test
```

### Test Markers

Use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_api_key` - Tests requiring API keys

## Registry Updates

When adding or modifying tools in the registry:

1. **Update `registry/tools_registry.json`**:
   - Add tool entry with all required fields
   - Use valid domain from `registry/domains_taxonomy.json`
   - Set appropriate status and safety_level

2. **Create or update schemas**:
   - Add JSON Schema files in `schemas/`
   - Reference schemas in tool entry (`input_schema`, `output_schema`)

3. **Validate**:
   ```bash
   python scripts/validate_registry.py
   ```

4. **Update documentation**:
   - Update `docs/REGISTRY_SUMMARY.md` if adding new tools
   - Add server README if adding new MCP server

### Required Fields

Each tool entry must include:

- `id` - Unique tool identifier
- `name` - Human-readable name
- `description` - Tool description
- `domain` - Domain from taxonomy
- `status` - One of: `stub`, `in_development`, `experimental`, `testing`, `active`, `deprecated`, `archived`
- `safety_level` - One of: `low`, `medium`, `high`, `restricted`
- `auth_required` - Boolean
- `mcp_server_path` - Path to MCP server

## Submitting Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation
   - Validate registry

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Provide a clear description
   - Reference related issues
   - Ensure CI passes
   - Request review from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Registry update
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] Registry validation passes
- [ ] CI checks pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Registry validated
```

## Release Process

Releases are created automatically when version tags are pushed:

1. **Create a version tag**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **GitHub Actions will**:
   - Build Docker images for servers with Dockerfiles
   - Push images to GitHub Container Registry
   - Create a GitHub Release with changelog

3. **Docker images**:
   - Available at `ghcr.io/OWNER/server-name:tag`
   - Tagged with version and `latest`

### Versioning

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Example: `v1.2.3`

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `docs/` directory

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

