# Post-Push PR Creator Hook

A minimal post-push hook that gives Claude Code complete autonomy to create pull requests after pushing commits.

## Overview

This implementation (`post_push_pr_creator.py`) exemplifies the concept library philosophy:
- **Zero validation**: Trust Claude completely
- **Maximum autonomy**: Claude makes all decisions
- **Minimal wrapper**: Under 100 lines of code
- **Rich functionality**: Despite minimal code

## Features

Claude autonomously:
- Detects current branch and remote configuration
- Determines if a PR should be created
- Analyzes all pushed commits
- Generates meaningful PR titles
- Creates comprehensive PR descriptions
- Uses GitHub CLI for PR creation
- Adds appropriate metadata (labels, reviewers, etc.)

## Installation

```bash
# Run the installer
./concept_library/commit_hooks/post_push/post_push_install.sh

# Or manually:
cp concept_library/commit_hooks/post_push/post_push_pr_creator.py .git/hooks/post-push
chmod +x .git/hooks/post-push
```

## How It Works

1. **Triggered After Push**: Runs automatically after `git push`
2. **Claude Analyzes Context**: 
   - Current branch name
   - Pushed commits
   - File changes
   - Existing PRs
3. **Decision Making**:
   - Skip if on main/master
   - Skip if PR exists
   - Create PR for feature branches
4. **PR Creation**:
   - Generate title from branch/commits
   - Create detailed description
   - Use `gh pr create`

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- Claude Code CLI installed
- Git repository with GitHub remote

## Comparison with simple_pr

| Aspect | simple_pr | post-push hook |
|--------|-----------|----------------|
| Trigger | Manual CLI command | Automatic after push |
| Validation | Requires validation file | No validation needed |
| Complexity | ~300 lines | ~100 lines |
| Dependencies | Multiple Python modules | None |
| User Input | Multiple CLI arguments | Zero input |
| Autonomy | Guided by user | Fully autonomous |

## Philosophy

This hook represents the ultimate in trusting Claude Code:
- No complex parsing or validation
- No hardcoded rules or logic
- Complete freedom for Claude to decide
- Minimal code, maximum capability

## Example Claude Workflow

When you run `git push`:

1. Claude detects: `feature/new-widget` branch
2. Finds 5 new commits pushed
3. Analyzes changes: Added widget.py, updated tests
4. Generates title: "Add new widget component"
5. Creates description with:
   - Summary of changes
   - List of commits
   - Testing performed
6. Runs: `gh pr create --title "..." --body "..."`
7. Reports: "✅ Created PR #42"

## Future Enhancements

Claude could autonomously:
- Assign reviewers based on CODEOWNERS
- Add labels based on file types
- Set milestones from branch patterns
- Create draft PRs for WIP branches
- Link related issues