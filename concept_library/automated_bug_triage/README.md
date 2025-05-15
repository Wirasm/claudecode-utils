# Automated Bug Triaging

A proof-of-concept tool that uses Claude to analyze GitHub issues, helping teams prioritize and address bugs more efficiently.

## Features

- Fetches GitHub issues from a repository
- Uses Claude to categorize issues by severity and type
- Assigns issues to components based on codebase analysis
- Generates clear reproduction steps from bug descriptions
- Suggests potential fixes to accelerate debugging

## Implementations

This concept provides two different implementations:

### 1. Structured Implementation (`bug_triage_poc.py`)

A traditional implementation with structured Python code that:
- Handles GitHub API integration
- Processes issues in a programmatic way
- Provides granular control over each step

```bash
# Analyze all open issues in a repository
uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo

# Analyze a specific issue
uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --issue 123

# Analyze issues with a specific label
uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --label bug

# Generate a markdown report
uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --output report.md
```

### 2. Claude-driven Implementation (`bug_triage_claude_poc.py`)

A minimal implementation that delegates the entire workflow to Claude Code using natural language:
- Gives Claude Code a detailed prompt about what to do
- Uses Bash tools to interact with GitHub CLI
- Demonstrates how Claude Code can handle complex workflows with minimal code

```bash
# Analyze all open issues in a repository
uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo

# Analyze a specific issue
uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --issue 123

# Analyze issues with a specific label
uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --label bug

# Generate a markdown report
uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --output report.md
```

## Requirements

- Python 3.8+
- Claude CLI installed and configured
- GitHub access token (set as GITHUB_TOKEN environment variable)
- PyGithub (optional, will fallback to GitHub CLI if not available)
- GitHub CLI (gh) installed and authenticated