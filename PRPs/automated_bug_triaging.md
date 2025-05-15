name: "Automated Bug Triaging"
description: |

# Product Requirement Prompt: Automated Bug Triaging

## Goal

Create a lightweight proof-of-concept tool that uses Claude to analyze GitHub issues, categorize them by severity and type, assign them to appropriate components, generate reproduction steps, and suggest potential fixes.

## Why

- Software projects often accumulate large numbers of bug reports that require manual triage
- Manual bug triaging is time-consuming and subjective, leading to inconsistent prioritization
- Automating the bug triage process helps teams focus on the most critical issues first
- NLP analysis can extract key information from bug reports that might be missed in manual review
- AI-generated reproduction steps and fix suggestions accelerate the debugging process

## What

A CLI tool that uses Claude to analyze GitHub issue contents and:

1. Categorize the severity of bugs (critical, high, medium, low)
2. Determine the bug type (functional, UI/UX, performance, security, etc.)
3. Assign to appropriate components based on codebase structure
4. Generate clear reproduction steps from sometimes unclear bug descriptions
5. Suggest potential approaches for fixing the issues

The tool should follow the project's philosophy of minimal validation and leverage Claude to do most of the analysis work.

## Current Directory Structure

```
concept_library/
├── README.md
├── __init__.py
├── cc_PRP_flow/
│   ├── PRPs/
│   ├── README.md
│   ├── ai_docs/
│   └── scripts/
├── concept_analysis.md
├── full_review_loop/
├── innovative_concepts.md
├── potential_concepts.md
├── simple_dev/
├── simple_pr/
├── simple_review/
└── simple_validator/
```

## Proposed Directory Structure

```
concept_library/
├── automated_bug_triage/
│   ├── README.md          # Documentation for the concept
│   ├── __init__.py        # Make it a proper module
│   ├── bug_triage_poc.py  # Main implementation
│   └── tests/             # Basic tests
│       ├── __init__.py
│       └── test_bug_triage.py
```

## Files to Reference

- `concept_library/simple_review/simple_review_poc.py` (read_only) Example of a minimal concept implementation using Claude
- `src/utility_library/cc_standup/activity.py` (read_only) Contains GitHub API integration patterns to follow
- `concept_library/cc_PRP_flow/scripts/cc_runner_simple.py` (read_only) Example of Claude command execution
- `concept_library/potential_concepts.md` (read_only) Original concept description

## Files to Implement

### Core Implementation

1. `concept_library/automated_bug_triage/bug_triage_poc.py` - Main implementation file

```python
#!/usr/bin/env -S uv run --script
"""
Automated Bug Triaging - A proof-of-concept tool that uses Claude to analyze GitHub issues.

This tool:
1. Fetches GitHub issues from a repository
2. Uses Claude to categorize issues by severity and type
3. Assigns issues to components
4. Generates reproduction steps
5. Suggests potential fixes

Use calude codes tools for as many of these steps as possible

Typical usage:
    # Analyze all open issues in a repository
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo

    # Analyze a specific issue
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --issue 123

    # Analyze issues with a specific label
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --label bug

    # Generate a markdown report
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --output report.md

Arguments:
    --repo          Repository name in format "owner/repo"
    --issue         Specific issue number to analyze (optional)
    --label         Filter issues by label (optional)
    --max-issues    Maximum number of issues to analyze (default: 10)
    --output        Output file path for the report (default: bug_triage_report.md)
    --model         Claude CLI executable name (default: "claude")
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Import PyGithub with fallback
try:
    from github import Github, Auth
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Constants
DEFAULT_MAX_ISSUES = 10
DEFAULT_OUTPUT = "bug_triage_report.md"
DEFAULT_MODEL = "claude"

def main():
    # Implementation goes here
    pass

if __name__ == "__main__":
    main()
```

2. `concept_library/automated_bug_triage/README.md` - Documentation for the concept

````markdown
# Automated Bug Triaging

A proof-of-concept tool that uses Claude to analyze GitHub issues, helping teams prioritize and address bugs more efficiently.

## Features

- Fetches GitHub issues from a repository
- Uses Claude to categorize issues by severity and type
- Assigns issues to components based on codebase analysis
- Generates clear reproduction steps from bug descriptions
- Suggests potential fixes to accelerate debugging

## Usage

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
````

## Requirements

- Python 3.8+
- Claude CLI installed and configured
- GitHub access token (set as GITHUB_TOKEN environment variable)
- PyGithub (optional, will fallback to GitHub CLI if not available)

```

## Implementation Notes

### GitHub Issue Retrieval

- Use PyGithub if available (same pattern as in cc_standup/activity.py)
- Fall back to GitHub CLI (gh) if PyGithub is not available
- Support filtering by issue number, label, and state
- Handle pagination for repositories with many issues
- Respect rate limits to avoid API throttling

### Issue Analysis with Claude

- Use Claude to analyze issue title, description, and comments
- Structure the prompt to guide Claude in extracting the relevant information
- Process issues in batches to respect context limits
- Include repository structure information to help with component assignment
- Use a consistent output format for further processing

### Report Generation

- Generate a markdown report with sections for each analyzed issue
- Include all categorization and analysis results
- Format the report for easy human readability
- Add summary statistics at the beginning of the report

### Error Handling

- Handle GitHub API exceptions gracefully
- Provide useful error messages when issues arise
- Include fallback strategies when possible
- Log errors for debugging purposes

## Validation Gates

- Script should run without errors when given a valid repository
- Claude should successfully analyze and categorize issues
- Report should be generated in markdown format
- Any external dependencies should be properly handled with fallbacks

## Implementation Checkpoints

### 1. GitHub Issue Retrieval

- Successfully fetch issues from a repository
- Handle authentication and API limits
- Support filtering by issue number, label, and state
- Command to verify: `python bug_triage_poc.py --repo owner/repo --dry-run`

### 2. Issue Analysis with Claude

- Successfully send issue data to Claude for analysis
- Receive structured responses from Claude
- Extract categorizations from Claude's response
- Command to verify: `python bug_triage_poc.py --repo owner/repo --issue 123 --verbose`

### 3. Report Generation

- Generate well-formatted markdown reports
- Include all analysis results in a readable format
- Command to verify: `python bug_triage_poc.py --repo owner/repo --output report.md`

## Other Considerations

- Privacy and security: Be mindful of sensitive information in issues
- Performance: Batch processing for larger repositories
- Error handling: Graceful fallbacks when APIs or services are unavailable
- Extensibility: Consider future enhancements such as:
  - Automatic issue labeling via GitHub API
  - Integration with other issue tracking systems
  - Component extraction from repository structure
  - Automated test case generation from reproduction steps
```
