# Dylan Release Manager

A minimal Claude Code utility for autonomous project releases.

## Overview

The `dylan release` command gives Claude Code complete autonomy to create project releases. It handles version bumping, changelog updates, and git operations in a project-agnostic way.

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

# Preview changes without applying (dry run)
dylan release --minor --dry-run

# Skip git operations
dylan release --minor --no-git

# Specify custom tools
dylan release --tools "Bash,Read,Write,Edit"
```

## Features

- **Project-agnostic**: Works with any project structure
- **Version detection**: Finds version in common files (pyproject.toml, package.json, etc.)
- **Changelog management**: Updates standard changelog formats
- **Flexible bumping**: Patch, minor, or major version bumps
- **Git integration**: Optional commit and tag creation
- **Dry run mode**: Preview changes before applying

## How It Works

1. Claude detects the project's version file
2. Parses current version (X.Y.Z format)
3. Calculates new version based on bump type
4. Updates version in the appropriate file
5. Moves `[Unreleased]` changelog entries to new version section
6. Creates release commit (optional)
7. Creates git tag (optional)

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
# After merging features to main
git checkout main
git pull

# Create a minor release
dylan release --minor --tag

# Claude will:
# 1. Find version in pyproject.toml (e.g., 0.4.0)
# 2. Bump to 0.5.0
# 3. Update pyproject.toml
# 4. Move [Unreleased] to [0.5.0] in CHANGELOG.md
# 5. Create commit: "release: version 0.5.0"
# 6. Create tag: v0.5.0
```

## Error Handling

- Clear messages if version/changelog not found
- Validates version format (X.Y.Z)
- Safe operations with dry-run mode
- Comprehensive error reporting