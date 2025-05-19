# Dylan CLI

The main command-line interface for Dylan utilities.

## Installation

```bash
# Install globally with uv
uv tool install -e /path/to/dylan

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

### `dylan pr`

Create and manage pull requests with AI-generated descriptions.

```bash
dylan pr                              # PR from current branch to main
dylan pr feature-branch --target develop  # PR from specific branch
dylan pr --changelog                  # Update changelog while creating PR
```

See [dylan_pr README](utility_library/dylan_pr/README.md) for detailed options.

### `dylan release`

Manage project releases with version bumping and changelog updates.

```bash
dylan release              # Create release with patch bump (default)
dylan release --minor      # Minor version bump
dylan release --major --tag # Major version bump with git tag
dylan release --dry-run    # Preview changes without applying
```

See [dylan_release README](utility_library/dylan_release/README.md) for detailed options.

## Usage

```bash
# Show all available commands
dylan --help

# Get help for a specific command
dylan review --help
dylan standup --help
dylan pr --help
dylan release --help
```

## Development

The CLI is built using [Typer](https://typer.tiangolo.com/) and dispatches to modular utilities:

- `dylan/cli.py` - Main CLI entry point
- `dylan/utility_library/dylan_review/` - Code review implementation
- `dylan/utility_library/dylan_standup/` - Standup report implementation

Each utility can also be run standalone:

- `dylan review` - Direct code review access
- `dylan standup` - Direct standup report access
