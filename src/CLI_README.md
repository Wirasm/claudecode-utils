# Claude Code CLI

The main command-line interface for Claude Code utilities.

## Installation

```bash
# Install globally with uv
uv tool install -e /path/to/claudecode-utility

# Verify installation
claudecode --help
```

## Commands

### `claudecode review`

Run AI-powered code reviews on git branches and commits.

```bash
claudecode review feature-branch
claudecode review main --format json
claudecode review --pretty-print review_report.json
```

See [cc_review README](utility_library/cc_review/README.md) for detailed options.

### `claudecode standup`

Generate daily standup reports from git commits and GitHub PRs.

```bash
claudecode standup
claudecode standup --since yesterday --open
claudecode standup --out report.md
```

See [cc_standup README](utility_library/cc_standup/README.md) for detailed options.

## Usage

```bash
# Show all available commands
claudecode --help

# Get help for a specific command
claudecode review --help
claudecode standup --help
```

## Development

The CLI is built using [Typer](https://typer.tiangolo.com/) and dispatches to modular utilities:

- `src/cli.py` - Main CLI entry point
- `src/utility_library/cc_review/` - Code review implementation
- `src/utility_library/cc_standup/` - Standup report implementation

Each utility can also be run standalone:

- `cc-review` - Direct code review access
- `standup` - Direct standup report access
