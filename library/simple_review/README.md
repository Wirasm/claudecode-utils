# Simple Review

A command-line tool that uses Claude to generate comprehensive code reviews for git branches or specific commits.

## Features

- Review all changes in a branch compared to the default branch
- Review only the latest commit in a branch
- Compare the latest commit to N commits back
- Compare changes against a specific base branch
- Generate detailed, structured review reports in markdown format
- Customizable output file location
- Configurable timeout for large codebases

## Usage

```bash
# Review all changes in a branch compared to the default branch (auto-detected)
uv run python library/simple_review/simple_review.py <branch_name> [OPTIONS]

# Review only the latest commit in a branch
uv run python library/simple_review/simple_review.py <branch_name> --latest-commit [OPTIONS]

# Review latest commit compared to N commits back
uv run python library/simple_review/simple_review.py <branch_name> --latest-commit --commits-back N [OPTIONS]

# Review changes compared to a specific base branch
uv run python library/simple_review/simple_review.py <branch_name> --base-branch <base_branch> [OPTIONS]
```

## Arguments

- `branch_name`: The git branch to review (required)

## Options

- `--output OUTPUT`: Path to save the review (default: tmp/review_<branch>.md or tmp/review_latest_commit.md)
- `--verbose`: Enable detailed progress output
- `--latest-commit`: Review only the latest commit instead of all branch changes
- `--commits-back N`: When using --latest-commit, compare HEAD to HEAD~N (default: 1)
- `--base-branch BASE`: Base branch to compare against (default: auto-detected, usually 'main' or 'master')
- `--timeout SECONDS`: Timeout in seconds for the Claude process (default: 1200, which is 20 minutes)

## Examples

```bash
# Review all changes in development branch compared to auto-detected base branch
uv run python library/simple_review/simple_review.py development

# Review only the latest commit in development branch
uv run python library/simple_review/simple_review.py development --latest-commit

# Review latest commit compared to 2 commits back
uv run python library/simple_review/simple_review.py development --latest-commit --commits-back 2

# Compare development branch to a specific base branch
uv run python library/simple_review/simple_review.py development --base-branch main

# Save review to a custom file with verbose output
uv run python library/simple_review/simple_review.py feature-branch --output reviews/my_review.md --verbose

# Set a custom timeout for large codebases
uv run python library/simple_review/simple_review.py large-branch --timeout 2400
```

## Review Format

The generated review includes the following sections:

1. **Summary**: Brief overall assessment of the changes
2. **Changes Made**: Description of what was implemented or fixed
3. **Issues to Fix**: Problems that need to be addressed, categorized by priority
4. **Recommendations**: Strategic suggestions to improve the codebase

## Security Features

- Branch name validation to prevent command injection
- Output path validation to ensure proper file handling
- Error handling for git operations

## Requirements

- Python 3.12+
- Git repository
- Claude API access
