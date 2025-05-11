# Claude Code Utility Library

A utility package for Claude code generation.

## Features

- Command-line interface
- [Simple Review](library/simple_review/README.md): A tool that uses Claude to generate comprehensive code reviews for git branches or specific commits

The Simple Review tool is the starting point for the utility library. It uses Claude to generate a comprehensive code review for a git branch or specific commit. The review is then saved to a file and can be used as input for the Simple Validator tool.

The simple_review_poc.py is a proof of concept for the Simple Review tool.

the simple_review.py is an example of n runs of the Simple Review tool in combination with the developer to implement the suggestions from the review.

# (WIP)

- [Simple Dev](library/simple_dev/README.md): A tool that uses Claude to generate development reports based on a code review.
- [Simple Validator](library/simple_validator/README.md): A tool that uses Claude to validate fixes implemented based on a code review.
- [Simple PR](library/simple_pr/README.md): A tool that uses Claude to create or update a pull request based on validated changes.

# Ignore below for now

## Installation

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

# Install the package to use command-line tools
uv pip install -e .

# Alternatively, install in regular mode (not development)
uv pip install .
```

## Development

```bash
# Install development dependencies
uv add --dev pytest black ruff mypy

# Install the package in development mode
uv pip install -e .

# Run tests
uv run pytest library/cc_review/tests/ -v

# Format code
uv run black .

# Run linter
uv run ruff check .

# Run type checker
uv run mypy .
```

## Usage

### As a Command Line Tool

There are multiple ways to run the application:

```bash
# Using the claudecode command (requires installation with `uv pip install .` or `uv pip install -e .`)
claudecode

# Using the cc-review command (requires installation with `uv pip install .` or `uv pip install -e .`)
cc-review

# Running the module directly (works without installation)
uv run python -m library.cc_review
```

## License

MIT
