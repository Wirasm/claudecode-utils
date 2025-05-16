#!/usr/bin/env python3
"""
Simple Claude Code review runner.
Builds on concept_library/full_review_loop concepts but starts minimal.

Command-line usage:
    # Review latest changes (default)
    uv run src/utility_library/cc_review/cc_review_runner.py

    # Review a specific branch
    uv run src/utility_library/cc_review/cc_review_runner.py feature-branch

    # With additional options
    uv run src/utility_library/cc_review/cc_review_runner.py feature-branch --tools Read,Bash,LS

    # Get structured output with JSON format
    uv run src/utility_library/cc_review/cc_review_runner.py feature-branch --format json

Options:
    branch        Optional branch name to review (positional argument)
    --tools       Comma-separated list of allowed tools (default: Read,Glob,Grep,LS,Bash)
    --format      Output format: text, json, stream-json (default: text)

Example:
    # Review changes in 'develop' branch with limited tools
    uv run src/utility_library/cc_review/cc_review_runner.py develop --tools Read,Bash

    # Get JSON output for parsing/automation
    uv run src/utility_library/cc_review/cc_review_runner.py develop --format json

Python API usage:
    from src.utility_library.cc_review.cc_review_runner import run_claude_review, generate_review_prompt

    # Review latest changes
    prompt = generate_review_prompt()
    run_claude_review(prompt)

    # Review specific branch with custom tools and JSON output
    prompt = generate_review_prompt(branch="feature-branch")
    run_claude_review(prompt, allowed_tools=["Bash", "Read", "LS"], output_format="json")
"""

import argparse
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
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash)
        branch: Optional branch to review (defaults to current branch)
        output_format: Output format (text, json, stream-json)
    """
    # Default safe tools for review
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash"]

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
        file_instruction = "Save your report as a JSON file named 'review_report.json' in the root of the repository with the structured data format described above."
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
    - Branch name
    - List of changed files
    - Date range
    - Number of commits
    - Number of files changed
    - Number of lines added
    - Number of lines removed
- Issue metadata:
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
"""


def main():
    """Main entry point for the review runner."""
    parser = argparse.ArgumentParser(
        description="Run Claude Code review on repository changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review latest changes
  %(prog)s

  # Review specific branch
  %(prog)s feature-branch

  # Review branch with specific tools
  %(prog)s develop --tools Read,Bash

  # Review with JSON output for structured data
  %(prog)s feature-branch --format json
        """,
    )

    parser.add_argument("branch", nargs="?", help="Branch to review (optional, defaults to latest changes)")

    parser.add_argument("--tools", default="Read,Glob,Grep,LS,Bash", help="Comma-separated list of allowed tools")

    parser.add_argument(
        "--format", default="text", choices=["text", "json", "stream-json"], help="Output format (default: text)"
    )

    args = parser.parse_args()

    # Parse tools
    allowed_tools = [tool.strip() for tool in args.tools.split(",")]

    # Generate prompt
    prompt = generate_review_prompt(branch=args.branch, output_format=args.format)

    # Run review
    run_claude_review(prompt, allowed_tools=allowed_tools, output_format=args.format)


if __name__ == "__main__":
    main()
