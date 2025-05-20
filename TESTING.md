# Testing Guide for Dylan

This document outlines the testing approach and structure for the Dylan package.

## Current Testing Status

The testing framework is being set up with a focus on unit tests that don't require the actual Claude provider. This allows for faster and more reliable testing without triggering actual provider calls.

### Updated Testing Strategy

The current branch has implemented these changes:

1. Fixed import errors in test files
2. Updated package structure to ensure proper imports
3. Simplified subprocess and exit command tests
4. Temporarily skipped tests that would trigger real Claude provider calls
5. Added support for mocking provider behavior

## Testing Structure

Dylan uses a vertical slice architecture for testing, with tests located close to the modules they test:

```
dylan/
├── conftest.py           # Main conftest with shared fixtures
├── tests/                # Tests for core CLI
│   ├── __init__.py
│   └── test_cli.py       # Tests for the main CLI application
├── utility_library/
    ├── shared/           # Shared components
    │   ├── tests/        # Tests for shared utilities
    │       ├── __init__.py
    │       ├── test_exit_command.py
    │       └── test_subprocess_utils.py
    ├── dylan_review/
    │   ├── tests/
    │       ├── __init__.py
    │       ├── conftest.py  # Review-specific fixtures
    │       ├── test_dylan_review_cli.py
    │       └── test_dylan_review_runner.py
    ├── dylan_pr/
    │   ├── tests/
    │       ├── ...
    └── ...
```

## Running Tests

Tests are run using pytest with UV:

```bash
# Run all tests (includes skipped tests)
uv run pytest

# Run tests for a specific module
uv run pytest dylan/utility_library/dylan_review/tests/

# Run tests with coverage report
uv run pytest --cov=dylan

# Run a specific test file
uv run pytest dylan/utility_library/dylan_review/tests/test_dylan_review_runner.py

# Run tests without skipped tests
uv run pytest -k "not skip"
```

## Test Types

### Unit Tests
- Test individual functions and classes in isolation
- Located in each vertical's tests directory
- Naming: `test_<module>_<function>.py`

### Integration Tests
- Test interactions between components
- Located in each vertical's tests directory
- Prefix: `test_integration_*.py`

### Functional Tests
- Test CLI commands end-to-end
- Located in the root tests directory
- Limited use of mocks - simulate real usage
- Prefix: `test_functional_*.py`

## Fixtures

### Global Fixtures (in dylan/conftest.py)
- `mock_claude_provider`: Mocks the Claude Code provider for testing
- `temp_output_dir`: Creates a temporary directory for test outputs
- `cli_runner`: Provides a Typer CLI test runner
- `mock_git_repo`: Creates a mock git repository structure
- `mock_git_operations`: Mocks common git commands

### Vertical-Specific Fixtures
Each vertical slice has its own fixtures in its conftest.py file.

#### dylan_review
- `mock_git_diff`: Mock git diff output
- `sample_review_report`: Sample review report for testing
- `mock_review_runner`: Mock for the review runner module

#### dylan_pr
- `mock_git_branch_info`: Mock git branch information
- `mock_github_api`: Mock GitHub API responses
- `mock_gh_cli`: Mock GitHub CLI command responses
- `mock_pr_runner`: Mock for the PR runner module

## Mocking Strategy

- External dependencies (git, gh, claude) are mocked
- File operations use temporary directories
- Internal modules use fixture-based dependency injection
- Unit tests use fine-grained mocking
- Integration tests use coarser-grained mocking

## Adding New Tests

When adding new functionality:

1. Create unit tests for new modules in the appropriate tests directory
2. Update/add fixtures in the relevant conftest.py
3. Add integration tests for interactions with other components
4. Run the full test suite before submitting changes

For new vertical slices:

1. Create a tests directory within the vertical
2. Add a vertical-specific conftest.py
3. Implement appropriate unit, integration, and functional tests

## Code Coverage

Code coverage is tracked using pytest-cov:

```bash
# Generate coverage report
uv run pytest --cov=dylan --cov-report=term

# Generate HTML coverage report
uv run pytest --cov=dylan --cov-report=html
```

## Continuous Integration

The test suite runs automatically on:
- Pull requests to develop and main branches
- Direct pushes to develop and main branches

All tests must pass for PRs to be merged.