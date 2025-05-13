# Simple Developer for Implementing Code Fixes

This utility automates the implementation of code fixes based on a code review. It uses Claude to read a review report, develop a plan to address issues, implement fixes, and document changes made.

## Features

- Automatically implements fixes for issues identified in code reviews
- Prioritizes CRITICAL and HIGH issues
- Makes code changes directly in the repository
- Runs tests to verify fix implementation
- Generates comprehensive development reports
- Supports working on specific branches or just the latest commit
- Integrates with the complete review-validate-PR workflow

## Usage

```bash
# Implement fixes from a review (default branch: development-wip)
uv run python library/simple_dev/simple_dev_poc.py <review_file> [--output <output_file>] [--verbose]

# Implement fixes for a specific branch
uv run python library/simple_dev/simple_dev_poc.py <review_file> --branch <branch_name> [--output <output_file>] [--verbose]

# Implement fixes for the latest commit only
uv run python library/simple_dev/simple_dev_poc.py <review_file> --latest-commit [--branch <branch_name>] [--output <output_file>] [--verbose]
```

## Arguments

- `review_file`: Path to the review file to implement fixes from (required)
- `--branch BRANCH`: Git branch to work on (default: development-wip)
- `--output OUTPUT`: Path to save the development report (default: tmp/dev*report*<branch>.md)
- `--verbose`: Enable detailed progress output
- `--latest-commit`: Work on only the latest commit instead of all branch changes

## Examples

### Implement fixes from a review on the default branch

```bash
uv run python library/simple_dev/simple_dev_poc.py tmp/review_development-wip.md
```

### Implement fixes from a review for the latest commit

```bash
uv run python library/simple_dev/simple_dev_poc.py tmp/review_latest_commit.md --latest-commit
```

### Implement fixes for a feature branch with custom output file

```bash
uv run python library/simple_dev/simple_dev_poc.py reviews/feature_review.md --branch feature-branch --output reports/feature_fixes.md --verbose
```

## Complete Workflow Example

This shows how the Simple Developer fits into the larger workflow:

```bash
# 1. Review code changes
uv run python library/simple_review/simple_review_poc.py development-wip --latest-commit --output tmp/review_latest.md

# 2. Implement changes based on review
uv run python library/simple_dev/simple_dev_poc.py tmp/review_latest.md --latest-commit --output tmp/dev_report_latest.md

# 3. Validate the changes
uv run python library/simple_validator/simple_validator_poc.py tmp/review_latest.md tmp/dev_report_latest.md --output tmp/validation.md
```

## Requirements

- Claude CLI installed and configured
- Git repository with changes to implement
- Python test suite using pytest (for verifying changes)

## Output

The developer produces a structured report containing:

1. Summary (overview of fixed issues and approach)
2. Issues Fixed (detailed breakdown by priority)
   - 2.1 CRITICAL Issues
   - 2.2 HIGH Priority Issues
3. Implementation Notes (challenges, alternatives considered)
4. Test Results (output from test runs)
5. Next Steps (issues that couldn't be fixed or need further work)

## How It Works

The developer:

1. Reads the review file to understand all issues that need to be fixed
2. Creates a prioritized list of issues, focusing on CRITICAL and HIGH priority items first
3. Implements fixes one by one, using appropriate tools (Edit, MultiEdit, Write, etc.)
4. Runs tests to verify that the fixes work correctly
5. Documents each change made and why it addresses the issue

## Notes

- Has a 60-minute timeout for complex implementations
- Return code 0 indicates successful implementation, 1 indicates failure
- Use `--verbose` flag to see progress and a preview of the development report
- The developer is designed to make pragmatic fixes without introducing new issues
