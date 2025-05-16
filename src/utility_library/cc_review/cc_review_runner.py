#!/usr/bin/env python3
"""
Simple Claude Code review runner.
Builds on concept_library/full_review_loop concepts but starts minimal.

This module provides the core review functionality. For CLI usage, use cc_review_cli.py

Python API usage:
    from src.utility_library.cc_review.cc_review_runner import run_claude_review, generate_review_prompt

    # Review latest changes
    prompt = generate_review_prompt()
    run_claude_review(prompt)

    # Review specific branch with custom tools and JSON output
    prompt = generate_review_prompt(branch="feature-branch")
    run_claude_review(prompt, allowed_tools=["Bash", "Read", "LS"], output_format="json")
"""

import subprocess
import sys
from typing import List, Optional


def run_claude_review(
    prompt: str,
    allowed_tools: Optional[List[str]] = None,
    branch: Optional[str] = None,
    output_format: str = "text",
) -> None:
    """Run Claude code with a review prompt and specified tools.

    Args:
        prompt: The review prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash, Write)
        branch: Optional branch to review (defaults to current branch)
        output_format: Output format (text, json, stream-json)
    """
    # Default safe tools for review
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write"]

    # Build the command
    command = ["claude", "-p", prompt]

    # Add output format
    if output_format != "text":
        command.extend(["--output-format", output_format])

    # Add allowed tools
    if allowed_tools:
        command.extend(["--allowedTools"] + allowed_tools)

    # Run the command
    try:
        subprocess.run(command, check=True)
        print("Claude process completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude: {e}")
        sys.exit(1)


def generate_review_prompt(branch: Optional[str] = None, output_format: str = "text") -> str:
    """Generate a simple review prompt.

    Args:
        branch: Optional branch to review
        output_format: Output format (text, json, stream-json)

    Returns:
        The review prompt string
    """
    if branch:
        base_prompt = f"Review the changes in branch '{branch}' compared to main."
    else:
        base_prompt = "Review the latest changes in this repository."

    # Determine file format and name based on output format
    if output_format == "json":
        file_instruction = """Save your report as a JSON file named 'review_report.json' in the root of the
        repository with the structured data format described above.

IMPORTANT: When generating JSON output valid JSON, ensure proper escaping:
- Escape all backslashes (\\) as double backslashes (\\\\)
- Use proper JSON escaping for special characters
- Be careful with strings containing Unix paths or regex patterns
- Test that the output is valid JSON before saving"""
    else:
        file_instruction = "Save your report as a markdown file named 'review_report.md' in the root of the repository."

    return f"""
{base_prompt}

Please:
1. Use git diff to see the changes
2. Identify any issues, bugs, or improvements
3. Provide specific feedback with file and line references
4. Suggest concrete fixes where applicable

Provide your review with the following metadata:
- Report metadata:
    - Report file name
    - Report relative path
    - Branch name
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

{file_instruction}
**ENSURE YOU ALWAYS RETURN THE FILE NAME AND RELATIVE PATH AS PART OF THE REPORT METADATA**
"""
