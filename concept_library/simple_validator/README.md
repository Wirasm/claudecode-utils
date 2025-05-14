# Simple Validator for Development Quality Assurance

This utility automates the validation of code changes made in response to a code review. It verifies that all critical and high-priority issues have been properly addressed, runs tests to ensure functionality, and evaluates overall code quality.

## Features

- Analyzes code changes against original review issues
- Ensures all CRITICAL and HIGH priority issues have been fixed
- Runs test suite to verify functionality
- Evaluates code quality (error handling, security, patterns)
- Produces comprehensive validation reports with PASSED/FAILED status
- Supports validating specific branches or just the latest commit
- Integrates with the complete review-develop-validate workflow

## Usage

```bash
# Validate fixes with default options
uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> [--output <output_file>] [--verbose]

# Validate fixes for a specific branch
uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> --branch <branch_name> [--output <output_file>] [--verbose]

# Validate only the latest commit
uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> --latest-commit [--branch <branch_name>] [--output <output_file>] [--verbose]
```

## Arguments

- `review_file`: Path to the review file containing issues (required)
- `dev_report_file`: Path to the development report file (required)
- `--branch BRANCH`: Git branch to validate (default: development-wip)
- `--output OUTPUT`: Path to save the validation report (default: tmp/validation_<branch>.md)
- `--verbose`: Enable detailed progress output
- `--latest-commit`: Validate only the latest commit instead of all branch changes

## Examples

### Validate fixes from review and dev report files with default branch

```bash
uv run python library/simple_validator/simple_validator_poc.py tmp/review_latest_commit.md tmp/dev_report_latest_commit.md
```

### Validate fixes for a specific branch with verbose output

```bash
uv run python library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --branch feature-branch --verbose
```

## Complete Workflow Example

This shows how the Simple Validator fits into the larger workflow:

```bash
# 1. Review code changes
uv run python library/simple_review/simple_review_poc.py development-wip --output tmp/review.md

# 2. Implement changes based on review
uv run python library/simple_dev/simple_dev_poc.py tmp/review.md --output tmp/dev_report.md

# 3. Validate the changes
uv run python library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --output tmp/validation.md
```

## Requirements

- Claude CLI installed and configured
- Git repository with changes to validate
- Python test suite using pytest

## Output

The validator produces a structured report containing:

1. Summary (overall assessment)
2. Issues Assessment (evaluation of each critical/high issue from the review)
3. Test Results (output from running tests)
4. Code Quality Evaluation (assessment of overall code quality)
5. Conclusion (final determination with PASSED/FAILED status)

The report ends with a clear status line:
- `VALIDATION: PASSED` - when all issues are resolved without introducing new problems
- `VALIDATION: FAILED` - when issues remain or new problems were introduced

## How It Works

The validator:

1. Reads the original review to understand what issues needed to be fixed
2. Reads the development report to see what changes were made
3. Analyzes all current changes using `git diff`
4. Runs tests to verify functionality
5. Evaluates code quality focusing on:
   - Proper error handling
   - Input validation
   - Security concerns
   - Adherence to architecture patterns
   - Consistent use of patterns and utilities

## Notes

- Has a 15-minute timeout for complex validations
- Return code 0 indicates successful validation, 1 indicates failure
- Use `--verbose` flag to see progress and a preview of the validation report
- The validator is designed to be strict to ensure high-quality code