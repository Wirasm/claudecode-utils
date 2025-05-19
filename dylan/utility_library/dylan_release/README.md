# Dylan Release Manager

A minimal Claude Code utility for autonomous project releases.

## Overview

The `dylan release` command gives Claude Code complete autonomy to create project releases. It handles version bumping, changelog updates, and git operations in a project-agnostic way.

The command is branch-aware and supports modern branching strategies (develop → main) while remaining backwards compatible with simple main-only workflows.

## Usage

```bash
# Create a patch release (default)
dylan release

# Create a minor release
dylan release --minor

# Create a major release  
dylan release --major

# Create release with git tag
dylan release --minor --tag

# Specify merge strategy (direct or pr)
dylan release --minor --merge-strategy direct

# Preview changes without applying (dry run)
dylan release --minor --dry-run

# Skip git operations
dylan release --minor --no-git

# Specify custom tools
dylan release --tools "Bash,Read,Write,Edit"
```

## Features

- **Project-agnostic**: Works with any project structure
- **Branch-aware**: Detects and uses branching strategy from `.branchingstrategy` file
- **Version detection**: Finds version in common files (pyproject.toml, package.json, etc.)
- **Changelog management**: Updates standard changelog formats
  - Integrates with PR reports to reuse formatted changelog entries
- **Flexible bumping**: Patch, minor, or major version bumps
- **Git integration**: Optional commit and tag creation
- **Merge strategies**: Direct merge or PR creation
- **Dry run mode**: Preview changes before applying

## How It Works

1. Claude detects branch and branching strategy
   - Reads `.branchingstrategy` file if it exists
   - Switches to release branch if needed (e.g., from main to develop)
2. Detects the project's version file
3. Parses current version (X.Y.Z format)
4. Calculates new version based on bump type
5. Searches for PR reports from the current branch
   - Extracts pre-formatted changelog entries if available
6. Updates changelog:
   - Uses PR report entries if found
   - Otherwise moves `[Unreleased]` entries to new version section
7. Creates release commit (optional)
8. Handles merging based on strategy:
   - Direct: Merges release branch to production branch
   - PR: Creates a pull request for the merge
9. Creates git tag (optional)

## Supported Version Files

Claude looks for version in this order:
1. `pyproject.toml` (Python projects)
2. `package.json` (Node.js projects)
3. `Cargo.toml` (Rust projects)
4. `version.txt` or `VERSION` (generic)

## Supported Changelog Files

Claude looks for changelog in this order:
1. `CHANGELOG.md`
2. `HISTORY.md`
3. `NEWS.md`

## Philosophy

This tool exemplifies the dylan philosophy:
- Give Claude complete autonomy
- Minimal wrapper code
- Project-agnostic design
- Trust Claude's decision making

## Example Workflow

```bash
# After merging features to develop
git checkout develop
git pull

# Create a minor release  
dylan release --minor --tag

# Claude will:
# 1. Detect branching strategy from .branchingstrategy
# 2. Find version in pyproject.toml (e.g., 0.4.0)
# 3. Bump to 0.5.0
# 4. Look for PR reports from develop branch
# 5. Update CHANGELOG.md with PR changelog entries
# 6. Create commit: "release: version 0.5.0"
# 7. Merge develop → main (direct strategy)
# 8. Create tag: v0.5.0 on main
# 9. Push both branches and tag
```

### Branching Strategy Configuration

Create a `.branchingstrategy` file in your repository root:

```
release_branch: develop
production_branch: main
merge_strategy: direct
```

## Error Handling

- Clear messages if version/changelog not found
- Validates version format (X.Y.Z)
- Safe operations with dry-run mode
- Comprehensive error reporting