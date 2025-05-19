# Dylan PR Creator

A minimal Claude Code utility for autonomous pull request creation.

## Overview

The `dylan pr` command gives Claude Code complete autonomy to analyze commits and create pull requests. It follows the same minimal philosophy as other dylan utilities.

The command saves its report to the `tmp/` directory with branch-aware naming for better tracking across multiple PRs.

## Usage

```bash
# Create PR from current branch to develop (default)
dylan pr

# Create PR from specific branch to develop
dylan pr feature-branch

# Create PR with custom target branch
dylan pr feature-branch --target main

# Create PR with changelog section
dylan pr --changelog

# Use JSON output format
dylan pr --format json

# Specify custom tools
dylan pr --tools "Bash,Read,Write"
```

## Features

- **Automatic branch detection**: Uses current branch if none specified
- **Rich PR descriptions**: Claude generates comprehensive PR content
- **Changelog support**: Add formatted changelog section to PR description with `--changelog`
- **Branch-aware reports**: Reports include branch name for better organization
- **Incremental updates**: Appends to existing PR reports for the same branch
- **GitHub CLI integration**: Uses `gh` command for PR creation
- **Minimal validation**: Trusts Claude to handle edge cases
- **Multiple output formats**: Supports text and JSON output

## How It Works

1. Claude analyzes the branch context and commits
2. Determines if a PR is needed
3. Generates PR title from branch name or commits
4. Creates detailed description with:
   - Summary of changes
   - List of commits
   - Files modified
   - Changelog section (if `--changelog` flag is used)
   - Testing notes
5. Uses GitHub CLI to create the PR
6. Reports results with PR URL
7. Saves report to `tmp/pr_report_<branch>_<timestamp>.md`
   - Branch name is sanitized (slashes replaced with dashes)
   - Appends to existing report if one exists for the branch

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- Git repository with GitHub remote
- Claude Code CLI installed

## Philosophy

This tool exemplifies the dylan philosophy:
- Give Claude complete autonomy
- Minimal wrapper code (~100 lines)
- Trust Claude's decision making
- No complex validation logic

## Example Output

```
Claude process completed successfully
✅ Created PR #123: Add new feature
URL: https://github.com/org/repo/pull/123

Summary:
- Analyzed 5 commits in feature/new-widget branch
- Generated PR title from branch name
- Created comprehensive description
- Successfully opened PR against main branch
```