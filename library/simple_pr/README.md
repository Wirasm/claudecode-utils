# Simple PR Manager for Creating Pull Requests

This utility automates creating pull requests with comprehensive descriptions based on validated changes. It uses Claude to analyze changes, generate meaningful PR descriptions, and create GitHub pull requests.

## Features

- Creates PRs based on validation reports
- Analyzes code changes to generate detailed PR descriptions
- Includes summaries of changes, issues fixed, and testing performed
- Supports different branches and custom PR titles
- Offers a dry-run mode to preview PR descriptions without creating PRs
- Integrates with the complete review-develop-validate-PR workflow

## Usage

```bash
# Create PR with default options based on validation report
uv run python library/simple_pr/simple_pr_poc.py <validation_file> [--title <pr_title>] [--output <output_file>] [--verbose]

# Create PR for a specific branch
uv run python library/simple_pr/simple_pr_poc.py <validation_file> --branch <branch_name> --base <base_branch> [--title <pr_title>] [--output <output_file>] [--verbose]

# Only generate PR description without actually creating PR
uv run python library/simple_pr/simple_pr_poc.py <validation_file> --dry-run [--output <output_file>] [--verbose]
```

## Arguments

- `validation_file`: Path to the validation report file confirming changes are ready (required)
- `--branch BRANCH`: Git branch containing changes (default: development-wip)
- `--base BASE`: Base branch to merge changes into (default: main)
- `--title TITLE`: Title for the pull request (default: generated from branch name)
- `--output OUTPUT`: Path to save the PR report (default: tmp/pr_<branch>.md)
- `--verbose`: Enable detailed progress output
- `--dry-run`: Generate PR description without creating the PR

## Examples

### Create a PR based on validation report

```bash
uv run python library/simple_pr/simple_pr_poc.py tmp/validation.md --title "Add PipedriveSettings configuration class"
```

### Create a PR for a specific branch into main

```bash
uv run python library/simple_pr/simple_pr_poc.py tmp/validation.md --branch feature-branch --base main --verbose
```

### Generate PR description without creating PR

```bash
uv run python library/simple_pr/simple_pr_poc.py tmp/validation.md --dry-run --output tmp/pr_description.md
```

## Complete Workflow Example

This shows how the Simple PR Manager fits into the larger workflow:

```bash
# 1. Review code changes
uv run python library/simple_review/simple_review_poc.py development-wip --output tmp/review.md

# 2. Implement changes based on review
uv run python library/simple_dev/simple_dev_poc.py tmp/review.md --output tmp/dev_report.md

# 3. Validate the changes
uv run python library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --output tmp/validation.md

# 4. Create PR if validation passed
uv run python library/simple_pr/simple_pr_poc.py tmp/validation.md --title "Implement configuration management"
```

## Requirements

- Claude CLI installed and configured
- GitHub CLI (gh) installed and authenticated
- Git repository with changes to submit

## Output

The PR manager produces a report file containing:

1. Summary of changes
2. List of issues addressed
3. Testing performed
4. Additional notes/considerations
5. PR URL (if not in dry-run mode and PR was successfully created)

## Notes

- Only proceeds if validation report shows PASSED status
- Uses GitHub CLI (gh) to create pull requests
- Has a 10-minute timeout for PR creation
- Use `--verbose` flag to see progress and a preview of the PR description