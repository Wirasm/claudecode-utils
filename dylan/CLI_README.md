# Dylan CLI

The main command-line interface for Dylan utilities.

## Installation

```bash
# Install globally with uv
uv tool install -e /path/to/claudecode-utility

# Verify installation
dylan --help
```

## Commands

### `dylan review`

Run AI-powered code reviews on git branches and commits.

```bash
dylan review feature-branch
dylan review main --format json
```

See [dylan_review README](utility_library/dylan_review/README.md) for detailed options.

### `dylan standup`

Generate daily standup reports from git commits and GitHub PRs.

```bash
dylan standup
dylan standup --since yesterday --open
dylan standup --out report.md
```

See [dylan_standup README](utility_library/dylan_standup/README.md) for detailed options.

## Usage

```bash
# Show all available commands
dylan --help

# Get help for a specific command
dylan review --help
dylan standup --help
```

## Development

The CLI is built using [Typer](https://typer.tiangolo.com/) and dispatches to modular utilities:

- `src/cli.py` - Main CLI entry point
- `src/utility_library/cc_review/` - Code review implementation
- `src/utility_library/cc_standup/` - Standup report implementation

Each utility can also be run standalone:

- `cc-review` - Direct code review access
- `standup` - Direct standup report access
