# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Principles

KISS (Keep It Simple, Stupid): Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

YAGNI (You Aren't Gonna Need It): Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

Dependency Inversion: High-level modules should not depend on low-level modules. Both should depend on abstractions. This principle enables flexibility and testability.

Open/Closed Principle: Software entities should be open for extension but closed for modification. Design your systems so that new functionality can be added with minimal changes to existing code.

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
# Run tests
uv run pytest library/cc_review/tests/ -v

# Format code
uv run black .

# Run linter
uv run ruff check .

# Run type checker
uv run mypy .
```

### Running the Application

```bash

# Running specific modules
uv run python library/simple_review/simple_review.py <branch_name> [OPTIONS]
```

## Code Architecture

The claudecode-utility is a modular library for code review and development using Claude. The architecture follows a pipeline approach with these main components:

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
