# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Principles

KISS (Keep It Simple, Stupid): Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

YAGNI (You Aren't Gonna Need It): Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

Dependency Inversion: High-level modules should not depend on low-level modules. Both should depend on abstractions. This principle enables flexibility and testability.

Open/Closed Principle: Software entities should be open for extension but closed for modification. Design your systems so that new functionality can be added with minimal changes to existing code.

KEEP early versions of new concepts in the concept_library/ directory very light and simple.
we add complexity step by step and only if needed.

Minimal claude code wrappers with 0 to minimal validation.

- Always remember to use uv run when we run scripts
- We never write commit messages, we have a pre-commit hook for that so always commit with git commit nothing more

## Example Claude Code Usage

```bash
# Simple prompt
claude -p "make a hello.js script that prints hello" --allowedTools "Write" "Edit"

# Using in a script
#!/usr/bin/env -S uv run --script

import subprocess

prompt = """
GIT checkout a NEW branch.

CREATE src/cc_todo/todo.py: a zero library CLI todo app with basic CRUD.

THEN GIT stage, commit and SWITCH back to main.
"""

command = ["claude", "-p", prompt, "--allowedTools", "Edit", "Bash", "Write"]

process = subprocess.run(command, check=True)

print(f"Claude process exited with output: {process.stdout}")
```

## Claude Code Tools Reference

Claude Code has access to various tools. Here are the most commonly used ones:

| Tool         | Description                                          | Permission Required |
| ------------ | ---------------------------------------------------- | ------------------- |
| Agent        | Runs a sub-agent to handle complex, multi-step tasks | No                  |
| Bash         | Executes shell commands in your environment          | Yes                 |
| Glob         | Finds files based on pattern matching                | No                  |
| Grep         | Searches for patterns in file contents               | No                  |
| LS           | Lists files and directories                          | No                  |
| Read         | Reads the contents of files                          | No                  |
| Edit         | Makes targeted edits to specific files               | Yes                 |
| MultiEdit    | Makes targeted edits to multiple files               | Yes                 |
| Write        | Creates or overwrites files                          | Yes                 |
| NotebookEdit | Modifies Jupyter notebook cells                      | Yes                 |
| NotebookRead | Reads and displays Jupyter notebook contents         | No                  |
| WebFetch     | Fetches content from a specified URL                 | Yes                 |
| WebSearch    | Searches the web for information                     | Yes                 |
| TodoRead     | Reads todo files                                     | No                  |
| TodoWrite    | Writes to todo files                                 | Yes                 |

Permission rules can be configured using /allowed-tools or in permission settings.

## Core Commands

### Environment Setup

```bash
# Create and activate virtual environment with uv
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install dependencies
uv sync

# Install package in development mode
uv pip install -e .
```

### Development Commands

```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest concept_library/full_review_loop/tests/ -v

# Format code
uv run black .

# Run linter
uv run ruff check .

# Run type checker
uv run mypy .
```

### Running Core Components

#### Individual Components

```bash
# Simple Review - Code review tool for git branches/commits
uv run python concept_library/simple_review/simple_review.py <branch_name>
uv run python concept_library/simple_review/simple_review.py <branch_name> --latest-commit

# Simple Dev - Implements fixes based on review feedback
uv run python concept_library/simple_dev/simple_dev_poc.py tmp/review.md

# Simple Validator - Validates that fixes address issues
uv run python concept_library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md

# Simple PR - Creates pull requests from validated changes
uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md
```

#### PRP Flow

```bash
# Run a PRP in interactive mode
uv run python concept_library/cc_PRP_flow/scripts/cc_runner_simple.py --prp test --interactive

# Run a specific PRP file
uv run python concept_library/cc_PRP_flow/scripts/cc_runner_simple.py --prp-path PRPs/custom_feature.md
```

#### Standup Report Generator

```bash
# Generate a standup report for today
standup

# Generate for a specific date
standup --since "2023-05-01T09:00:00"

# Open the report after generation
standup --open
```

#### PR Creation

```bash
# Create a pull request from the current branch to main
dylan pr

# Create PR from a specific branch to a target branch
dylan pr feature-branch --target develop

# Update changelog while creating PR
dylan pr --changelog

# Create PR with custom target and tools
dylan pr --target develop --tools "Read,Bash"
```

#### Release Management

```bash
# Create a new release with patch version bump (default)
dylan release

# Minor version bump
dylan release --minor

# Major version bump with git tag
dylan release --major --tag

# Dry run to preview changes
dylan release --minor --dry-run

# Release with specific merge strategy
dylan release --minor --merge-strategy pr
```

## Graceful Claude Code Termination

When working with Claude Code processes, use the improved provider implementation in Dylan for graceful termination:

```python
from dylan.utility_library.provider_clis.provider_claude_code import get_provider

# Get the Claude Code provider
provider = get_provider()

# Generate content with graceful termination handling
try:
    result = provider.generate(
        "Write a short story about a robot learning to garden",
        timeout=60,  # 60 second timeout
        stream=True,  # Enable streaming output
    )
    print(result)
except KeyboardInterrupt:
    print("Process was interrupted by user")
```

This implementation ensures proper subprocess management, including signal handling, custom exit commands, and real-time output streaming.

## UV Package Management

This project uses UV for Python package management. Key commands include:

```bash
# Create virtual environment
uv venv

# Install dependencies from pyproject.toml
uv sync

# Install a specific package
uv add requests

# Remove a package
uv remove requests

# Run a Python script or command
uv run python script.py
uv run pytest

# Install editable packages
uv pip install -e .
```

When running scripts or tools, always use `uv run` to ensure proper virtual environment activation:

```bash
# Preferred way to run commands
uv run pytest
uv run black .

# Running tools without installing
uvx black .
uvx ruff check .
```

## Code Architecture

Dylan is a modular CLI for AI-powered development utilities using Claude Code. The project explores three core concepts:

### 1. Automated Review Flow

The architecture follows a pipeline approach with these main components:

1. **Simple Review**: Code review tool generating feedback for git branches or commits

   - `simple_review_poc.py`: Proof-of-concept implementation
   - `simple_review.py`: Enhanced implementation with config options

2. **Simple Developer**: Implements fixes based on review feedback

   - Prioritizes critical and high-priority issues identified in reviews

3. **Simple Validator**: Validates that fixes properly address review issues

   - Generates validation reports with PASS/FAIL determinations

4. **Simple PR**: Creates pull requests based on validated changes

   - Generates comprehensive PR descriptions from development reports

5. **Full Review Loop**: Orchestrates complete workflow with multiple Claude instances
   - `full_review_loop_safe.py`: Creates isolated environments (temporary branches and worktrees)
   - Implements iterative improvement cycles: Review → Develop → Re-Review → Validate

Key architectural principles:

- Each component is designed to function independently
- Components communicate through structured markdown reports
- Safety features include temporary branch creation and worktree isolation
- The workflow follows a progressive refinement pattern, where validation results feed back into development

### 2. Product Requirement Prompt (PRP) Flow

The PRP Flow is a sophisticated agentic engineering workflow for implementing complete features:

- **Key Concept**: "Over-specifying what to build while under-specifying the context is why so many AI-driven coding attempts stall at 80%. A Product Requirement Prompt (PRP) fixes that by fusing the disciplined scope of a traditional Product Requirements Document (PRD) with the 'context-is-king' mindset of modern prompt engineering."

- **Structure**:

  - **Context**: Precise file paths, library versions, code snippets
  - **Implementation Details**: Clear guidance on how to build the feature
  - **Validation Gates**: Deterministic checks for quality control

- **Components**:
  - PRP templates in the PRPs/ directory
  - Runner scripts in concept_library/cc_PRP_flow/scripts/
  - Support for both interactive and headless modes

### 3. Standup Automation

A tool for generating daily standup reports from git activity:

- Collects recent git commits and PR activity
- Uses Claude to generate structured Markdown reports
- Supports customizable date ranges
- Automatically formats reports with Yesterday/Today/Blockers sections

## Requirements

- Python 3.12+
- Claude CLI installed and configured
- Git
- GitHub CLI (gh) for PR creation and GitHub operations

## Project Structure

- `concept_library/`: Contains the core concept implementations
  - `full_review_loop/`: Integrated review-dev-validate-PR workflow
  - `simple_review/`: Standalone code review tool
  - `simple_dev/`: Developer agent that implements fixes
  - `simple_validator/`: Validator agent that checks if fixes are correct
  - `simple_pr/`: PR creation tool
  - `cc_PRP_flow/`: Product Requirement Prompt workflow
  - `automated_bug_triage/`: GitHub issue analysis and categorization
- `dylan/utility_library/`: Contains the utility implementations
  - `dylan_standup/`: Standup report generator
  - `dylan_review/`: Code review tool
  - `dylan_pr/`: Pull request creation and management
  - `dylan_release/`: Release management and changelog generation
  - `provider_clis/`: Claude Code provider interfaces
  - `shared/`: Shared utilities and UI components
- `PRPs/`: Contains Product Requirement Prompt templates
- `ai_docs/`: Documentation for AI tools and best practices

## BRANCHING STRATEGY

This repository follows a develop → main branching strategy, where:

- `main` is the production branch containing stable releases
- `develop` is the integration branch where features are merged
- Feature branches are created from `develop` for work in progress

More details are available in BRANCHING_STRATEGY.md.

When creating branches, follow these naming conventions:
- Feature branches: `feature/descriptive-name`
- Bug fix branches: `fix/issue-description`
- Documentation branches: `docs/what-is-changing`
- Refactoring branches: `refactor/what-is-changing`

The branching strategy is configured in the `.branchingstrategy` file which is used by the Dylan tools to understand how to handle branches during release and PR processes.