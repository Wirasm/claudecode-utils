#!/usr/bin/env python3
"""Core functionality for the Claude Code development runner.

This module provides the functionality to parse review files and implement fixes
based on the issues identified, prioritizing critical and high-severity issues.

Python API usage:
    from dylan.utility_library.dylan_dev.dylan_dev_runner import run_claude_dev, generate_dev_prompt

    # Generate prompt from review file
    prompt = generate_dev_prompt(review_file="tmp/review.md")

    # Run development process
    run_claude_dev(prompt)
"""

import os
import sys
from pathlib import Path
from typing import Literal

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.config import (
    CLAUDE_CODE_NPM_PACKAGE,
    CLAUDE_CODE_REPO_URL,
    GITHUB_ISSUES_URL,
)
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_dev(
    prompt: str,
    allowed_tools: list[str] | None = None,
    branch: str | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    debug: bool = False,
    interactive: bool = False,
) -> None:
    """Run Claude Code with a development prompt and specified tools.

    Args:
        prompt: The development prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash, Write, Edit, MultiEdit)
        branch: Optional branch to apply fixes to (not used in this implementation)
        output_format: Output format (text, json, stream-json)
        debug: Whether to print debug information (default False)
        interactive: Whether to run in interactive mode (default False)
    """
    # Default safe tools for development
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write", "Edit", "MultiEdit", "TodoRead", "TodoWrite"]

    # Print prompt for debugging
    if debug:
        print("\n===== DEBUG: PROMPT =====\n")
        print(prompt)
        print("\n========================\n")

    # We no longer provide a fixed output file - Claude will determine the correct filename
    # based on the current branch using the format:
    # tmp/dylan-dev-report-<branch>.md
    output_file = None

    # Get provider
    provider = get_provider()

    if interactive:
        # Use shared interactive session utility for consistent behavior
        from ..shared.interactive.utils import run_interactive_session
        result = run_interactive_session(
            provider=provider,
            prompt=prompt,
            allowed_tools=allowed_tools,
            output_format=output_format,
            context_name="development",
            console=console
        )
    else:
        # Non-interactive mode - use progress display and existing output handling
        with create_dylan_progress(console=console) as progress:
            task = create_task_with_dylan(progress, "Dylan is implementing fixes...")
            try:
                result = provider.generate(
                    prompt,
                    output_path=output_file,  # output_file is None, provider handles filename
                    allowed_tools=allowed_tools,
                    output_format=output_format,
                    interactive=False  # Explicitly false
                )
                progress.update(task, completed=True)
                console.print()
                console.print(create_status("Development completed successfully!", "success"))
                console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory[/]")
                console.print(f"[{COLORS['muted']}]Format: dylan-dev-report-<branch>.md[/]")
                console.print()
                console.print(f"[{COLORS['primary']}]{ARROW}[/] [bold]Development Summary[/bold] [{COLORS['accent']}]{SPARK}[/]")
                console.print(f"[{COLORS['muted']}]Dylan has implemented fixes for the issues in your review.[/]")
                console.print()
                if result and "Mock" not in result and "Authentication Error" not in result:
                    console.print(result)  # Display the report content if not a mock or auth error
                elif "Authentication Error" in result:
                    # The auth error from the provider is already well-formatted Markdown.
                    console.print(result)

            except RuntimeError as e:
                progress.update(task, completed=True)
                console.print()
                console.print(create_status(str(e), "error"))
                sys.exit(1)
            except FileNotFoundError:
                progress.update(task, completed=True)
                console.print()
                console.print(create_status("Claude Code not found!", "error"))
                console.print(f"\n[{COLORS['warning']}]Please install Claude Code:[/]")
                console.print(f"[{COLORS['muted']}]  npm install -g {CLAUDE_CODE_NPM_PACKAGE}[/]")
                console.print(f"\n[{COLORS['muted']}]For more info: {CLAUDE_CODE_REPO_URL}[/]")
                sys.exit(1)
            except Exception as e:
                progress.update(task, completed=True)
                console.print()
                console.print(create_status(f"Unexpected error: {e}", "error"))
                console.print(f"\n[{COLORS['muted']}]Please report this issue at:[/]")
                console.print(f"[{COLORS['primary']}]{GITHUB_ISSUES_URL}[/]")
                sys.exit(1)


def generate_dev_prompt(
    review_file: str,
    branch: str | None = None,
    output_file: str | None = None,
    issue_numbers: list[str] | None = None,
    severity_levels: list[str] | None = None,
    dry_run: bool = False,
) -> str:
    """Generate a development prompt based on a review file.

    Args:
        review_file: Path to the review file
        branch: Optional branch to apply fixes to
        output_file: Optional custom output file path
        issue_numbers: Optional list of issue numbers to fix
        severity_levels: Optional list of severity levels to fix
        dry_run: Whether to run in dry run mode

    Returns:
        The development prompt string
    """
    # Check if review file exists
    review_path = Path(review_file)
    if not review_path.exists():
        console.print(create_status(f"Review file not found: {review_file}", "error"))
        sys.exit(1)

    # Create tmp directory if it doesn't exist
    os.makedirs("tmp", exist_ok=True)

    # Determine branch name if not provided
    branch_instruction = """
BRANCH DETERMINATION:
1. If the branch was specified in the command (--branch), use that branch.
2. Otherwise, determine the current branch: git symbolic-ref --short HEAD
3. Checkout the branch before making any changes: git checkout <branch>
"""

    # Filter issues based on severity and/or issue numbers
    filter_instruction = """
ISSUE FILTERING:
1. Read the review file and identify all issues.
2. Filter issues based on severity levels and issue numbers (if specified).
3. Sort filtered issues by severity (critical first, then high, medium, low).
"""

    # Add severity filter if provided
    if severity_levels:
        filter_instruction += f"\nSeverity filter: {', '.join(severity_levels)}"

    # Add issue number filter if provided
    if issue_numbers:
        filter_instruction += f"\nIssue number filter: {', '.join(issue_numbers)}"

    # Set up file handling instructions
    file_handling = """
FILE HANDLING INSTRUCTIONS:
1. Determine the branch name from the BRANCH DETERMINATION steps
2. Create the output filename in this format: tmp/dylan-dev-report-<branch>.md
   - Replace any slashes in branch names with hyphens (e.g., feature/foo becomes feature-foo)
   - Do not add timestamps to the filename itself
3. Save the development report to this file using the Write tool
"""

    # Custom output file path if provided
    if output_file:
        file_handling = f"""
FILE HANDLING INSTRUCTIONS:
1. Save the development report to: {output_file}
"""

    # Development process steps
    dev_steps = """
DEVELOPMENT STEPS:
1. Read the review file to understand the issues
2. Filter issues based on severity and issue numbers
3. For each issue:
   a. Understand the problem and the suggested fix
   b. Navigate to the affected files using the provided file paths
   c. Implement the fix using the appropriate tools
   d. Verify the fix works correctly
4. Document each implemented fix in the development report
5. Save the report to the specified output file
"""

    # Dry run mode instruction
    dry_run_instruction = ""
    if dry_run:
        dry_run_instruction = """
DRY RUN MODE:
This is a dry run mode. Do not actually make any changes to the code.
Instead, describe in detail how you would fix each issue, including:
- The exact changes you would make
- The files and line numbers you would modify
- Sample code snippets showing the before and after state
But DO NOT actually execute any Edit, Write, or MultiEdit tools that would modify files.
"""

    # Development report format
    report_format = """
DEVELOPMENT REPORT FORMAT:
1. Summary
   - Overview of fixes implemented
   - Number of issues fixed per severity level
   - Brief description of approach taken

2. Fixed Issues
   - Section for each severity level (Critical, High, Medium, Low)
   - For each issue:
     - Issue ID and description from the review
     - Files modified
     - Changes made
     - Explanation of how the fix addresses the issue

3. Verification
   - Description of how you verified the fixes work
   - Results of any tests run

4. Issues Not Fixed
   - Any issues that couldn't be fixed and why
   - Recommendations for addressing them

5. Next Steps
   - Suggested follow-up actions
   - Any potential improvements beyond the scope of the current fixes
"""

    return f"""
Implement fixes for issues identified in a code review.

{branch_instruction}

{filter_instruction}

{file_handling}

{dev_steps}

{dry_run_instruction}

{report_format}

IMPORTANT INSTRUCTIONS:
- First, verify the review file exists: {review_file}
- Focus on implementing fixes for the highest priority issues first (Critical, then High, etc.)
- Only fix the issues that match the specified filters (severity levels and issue numbers)
- Make minimal, focused changes to fix each issue
- Test each fix to ensure it resolves the issue without introducing new problems
- Document all changes made in the development report
- Save the report to the specified output file using the Write tool
- Include code snippets and explanations for each fix
- Use git commands to track your changes and check the current state of the codebase
"""
