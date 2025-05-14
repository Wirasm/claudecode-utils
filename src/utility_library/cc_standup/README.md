# Claude Code Standup Report Generator

A simple utility that generates stand-up reports using Claude Code, git commits, and GitHub PRs.

## Overview

The cc_standup tool helps developers generate daily stand-up reports by:

1. Collecting your recent git commits (since yesterday by default)
2. Gathering your GitHub pull requests (if configured)
3. Using Claude to create a formatted Markdown stand-up report
4. Displaying a preview and saving the report to a file

## Requirements

- Python 3.12+
- Claude Code CLI installed (`npm i -g @anthropic-ai/claude-code`)
- Git repository
- GitHub access token (optional, for PR collection)

## Installation

### Using uv (recommended)

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows

# Install the package in development mode
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows

# Install the package in development mode
pip install -e .
```

## Environment Setup

Set the following environment variables:

```bash
# Required for Claude Code access
export CLAUDE_API_KEY=your_claude_api_key

# Optional, for GitHub PR collection
export GITHUB_TOKEN=your_github_token
```

## Usage

The standup tool can be run in several ways:

### From the command line

```bash
# Use the installed entry point
standup

# Include PRs since yesterday and open report after generation
standup --open

# Specify a custom date range (ISO format)
standup --since 2025-05-10T00:00:00

# Specify a custom output path
standup --out custom_report.md
```

### From Python code

```python
from src.utility_library.cc_standup import activity, report, provider

# Collect activities
since_dt = datetime.datetime.now() - datetime.timedelta(days=1)
since_iso = since_dt.isoformat()
commits = activity.collect_commits(since_iso)
prs = activity.collect_prs(since_dt)

# Generate report
prompt = report.build_prompt(commits, prs)
claude = provider.get_provider()
markdown = claude.generate(prompt)

# Save report
with open("standup.md", "w") as f:
    f.write(markdown)
```

## Customization

The report format can be customized by editing the prompt template in `report.py`.

## Troubleshooting

1. **Claude Code CLI not found**: Install with `npm i -g @anthropic-ai/claude-code`
2. **CLAUDE_API_KEY not set**: Export your API key in your environment
3. **No git repository found**: Run the tool inside a git repository
4. **No activity found**: The tool will exit if no commits or PRs are found in the specified time range

## License

MIT
