# Claude Code Utility Library

A collection of standalone scripts and utilities for automating code workflows with Claude. This project explores various ways to script and automate Claude Code for software development tasks.

## Core Features

The scripts in this library showcase different patterns for using Claude in software development workflows:

- **Code Review**: Automated reviews of git branches or specific commits
- **Code Generation**: Implementing fixes based on reviews
- **Code Validation**: Verifying that implemented changes address review feedback
- **PR Management**: Creating pull requests with comprehensive summaries
- **Agentic Review Loop**: Fully automated review, fix, validate, and PR workflow

## Directory Structure

- [`library/full_review_loop/`](#full-review-loop): Integrated review-dev-validate-PR workflow (our latest work)
- [`library/simple_review/`](#simple-review): Standalone code review tool
- [`library/simple_dev/`](#simple-dev): Developer agent that implements fixes
- [`library/simple_validator/`](#simple-validator): Validator agent that checks if fixes are correct
- [`library/simple_pr/`](#simple-pr): PR creation tool
- [`library/cc_review/`](#cc-review): Early prototype with CLI

## Usage Instructions

Most scripts can be run directly with the Claude CLI available. You can copy any individual script to use in your own projects.

### <a name="full-review-loop"></a>Full Review Loop

The full review loop is the most advanced utility that combines all the components into a single workflow. This script creates a temporary branch, runs a code review, implements fixes, validates the changes, and creates a PR - all using Claude agents.

**Quick Start**

1. Copy [`full_review_loop_safe.py`](library/full_review_loop/full_review_loop_safe.py) to your project
2. Run it using UV:

```bash
# Review latest commit
uv run python full_review_loop_safe.py --latest --verbose

# Review a specific branch against main
uv run python full_review_loop_safe.py --branch feature-branch --verbose

# Use a git worktree for isolation
uv run python full_review_loop_safe.py --branch feature-branch --worktree

# Specify base branch and keep temporary branch after run
uv run python full_review_loop_safe.py --branch feature-branch --base-branch develop --keep-branch

# Customize number of iterations and output directory
uv run python full_review_loop_safe.py --latest --max-iterations 5 --output-dir my_review

# Skip PR creation
uv run python full_review_loop_safe.py --latest --no-pr
```

**Key Features**

- Creates an isolated temporary branch
- Optional worktree for even more isolation
- Multi-step process:
  1. **Reviewer Agent**: Analyzes code changes, identifies issues
  2. **Developer Agent**: Implements fixes based on review
  3. **Re-Review**: Reviewer analyzes fixed code
  4. **Validator Agent**: Verifies all critical issues are addressed
  5. **PR Manager**: Creates pull request if validation passes
- Iterative workflow that continues until validation passes or max iterations
- Optimized workflow after validation failure

### <a name="simple-review"></a>Simple Review

A standalone tool that uses Claude to review code changes and identify issues.

**Quick Start**

```bash
# Copy the script and run
cp library/simple_review/simple_review_poc.py your_project/
cd your_project
uv run python simple_review_poc.py --branch your-branch --base main
```

### <a name="simple-dev"></a>Simple Dev

A standalone developer agent that implements fixes based on a code review.

**Quick Start**

```bash
# Copy the script and run
cp library/simple_dev/simple_dev_poc.py your_project/
cd your_project
uv run python simple_dev_poc.py --review-file review_report.md
```

### <a name="simple-validator"></a>Simple Validator

Validates that implemented changes correctly address issues found in a code review.

**Quick Start**

```bash
# Copy the script and run
cp library/simple_validator/simple_validator_poc.py your_project/
cd your_project
uv run python simple_validator_poc.py --review-file review_report.md --dev-file dev_report.md
```

### <a name="simple-pr"></a>Simple PR

Creates a pull request based on changes implemented to address review feedback.

**Quick Start**

```bash
# Copy the script and run
cp library/simple_pr/simple_pr_poc.py your_project/
cd your_project
uv run python simple_pr_poc.py --review-file review_report.md --dev-file dev_report.md --validation-file validation_report.md
```

### <a name="cc-review"></a>CC Review

Early prototype with a command-line interface.

## Development

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

```bash
# Clone the repository
git clone https://github.com/yourusername/claudecode-utility.git
cd claudecode-utility

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .

# Run linter
uv run ruff check .
```

## Requirements

- Python 3.8+
- Claude CLI installed and configured
- Git
- GitHub CLI (gh) for PR creation

## License

MIT