# Claude Code Review Runner

A simple utility that runs code reviews using Claude Code on git branches and commits.

## Overview

The cc_review tool helps developers get AI-powered code reviews by:

1. Analyzing git diffs between branches or commits
2. Identifying issues, bugs, and potential improvements
3. Providing specific feedback with file and line references
4. Generating structured review reports in markdown or JSON format
5. Supporting pretty-printing for JSON outputs

**Required Claude Code Tools**: Read, Glob, Grep, LS, Bash, Write (configurable via --allowed-tools)

## Requirements

- Python 3.12+
- Claude Code CLI installed (`npm i -g @anthropic-ai/claude-code`)
- Git repository
- Claude API key (or Claude Code authentication)

## Installation

Clone this repository

### Using uv (recommended)

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows

# Install the package in development mode
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"

# Install as a UV tool to use on any directory
uv tool install -e /path/to/repo/root

# Run in any git repository standalone
cc-review

# Run with the main CLI
claudecode review

# Reinstall as a global tool if any updates are made
uv tool install -e . --force
```

### Using pip

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows

# Install the package in development mode
pip install -e .
```

## Usage

The review tool can be run in several ways:

### From the command line

```bash
# Review latest changes on current branch
cc-review

# Review specific branch against main
cc-review feature-branch

# Get JSON output for automation
cc-review feature-branch --format json

# Review with specific tools only
cc-review develop --tools Read,Bash

# Pretty print an existing JSON report
cc-review --pretty-print review_report.json

# Pretty print and save to new file
cc-review --pretty-print review_report.json --pretty-output report_pretty.json
```

### Using the integrated CLI

```bash
# Using the main CLI
claudecode review feature-branch

# With options
claudecode review feature-branch --format json --tools Read,Bash,Grep

# Pretty print JSON output
claudecode review --pretty-print review_report.json
```

### From Python code

```python
from src.utility_library.cc_review import run_claude_review, generate_review_prompt
from src.utility_library.cc_review.cc_review_utils import pretty_print_json_file

# Generate and run a review
prompt = generate_review_prompt(branch="feature-branch")
run_claude_review(prompt)

# Use JSON output format
prompt = generate_review_prompt(branch="feature-branch", output_format="json")
run_claude_review(prompt, output_format="json")

# Pretty print a JSON report
pretty_print_json_file("review_report.json", output_path="review_pretty.json")
```

## Options

- `branch`: Optional branch name to review (defaults to latest changes)
- `--tools`: Comma-separated list of tools (default: Read,Glob,Grep,LS,Bash,Write)
- `--format`: Output format - text, json, or stream-json (default: text)
- `--pretty-print`: Pretty print a JSON file instead of running a review
- `--pretty-output`: Save pretty-printed JSON to a file

## Output Formats

### Markdown (default)

Creates a `review_report.md` file with:

- Report metadata (branch, commits, file changes)
- Issues ranked by severity
- Specific file/line references
- Suggested fixes

### JSON

Creates a `review_report.json` file with structured data:

- Report metadata
- Issue metadata
- Detailed issue list with severity, type, and fixes
- Summary of critical issues

## Customization

The review prompts can be customized by modifying the `generate_review_prompt()` function in `cc_review_runner.py`.

Available severity levels:

- Critical
- High
- Medium
- Low

Issue types:

- Bug
- Security
- Performance
- Style
- Documentation
- Testing

## Troubleshooting

1. **Claude Code CLI not found**: Install with `npm i -g @anthropic-ai/claude-code`
2. **Permission denied**: Make sure Claude Code has write permission for saving reports
3. **No git repository found**: Run the tool inside a git repository
4. **JSON escape issues**: Use the `--pretty-print` option to fix common escape problems
5. **Branch not found**: Ensure the branch name is spelled correctly

## Architecture

The cc_review tool is split into modular components:

- `cc_review_runner.py`: Core review functionality
- `cc_review_cli.py`: Typer-based CLI interface
- `cc_review_utils.py`: Utility functions (pretty-printing)
- `__init__.py`: Module exports

## License

MIT
