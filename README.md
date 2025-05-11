# Claude Code Utility Library

A utility package for Claude code generation.

## Features

- Command-line interface

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

### As a Library

```python
from library.cc_review.utils.helpers import fetch_json_data

# Fetch data from an API
data = fetch_json_data("https://api.example.com/data", {"param": "value"})
print(data)
```

## License

MIT
