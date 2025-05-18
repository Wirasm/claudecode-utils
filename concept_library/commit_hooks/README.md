# Commit Hooks with Claude Code

This directory contains experimental git commit hooks that leverage Claude Code for various development workflow enhancements.

## Directory Structure

```
commit_hooks/
├── README.md
├── __init__.py
├── prepare_commit_msg/
│   ├── prepare_commit_msg.py         # The main hook script
│   ├── prepare_commit_msg_install.sh # Installation script
│   └── prepare_commit_msg_test.py    # Test script for development
└── pre_push/
    ├── pre_push_version_bump.py     # Version bump hook script
    ├── pre_push_install.sh          # Installation script
    └── pre_push_test.py             # Test script for development
```

## Available Hooks

### 1. Prepare Commit Message (prepare-commit-msg)

Automatically generates conventional commit messages using Claude Code by analyzing staged changes.

**Features:**
- Generates conventional commit messages (feat, fix, docs, etc.)
- Max-plan-aware (works with OAuth or API key)
- Automatic auth fallback
- Considers staged diff for context
- Non-blocking on failures

**Quick Install:**
```bash
# Run the installer
./concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg_install.sh

# Or manually:
cp concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg.py .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

**Uninstall:**
```bash
rm .git/hooks/prepare-commit-msg
```

### 2. Pre-Push Version Bump (pre-push)

Automatically bumps version and updates CHANGELOG.md based on conventional commits.

**Features:**
- Analyzes commits since last version tag
- Never bumps major version (development mode)
- Updates pyproject.toml version
- Prepends changes to CHANGELOG.md
- Exits for review before push

**Quick Install:**
```bash
# Run the installer
./concept_library/commit_hooks/pre_push/pre_push_install.sh

# Or manually:
cp concept_library/commit_hooks/pre_push/pre_push_version_bump.py .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

**Uninstall:**
```bash
rm .git/hooks/pre-push
```

## Philosophy

Following the concept library principles:
- Minimal validation
- Zero to minimal wrappers around Claude Code
- Direct subprocess calls to `claude`
- Graceful failures (never block commits)

## Future Hook Concepts

- `pre-commit`: AI-powered linting and code quality checks
- `commit-msg`: Validate and enhance commit messages  
- `post-commit`: Generate documentation or update issues
- `pre-push`: Final review before pushing to remote
- `post-merge`: Update dependencies or run migrations
- `pre-rebase`: Analyze potential conflicts

## Requirements

- Claude Code CLI installed (`npm i -g @anthropic-ai/claude-code`)
- Git repository
- Python 3.12+
- Either Max OAuth login or ANTHROPIC_API_KEY

## Development

To test hooks during development:

**prepare-commit-msg:**
```bash
# Run the test script
python concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg_test.py

# Or test manually
git add -A
python concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg.py .git/COMMIT_EDITMSG
```

**pre-push:**
```bash
# Test the version bump logic
python concept_library/commit_hooks/pre_push/pre_push_test.py

# Or run directly
python concept_library/commit_hooks/pre_push/pre_push_version_bump.py
```
