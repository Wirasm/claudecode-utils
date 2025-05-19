# Commit Hooks with Claude Code

This directory contains experimental git commit hooks that leverage Claude Code for various development workflow enhancements.

## Directory Structure

```
commit_hooks/
├── README.md
├── __init__.py
├── prepare_commit_msg/
│   ├── prepare_commit_msg.py         # Autonomous commit message generator
│   ├── prepare_commit_msg_install.sh # Installation script
│   └── prepare_commit_msg_test.py    # Test script for development
├── pre_push/
│   ├── pre_push_version_bump.py      # Autonomous version/changelog updater
│   ├── pre_push_install.sh           # Installation script
│   └── pre_push_test.py              # Test script for development
└── post_push/
    ├── post_push_pr_creator.py       # Autonomous PR creator
    ├── post_push_install.sh          # Installation script
    └── README.md                     # Detailed documentation
```

## Available Hooks

### 1. Prepare Commit Message - Minimal Autonomous Version (prepare-commit-msg)

Gives Claude Code COMPLETE AUTONOMY to analyze staged changes and generate commit messages.

**Features:**
- Trusts Claude to analyze staged changes with git diff
- Lets Claude determine the perfect conventional commit format
- Prints the generated message to terminal for visibility
- Zero validation - maximum trust in Claude's analysis
- Fails gracefully - never blocks commits on errors
- No authentication fallback complexity

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

### 2. Pre-Push Hook - Minimal Autonomous Version (pre-push)

Gives Claude Code COMPLETE AUTONOMY to analyze commits and update project files.

**Features:**
- Trusts Claude to analyze all commits being pushed
- Lets Claude decide appropriate version bumps
- Allows Claude to format CHANGELOG.md as it sees fit
- Enables Claude to run optional checks based on changes
- Fails gracefully - never blocks pushes on errors
- Zero validation - maximum trust in Claude's decisions

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

### 3. Post-Push PR Creator - Minimal Autonomous Version (post-push)

Gives Claude Code COMPLETE AUTONOMY to create pull requests after pushing commits.

**Features:**
- Automatically triggered after git push
- Analyzes pushed commits and branch context
- Decides autonomously if PR should be created
- Generates rich PR titles and descriptions
- Uses GitHub CLI for PR creation
- Zero user input required
- Handles all edge cases gracefully

**Quick Install:**
```bash
# Run the installer
./concept_library/commit_hooks/post_push/post_push_install.sh

# Or manually:
cp concept_library/commit_hooks/post_push/post_push_pr_creator.py .git/hooks/post-push
chmod +x .git/hooks/post-push
```

**Uninstall:**
```bash
rm .git/hooks/post-push
```

**Requirements:**
- GitHub CLI (`gh`) must be installed and authenticated
- Repository must have GitHub remote configured

## Philosophy

Following the concept library principles:
- **Maximum Trust**: Give Claude complete autonomy
- **Minimal Validation**: Zero validation of Claude's outputs
- **Simple Wrappers**: Minimal code around Claude Code
- **Direct Calls**: Simple subprocess calls to `claude`
- **Graceful Failures**: Never block git operations on errors
- **Transparency**: Show Claude's output to users

## Future Hook Concepts

- `pre-commit`: AI-powered linting and code quality checks
- `commit-msg`: Validate and enhance commit messages  
- `post-commit`: Generate documentation or update issues
- `post-merge`: Update dependencies or run migrations
- `pre-rebase`: Analyze potential conflicts
- `post-checkout`: Setup branch-specific environments
- `post-rewrite`: Update related issues after rebases

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
