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

Run AI-powered code reviews on git branches and commits. Automatically detects the appropriate base branch for comparison.

```bash
dylan review feature-branch
dylan review main --format json
```

See [dylan_review README](utility_library/dylan_review/README.md) for detailed options.

### `dylan pr`

Create pull requests with autonomous PR description generation. Optionally includes changelog sections.

```bash
dylan pr                           # Create PR from current branch to develop
dylan pr --target main            # Specify target branch
dylan pr --changelog              # Include changelog section in PR
```

See [dylan_pr README](utility_library/dylan_pr/README.md) for detailed options.

### `dylan release`

Create project releases with version bumping, changelog updates, and automated merging.

```bash
dylan release                     # Patch release
dylan release --minor --tag       # Minor release with tag
dylan release --major --merge-strategy pr  # Major release via PR
```

See [dylan_release README](utility_library/dylan_release/README.md) for detailed options.

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

## Branching Strategy Support

All dylan commands are branch-aware and support modern branching strategies through a `.branchingstrategy` file:

```
release_branch: develop
production_branch: main
merge_strategy: direct
```

This enables:
- Reviews to compare against the correct base branch
- PRs to target the right integration branch
- Releases to handle develop → main workflows

## Report Management

All commands generate reports in the `tmp/` directory with branch-aware naming:
- Review reports: `tmp/review_report_<branch>_<timestamp>.md`
- PR reports: `tmp/pr_report_<branch>_<timestamp>.md`
- Release reports: `tmp/release_report_<timestamp>.md`

PR reports support incremental updates, appending new information to existing reports.

## Development

The CLI is built using [Typer](https://typer.tiangolo.com/) and dispatches to modular utilities:

- `dylan/cli.py` - Main CLI entry point
- `dylan/utility_library/dylan_review/` - Code review implementation
- `dylan/utility_library/dylan_pr/` - PR creation implementation
- `dylan/utility_library/dylan_release/` - Release management implementation
- `dylan/utility_library/dylan_standup/` - Standup report implementation
- `dylan/utility_library/shared/` - Shared utilities for branch strategy
