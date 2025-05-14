# Claude Code Utility Library

A collection of standalone scripts and utilities for automating code workflows with Claude. This project explores various ways to script and automate Claude Code for software development tasks.

## Core Concepts

The Claude Code Utility Library explores three core concepts for enhancing AI-driven software development:

1. **Automated Review Flow**: A comprehensive solution for code reviews, fixes, validation, and PR creation
2. **Product Requirement Prompt (PRP) Flow**: A sophisticated agentic engineering workflow for implementing complete features
3. **Standup Automation**: A tool for generating daily standup reports from git activity

## Directory Structure

- [`concept_library/full_review_loop/`](#full-review-loop): Integrated review-dev-validate-PR workflow
- [`concept_library/simple_review/`](#simple-review): Standalone code review tool
- [`concept_library/simple_dev/`](#simple-dev): Developer agent that implements fixes
- [`concept_library/simple_validator/`](#simple-validator): Validator agent that checks if fixes are correct
- [`concept_library/simple_pr/`](#simple-pr): PR creation tool
- [`concept_library/cc_PRP_flow/`](#prp-flow): Product Requirement Prompt workflow
- [`src/utility_library/cc_standup/`](#standup): Standup report generator

## Concept Details

### <a name="automated-review-flow"></a>Automated Review Flow

The Review Flow comes in two variants: a complete integrated workflow and modular components.

#### <a name="full-review-loop"></a>Full Review Loop

The full review loop orchestrates multiple Claude instances to review, develop, validate, and create PRs within safe, isolated environments.

**Quick Start**

```bash
# Review latest commit
uv run python concept_library/full_review_loop/full_review_loop_safe.py --latest --verbose

# Review a specific branch against main
uv run python concept_library/full_review_loop/full_review_loop_safe.py --branch feature-branch --verbose

# Use a git worktree for isolation
uv run python concept_library/full_review_loop/full_review_loop_safe.py --branch feature-branch --worktree

# Specify base branch and keep temporary branch after run
uv run python concept_library/full_review_loop/full_review_loop_safe.py --branch feature-branch --base-branch develop --keep-branch
```

**Key Features**

- Automatic branching and worktree isolation
- Iterative improvement cycles
- Feedback loops between agents
- PR creation upon successful validation
- Safety features to prevent destructive changes

#### Individual Components

Each component of the review flow can be used independently:

- **[Simple Review](#simple-review)**: Generates comprehensive code reviews for git branches or specific commits
- **[Simple Developer](#simple-dev)**: Implements code fixes based on review feedback
- **[Simple Validator](#simple-validator)**: Validates that fixes properly address review issues
- **[Simple PR](#simple-pr)**: Creates well-documented pull requests based on validated changes

### <a name="prp-flow"></a>Product Requirement Prompt (PRP) Flow

The PRP Flow is a highly sophisticated agentic engineering workflow concept for implementing vertical slices of working software.

**Key Concept:**

"Over-specifying what to build while under-specifying the context is why so many AI-driven coding attempts stall at 80%. A Product Requirement Prompt (PRP) fixes that by fusing the disciplined scope of a traditional Product Requirements Document (PRD) with the 'context-is-king' mindset of modern prompt engineering."

**Quick Start**

```bash
# Run a PRP in interactive mode
uv run python concept_library/cc_PRP_flow/scripts/cc_runner_simple.py --prp test --interactive

# Run a specific PRP file
uv run python concept_library/cc_PRP_flow/scripts/cc_runner_simple.py --prp-path PRPs/custom_feature.md
```

**Key Features**

- Structured prompt templates that provide complete context
- Three AI-critical layers:
  - **Context**: Precise file paths, library versions, code snippets
  - **Implementation Details**: Clear guidance on how to build the feature
  - **Validation Gates**: Deterministic checks for quality control
- PRP runner script for executing PRPs with Claude Code
- Support for both interactive and headless modes

### <a name="standup"></a>Standup Report Generator

The Standup tool automates the creation of daily standup reports by analyzing git commits and GitHub PR activity.

**Quick Start**

```bash
# Generate a standup report for today
uv run python -m utility_library.cc_standup

# Generate for a specific date
uv run python -m utility_library.cc_standup --since "2023-05-01T09:00:00"

# Open the report after generation
uv run python -m utility_library.cc_standup --open
```

**Key Features**

- Collects recent git commits and PR activity
- Uses Claude to generate structured Markdown reports
- Supports customizable date ranges
- Automatically formats reports with Yesterday/Today/Blockers sections
- Minimal dependencies with graceful fallbacks

## Component Usage

### <a name="simple-review"></a>Simple Review

A standalone tool that uses Claude to review code changes and identify issues.

```bash
# Review all changes in a branch
uv run python concept_library/simple_review/simple_review.py development

# Review only the latest commit
uv run python concept_library/simple_review/simple_review.py development --latest-commit
```

### <a name="simple-dev"></a>Simple Dev

A standalone developer agent that implements fixes based on a code review.

```bash
# Implement fixes from a review
uv run python concept_library/simple_dev/simple_dev_poc.py tmp/review.md
```

### <a name="simple-validator"></a>Simple Validator

Validates that implemented changes correctly address issues found in a code review.

```bash
# Validate fixes
uv run python concept_library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md
```

### <a name="simple-pr"></a>Simple PR

Creates a pull request based on changes implemented to address review feedback.

```bash
# Create a PR
uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

```bash
# Clone the repository
git clone https://github.com/yourusername/claudecode-utility.git
cd claudecode-utility

# Create a virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install dependencies
uv sync

# Install package in development mode
uv pip install -e .

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
- GitHub CLI (gh) for PR creation and GitHub operations

## License

MIT