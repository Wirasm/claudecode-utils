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
from ..shared.config import CLAUDE_CODE_NPM_PACKAGE, CLAUDE_CODE_REPO_URL, GITHUB_ISSUES_URL
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_review(
    prompt: str,
    allowed_tools: list[str] | None = None,
    branch: str | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    debug: bool = False,
) -> None:
    """Run Claude code with a review prompt and specified tools.

    Args:
        prompt: The review prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash, Write)
        branch: Optional branch to review (not used in this implementation)
        output_format: Output format (text, json, stream-json)
        debug: Whether to print debug information (default False)
    """
    # Default safe tools for review
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write", "Edit", "MultiEdit", "TodoRead", "TodoWrite"]

    # Print prompt for debugging
    if debug:
        print("\n===== DEBUG: PROMPT =====\n")
        print(prompt)
        print("\n========================\n")

    # We no longer provide a fixed output file - Claude will determine the correct filename
    # based on the current branch and target branch using the format:
    # tmp/dylan-review-compare-[current-branch]-to-[target].<extension>
    output_file = None

    # Get provider and run the review
    provider = get_provider()

    with create_dylan_progress(console=console) as progress:
        # Start the review task
        task = create_task_with_dylan(progress, "Dylan is working on the code review...")

        try:
            result = provider.generate(
                prompt,
                output_path=output_file,
                allowed_tools=allowed_tools,
                output_format=output_format,
            )

            # Update task to complete
            progress.update(task, completed=True)

            # Success message with flair
            console.print()
            console.print(create_status("Code review completed successfully!", "success"))
            console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory[/]")
            console.print(f"[{COLORS['muted']}]Format: dylan-review-compare-<branch>-to-<target>.md[/]")
            console.print()

            # Show a nice completion message
            console.print(f"[{COLORS['primary']}]{ARROW}[/] [bold]Review Summary[/bold] [{COLORS['accent']}]{SPARK}[/]")
            console.print(f"[{COLORS['muted']}]Dylan has analyzed your code and generated a detailed report.[/]")
            console.print()

            if result and "Mock" not in result:  # Don't show mock results
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


def generate_review_prompt(branch: str | None = None, output_format: str = "text") -> str:
    """Generate a simple review prompt.

    Args:
        branch: Optional branch to review
        output_format: Output format (text, json, stream-json)

    Returns:
        The review prompt string
    """
    # Determine file extension based on format
    extension = ".json" if output_format == "json" else ".md"

    branching_instructions = """
BRANCH STRATEGY DETECTION:
1. First, determine the current branch using: git symbolic-ref --short HEAD
2. Check for .branchingstrategy file in repository root
3. If found, parse release_branch (typically: develop) and use as target for comparison
4. If not found, check for common development branches (develop, development, dev)
5. If none found, fall back to main/master as the target branch
6. Report both the current branch and target branch in the metadata
"""

    file_handling_instructions = f"""
FILE HANDLING INSTRUCTIONS:
1. Create the tmp/ directory if it doesn't exist: mkdir -p tmp
2. Determine the current branch: git symbolic-ref --short HEAD
3. Determine the target branch from the BRANCH STRATEGY DETECTION steps
4. Create a filename in this format: tmp/dylan-review-compare-[current-branch]-to-[target]{extension}
   - Replace any slashes in branch names with hyphens (e.g., feature/foo becomes feature-foo)
   - DO NOT add timestamps to the filename itself
5. If the file already exists:
   - Read the existing file to understand previous reviews
   - APPEND to the existing file with a clear separator
   - Add a timestamp header: ## Review [DATE] [TIME]
   - This allows tracking multiple reviews over time
"""

    review_steps = """
REVIEW STEPS:
1. Determine current branch and target branch following the strategy detection
2. Create the properly formatted output filename as specified in FILE HANDLING
3. Use git diff to analyze the changes from the current branch to the target branch
   - git diff [target]...[current] for detailed changes
   - git diff --stat [target]...[current] for change statistics
   - git log [target]...[current] for commit history
4. Identify issues, bugs, or improvements in the code
5. Provide specific feedback with file and line references
6. Suggest concrete fixes for each issue
7. Format the report according to the metadata requirements
8. Save the report to the determined filename
"""

    return f"""
Review the changes in the current branch compared to the target branch (develop or main).

{branching_instructions}

{file_handling_instructions}

{review_steps}

Provide your review with the following metadata:
- Report metadata:
    - Report file name (dylan-review-compare-[current-branch]-to-[target]{extension})
    - Report relative path (tmp/dylan-review-compare-[current-branch]-to-[target]{extension})
    - Current branch name
    - Target branch used for comparison
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

**IMPORTANT INSTRUCTIONS:**
- Always append your review to the file if it already exists, with a timestamp header separating reviews
- DO NOT add timestamps to the filename itself
- Always include a "Steps Executed" section listing all commands and decisions you made
- Use the exact filename format: tmp/dylan-review-compare-[current-branch]-to-[target]{extension}
"""
