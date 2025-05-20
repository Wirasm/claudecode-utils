# Claude Code Utility Library

A collection of CLI utilities and experimental concepts for enhancing development workflows with Claude Code. This project serves as both a production-ready CLI application and a concept exploration library.

## Core Application

The main CLI (`dylan`) provides integrated access to production-ready utilities:

```bash
# Main CLI with sub-commands
dylan review feature-branch    # Run AI code reviews
dylan standup                 # Generate standup reports
```

### Available Commands

#### `dylan review` - AI Code Review
Analyzes git diffs and provides comprehensive code reviews with:
- Issue identification by severity (critical, high, medium, low)
- File and line-specific feedback
- Suggested fixes
- JSON output support for automation

```bash
dylan review feature-branch --format json
```

#### `dylan standup` - Daily Standup Reports
Generates formatted standup reports from:
- Recent git commits
- GitHub PRs (if configured)
- Customizable time ranges

```bash
dylan standup --since yesterday --open
```

## Installation

```bash
# Install as a development tool
uv tool install -e /path/to/claudecode-utility

# Use anywhere
dylan --help
```

## Concept Library

The `concept_library/` directory contains experimental ideas and proof-of-concepts exploring Claude Code's capabilities:

### Core Concepts

1. **Automated Review Flow** - Multi-stage code review, development, and PR creation
2. **Product Requirement Prompt (PRP) Flow** - Structured prompt engineering for feature implementation
3. **Automated Bug Triage** - GitHub issue analysis and categorization

### Key Components

- `simple_review/` - Standalone code review generation
- `simple_dev/` - Automated fix implementation
- `simple_validator/` - Fix validation
- `simple_pr/` - PR creation
- `full_review_loop/` - Orchestrated workflow
- `cc_PRP_flow/` - Product requirement workflows
- `automated_bug_triage/` - Issue triaging

## Project Structure

```
claudecode-utility/
├── src/                    # Production CLI and utilities
│   ├── cli.py             # Main CLI entry point
│   └── utility_library/    
│       ├── cc_review/     # Code review utility
│       └── cc_standup/    # Standup report generator
├── concept_library/       # Experimental concepts
└── PRPs/                  # Product Requirement Prompts
```

## Development

```bash
# Setup
git clone https://github.com/yourusername/claudecode-utility.git
cd claudecode-utility
uv venv
source .venv/bin/activate

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run black .
```

## Philosophy

This project follows these principles:
- **KISS**: Keep implementations simple
- **YAGNI**: Build only what's needed now
- **Modular Design**: Separate concerns clearly
- **Progressive Enhancement**: Start simple, add complexity when proven useful

Concepts begin in `concept_library/` as minimal implementations. Once proven valuable, they graduate to `src/` as production utilities.

## Requirements

- Python 3.12+
- Claude Code CLI (`npm i -g @anthropic-ai/claude-code`)
- Git
- GitHub CLI (optional, for PR features)

## Working with Claude Code

For the best experience:
1. Start with `/project:context-prime` to help Claude understand the repository
2. Refer to CLAUDE.md for project-specific instructions
3. Use the concept library to explore new ideas

## License

MIT