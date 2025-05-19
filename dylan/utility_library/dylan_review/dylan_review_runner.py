#!/usr/bin/env python3
"""Simple Claude Code review runner.

Builds on concept_library/full_review_loop concepts but starts minimal.

This module provides the core review functionality. For CLI usage, use dylan_review_cli.py

Python API usage:
    from dylan.utility_library.dylan_review.dylan_review_runner import run_claude_review, generate_review_prompt

    # Review latest changes
    prompt = generate_review_prompt()
    run_claude_review(prompt)

    # Review specific branch with custom tools and JSON output
    prompt = generate_review_prompt(branch="feature-branch")
    run_claude_review(prompt, allowed_tools=["Bash", "Read", "LS"], output_format="json")
"""

import sys
from typing import Literal

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.progress import create_dylan_progress, create_task_with_dylan


def run_claude_review(
    prompt: str,
    allowed_tools: list[str] | None = None,
    branch: str | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
) -> None:
    """Run Claude code with a review prompt and specified tools.

    Args:
        prompt: The review prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash, Write)
        branch: Optional branch to review (not used in this implementation)
        output_format: Output format (text, json, stream-json)
    """
    # Default safe tools for review
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write"]

    # Determine output file based on format - always in tmp directory
    output_file = "tmp/review_report.json" if output_format == "json" else "tmp/review_report.md"

    console = Console()

    # Create progress bar
    with create_dylan_progress(console) as progress:
        task = create_task_with_dylan(progress, "Running code review...")

        # Get provider and run the review
        provider = get_provider()
        try:
            result = provider.generate(
                prompt,
                output_path=output_file,
                allowed_tools=allowed_tools,
                output_format=output_format
            )
            progress.update(task, completed=True)
            console.print("\n✅ Review completed successfully")
            console.print(f"📝 Report saved to: {output_file}")
            if result:
                console.print(result)
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n❌ Error running review: {e}")
            sys.exit(1)


def generate_review_prompt(branch: str | None = None, output_format: str = "text") -> str:
    """Generate a simple review prompt.

    Args:
        branch: Optional branch to review
        output_format: Output format (text, json, stream-json)

    Returns:
        The review prompt string
    """
    if branch:
        base_prompt = f"Review the changes in branch '{branch}' compared to develop (or main if develop doesn't exist)."
    else:
        base_prompt = "Review the latest changes in this repository compared to develop (or main if develop doesn't exist)."

    # Determine file extension based on format
    extension = ".json" if output_format == "json" else ".md"

    branching_instructions = """
BRANCH STRATEGY DETECTION:
1. Check for .branchingstrategy file in repository root
2. If found, parse release_branch (typically: develop) and use as base for comparison
3. If not found, check for common development branches (develop, development, dev)
4. If none found, fall back to main/master
5. Report which base branch was selected
"""

    return f"""
{base_prompt}

{branching_instructions}

IMPORTANT FILE HANDLING INSTRUCTIONS:
- Save your report to the tmp/ directory
- If tmp/review_report{extension} already exists, create a new file with timestamp
- Format: tmp/review_report_YYYYMMDD_HHMMSS{extension}
- Use the Bash tool to check if the file exists first
- DO NOT modify or append to existing files

Please:
1. Check if tmp/review_report{extension} exists using Bash
2. If it exists, create a new filename with date/timestamp
3. Detect the correct base branch following the BRANCH STRATEGY DETECTION steps
4. Use git diff to see the changes from the detected base branch
5. Identify any issues, bugs, or improvements
6. Provide specific feedback with file and line references
7. Suggest concrete fixes where applicable

Provide your review with the following metadata:
- Report metadata:
    - Report file name
    - Report relative path
    - Branch name
    - Base branch used for comparison
    - List of changed files
    - Date range
    - Number of commits
    - List of commits and their id and message
    - Number of files changed
    - Number of lines added
    - Number of lines removed
- Issue metadata:
    - Issue ID (FORMAT: 001, 002, ...)
    - Affected files list
    - Issue types found (bug, security, performance, style, etc.)
    - Overall severity (critical, high, medium, low)
    - Number of issues found
    - Status (open, fixed, in progress)

Rank the issues by severity and provide a summary of the most critical issues.

For each issue, provide:
- A short description
- A list of affected files
- A list of affected lines
- A list of suggested fixes

**ENSURE YOU ALWAYS RETURN THE FILE NAME AND RELATIVE PATH AS PART OF THE REPORT METADATA**
"""
