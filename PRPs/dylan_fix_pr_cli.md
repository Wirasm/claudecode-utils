name: "Dylan Fix PR CLI Implementation"
description: |
A new command for the Dylan CLI that automates the implementation of fixes based on GitHub pull request comments and review feedback.

## Goal

Create a new `dylan fix-pr` command that automatically analyzes a GitHub pull request, identifies issues mentioned in comments and reviews, implements fixes for those issues, and integrates seamlessly with the existing Dylan CLI workflow.

## Why

- **Efficiency**: Automates the process of addressing feedback in PR comments, saving developer time
- **Integration**: Directly ties into the GitHub PR workflow that many developers already use
- **Consistency**: Ensures that PR feedback is addressed following best practices and coding standards
- **Transparency**: Provides detailed reports on what changes were made and why
- **Completeness**: Fills a gap in the existing workflow by connecting PR review with automated fix implementation
- **Collaboration**: Improves the collaborative development process by reducing feedback loops

## What

The `dylan fix-pr` command will:

- Accept a GitHub PR URL or PR number
- Use GitHub CLI (`gh`) to:
  - Fetch the complete PR (description, comments, review threads, checks)
  - Check out the PR branch locally
- Pass the entire PR content to Claude Code
- Let Claude Code analyze the PR to identify issues that need fixing
- Apply fixes to the PR branch
- Generate a development report detailing changes made
- Optionally push changes back to the remote branch
- Support various options for controlling the fix implementation process

## Endpoints/APIs to Implement

N/A - This feature implements a CLI command, not an API endpoint.

## Current Directory Structure

```
dylan/
├── cli.py                                # Main CLI entry point
├── utility_library/
│   ├── dylan_review/                     # Review functionality
│   │   ├── __init__.py
│   │   ├── dylan_review_cli.py           # Review CLI interface
│   │   └── dylan_review_runner.py        # Review core functionality
│   ├── dylan_dev/                        # Dev functionality from first PRP
│   │   ├── __init__.py
│   │   ├── dylan_dev_cli.py              # Dev CLI interface
│   │   └── dylan_dev_runner.py           # Dev core functionality
│   ├── dylan_pr/                         # PR functionality
│   │   ├── __init__.py
│   │   ├── dylan_pr_cli.py               # PR CLI interface
│   │   └── dylan_pr_runner.py            # PR core functionality
│   ├── provider_clis/                    # Provider interfaces
│   │   ├── __init__.py
│   │   ├── provider_claude_code.py       # Claude Code provider
│   │   └── shared/
│   │       ├── __init__.py
│   │       └── subprocess_utils.py       # Subprocess utilities
│   └── shared/                           # Shared utilities and UI components
│       ├── __init__.py
│       ├── config.py                     # Configuration
│       ├── error_handling.py             # Error handling
│       ├── exit_command.py               # Exit command handling
│       ├── progress.py                   # Progress reporting
│       └── ui_theme.py                   # UI theme components
```

## Proposed Directory Structure

```
dylan/
├── cli.py                                # Updated to add fix-pr command
├── utility_library/
│   ├── dylan_review/                     # Existing review functionality
│   │   ├── __init__.py
│   │   ├── dylan_review_cli.py
│   │   └── dylan_review_runner.py
│   ├── dylan_dev/                        # Existing dev functionality
│   │   ├── __init__.py
│   │   ├── dylan_dev_cli.py
│   │   └── dylan_dev_runner.py
│   ├── dylan_fix_pr/                     # New fix-pr functionality
│   │   ├── __init__.py
│   │   ├── dylan_fix_pr_cli.py           # Fix PR CLI interface
│   │   └── dylan_fix_pr_runner.py        # Fix PR core functionality
│   ├── dylan_pr/                         # Existing PR functionality
│   │   ├── __init__.py
│   │   ├── dylan_pr_cli.py
│   │   └── dylan_pr_runner.py
│   └── ... (other existing directories)
```

## Files to Reference

- `/Users/rasmus/Projects/claudecode-utility/concept_library/simple_dev/simple_dev_poc.py` (read_only) Reference implementation of the dev concept
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/dylan_dev/dylan_dev_cli.py` (read_only) Pattern for CLI interface implementation
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/dylan_dev/dylan_dev_runner.py` (read_only) Pattern for runner implementation
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/dylan_pr/dylan_pr_runner.py` (read_only) PR runner for GitHub PR interaction
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/provider_clis/provider_claude_code.py` (read_only) Provider interface for Claude Code
- `/Users/rasmus/Projects/claudecode-utility/dylan/cli.py` (read_only) Main CLI entry point to be updated
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/shared/ui_theme.py` (read_only) UI theme components for consistent look and feel
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/shared/interactive/utils.py` (read_only) Utilities for interactive Claude sessions
- https://typer.tiangolo.com/tutorial/ (read_only) Documentation for Typer CLI library used in the project

## Files to Implement (concept)

### Core CLI Module

1. `dylan/utility_library/dylan_fix_pr/__init__.py` - Empty init file for the package

```python
"""Dylan Fix PR module for implementing fixes from GitHub Pull Requests."""
```

2. `dylan/utility_library/dylan_fix_pr/dylan_fix_pr_cli.py` - CLI interface for the fix-pr command

```python
#!/usr/bin/env python3
"""CLI interface for the Claude Code PR fix runner using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
)
from .dylan_fix_pr_runner import generate_fix_pr_prompt, run_claude_fix_pr

console = Console()


def fix_pr(
    pr_identifier: str = typer.Argument(
        ...,
        help="GitHub PR URL or number to fix issues for",
        metavar="PR_URL_OR_NUMBER",
    ),
    branch: str | None = typer.Option(
        None,
        "--branch",
        "-b",
        help="Branch to apply fixes to (defaults to the PR branch)",
        show_default=True,
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output file path for fix report (defaults to tmp/dylan-fix-pr-report-<pr-number>.md)",
        show_default=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive mode, asking for confirmation before implementing each fix",
        show_default=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without applying them to files",
        show_default=True,
    ),
    push: bool = typer.Option(
        False,
        "--push",
        help="Push changes to the remote branch after fixes are implemented",
        show_default=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print debug information (including the full prompt)",
        show_default=True,
    ),
):
    """Implement fixes for GitHub Pull Requests using Claude Code.

    Takes a GitHub PR URL or number and implements fixes for issues
    mentioned in comments and reviews. Generates a development report
    detailing changes made.

    Examples:
        # Implement fixes from a PR URL
        dylan fix-pr https://github.com/org/repo/pull/123

        # Implement fixes from a PR number
        dylan fix-pr 123

        # Run in interactive mode
        dylan fix-pr 123 --interactive

        # Preview changes without applying them
        dylan fix-pr 123 --dry-run

        # Push changes after implementing fixes
        dylan fix-pr 123 --push
    """
    # Default values
    allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Edit", "MultiEdit", "Write", "TodoRead", "TodoWrite", "WebFetch"]
    output_format = "text"

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Fix PR"))
    console.print()

    # Show configuration
    console.print(create_box_header("Fix PR Configuration", {
        "PR Identifier": pr_identifier,
        "Branch": branch or "PR branch",
        "Output": output or "tmp/dylan-fix-pr-report-<pr-number>.md",
        "Mode": "🔍 Dry run" if dry_run else "💻 Live run",
        "Interactive": format_boolean_option(interactive, "✓ Enabled", "✗ Disabled"),
        "Push Changes": format_boolean_option(push, "✓ Enabled", "✗ Disabled"),
        "Debug": format_boolean_option(debug, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt"
    }))
    console.print()

    # Generate prompt
    prompt = generate_fix_pr_prompt(
        pr_identifier=pr_identifier,
        branch=branch,
        interactive=interactive,
        dry_run=dry_run,
        push=push,
        output_file=output,
        output_format=output_format,
    )

    # Run fix PR process
    run_claude_fix_pr(
        prompt,
        allowed_tools=allowed_tools,
        output_format=output_format,
        debug=debug,
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(fix_pr)


if __name__ == "__main__":
    main()
```

3. `dylan/utility_library/dylan_fix_pr/dylan_fix_pr_runner.py` - Core implementation of the fix-pr command

````python
#!/usr/bin/env python3
"""Core functionality for the Claude Code PR fix runner.

This module provides the functionality to fetch GitHub PR data and implement
fixes for issues identified in PR comments and reviews.

Python API usage:
    from dylan.utility_library.dylan_fix_pr.dylan_fix_pr_runner import run_claude_fix_pr, generate_fix_pr_prompt

    # Generate prompt from PR
    prompt = generate_fix_pr_prompt(pr_identifier="https://github.com/org/repo/pull/123")

    # Run fix process
    run_claude_fix_pr(prompt)
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Literal, List, Dict, Any, Optional

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.config import (
    CLAUDE_CODE_NPM_PACKAGE,
    CLAUDE_CODE_REPO_URL,
    GITHUB_ISSUES_URL,
)
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status
from ..shared.interactive.utils import run_interactive_session

console = Console()


def run_claude_fix_pr(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    debug: bool = False,
    interactive: bool = False,
) -> None:
    """Run Claude Code with a PR fix prompt and specified tools.

    Args:
        prompt: The PR fix prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Glob, Grep, LS, Bash, Write, Edit, MultiEdit)
        output_format: Output format (text, json, stream-json)
        debug: Whether to print debug information (default False)
        interactive: Whether to run in interactive mode (default False)
    """
    # Default safe tools for PR fixing
    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write", "Edit", "MultiEdit", "TodoRead", "TodoWrite"]

    # Print prompt for debugging
    if debug:
        print("\n===== DEBUG: PROMPT =====\n")
        print(prompt)
        print("\n========================\n")

    # We no longer provide a fixed output file - Claude will determine the correct filename
    # based on the PR information
    output_file = None

    # Get provider and run the process
    provider = get_provider()

    if interactive:
        # Use shared interactive session utility for consistent behavior
        result = run_interactive_session(
            provider=provider,
            prompt=prompt,
            allowed_tools=allowed_tools,
            output_format=output_format,
            context_name="Fix PR",
            console=console
        )
    else:
        # Non-interactive mode with progress display
        with create_dylan_progress(console=console) as progress:
            task = create_task_with_dylan(progress, "Dylan is implementing fixes from PR...")

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
                console.print(create_status("PR fixes implemented successfully!", "success"))
                console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory[/]")
                console.print()

                # Show a nice completion message
                console.print(f"[{COLORS['primary']}]{ARROW}[/] [bold]PR Fix Summary[/bold] [{COLORS['accent']}]{SPARK}[/]")
                console.print(f"[{COLORS['muted']}]Dylan has implemented fixes based on PR feedback and generated a detailed report.[/]")
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


def fetch_pr_data(pr_identifier: str) -> Dict[str, Any]:
    """Fetch PR data from GitHub using the gh CLI.

    Args:
        pr_identifier: PR URL or number

    Returns:
        Dictionary with PR information including title, body, comments, etc.
    """
    # Extract PR number if URL is provided
    pr_number = pr_identifier
    if pr_identifier.startswith("http"):
        # Extract PR number from URL
        match = re.search(r'/pull/(\d+)', pr_identifier)
        if match:
            pr_number = match.group(1)
        else:
            raise ValueError(f"Invalid PR URL: {pr_identifier}")

    # Create tmp directory if it doesn't exist
    os.makedirs("tmp", exist_ok=True)

    try:
        # Fetch basic PR data
        pr_view_cmd = ["gh", "pr", "view", pr_number, "--json",
                        "title,number,body,state,url,author,assignees,reviewDecision,reviewers,baseRefName,headRefName,headRepository,headRepositoryOwner,labels,commits"]
        pr_result = subprocess.run(pr_view_cmd, capture_output=True, text=True, check=True)
        pr_data = json.loads(pr_result.stdout)

        # Fetch PR comments
        comments_cmd = ["gh", "pr", "view", pr_number, "--json", "comments"]
        comments_result = subprocess.run(comments_cmd, capture_output=True, text=True, check=True)
        comments_data = json.loads(comments_result.stdout)
        pr_data['comments'] = comments_data.get('comments', [])

        # Fetch PR review comments
        reviews_cmd = ["gh", "pr", "view", pr_number, "--json", "reviews"]
        reviews_result = subprocess.run(reviews_cmd, capture_output=True, text=True, check=True)
        reviews_data = json.loads(reviews_result.stdout)
        pr_data['reviews'] = reviews_data.get('reviews', [])

        # Fetch PR checks
        checks_cmd = ["gh", "pr", "checks", pr_number, "--json", "name,status,conclusion,startedAt,completedAt,detailsUrl,output"]
        try:
            checks_result = subprocess.run(checks_cmd, capture_output=True, text=True, check=True)
            checks_data = json.loads(checks_result.stdout) if checks_result.stdout.strip() else []
            pr_data['checks'] = checks_data
        except subprocess.CalledProcessError:
            # Some PRs might not have checks
            pr_data['checks'] = []

        # Get PR diff
        diff_cmd = ["gh", "pr", "diff", pr_number]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
        pr_data['diff'] = diff_result.stdout

        return pr_data

    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR data: {e}")
        print(f"stderr: {e.stderr}")
        raise RuntimeError(f"Failed to fetch PR data: {e}")


def checkout_pr_branch(pr_number: str) -> str:
    """Checkout the PR branch locally.

    Args:
        pr_number: PR number

    Returns:
        Branch name
    """
    try:
        # Checkout PR branch
        checkout_cmd = ["gh", "pr", "checkout", pr_number]
        subprocess.run(checkout_cmd, check=True)

        # Get current branch name
        branch_cmd = ["git", "symbolic-ref", "--short", "HEAD"]
        branch_result = subprocess.run(branch_cmd, capture_output=True, text=True, check=True)
        return branch_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error checking out PR branch: {e}")
        print(f"stderr: {e.stderr}")
        raise RuntimeError(f"Failed to checkout PR branch: {e}")


def determine_report_filename(pr_number: str, output_format: str = "text") -> str:
    """Determine the correct report filename based on PR number and format.

    Args:
        pr_number: PR number
        output_format: Output format (text, json, stream-json)

    Returns:
        The determined filename
    """
    extension = ".json" if output_format == "json" else ".md"

    # Ensure tmp directory exists
    os.makedirs("tmp", exist_ok=True)

    return f"tmp/dylan-fix-pr-report-{pr_number}{extension}"


def generate_fix_pr_prompt(
    pr_identifier: str,
    branch: str | None = None,
    interactive: bool = False,
    dry_run: bool = False,
    push: bool = False,
    output_file: str | None = None,
    output_format: str = "text",
) -> str:
    """Generate a prompt to fix PR issues.

    Args:
        pr_identifier: PR URL or number
        branch: Optional branch to apply fixes to (defaults to PR branch)
        interactive: Whether to run in interactive mode
        dry_run: Whether to preview changes without applying them
        push: Whether to push changes to remote branch
        output_file: Optional custom output file path
        output_format: Output format (text, json, stream-json)

    Returns:
        The PR fix prompt string
    """
    # Extract PR number if URL is provided
    pr_number = pr_identifier
    if pr_identifier.startswith("http"):
        # Extract PR number from URL
        match = re.search(r'/pull/(\d+)', pr_identifier)
        if match:
            pr_number = match.group(1)
        else:
            raise ValueError(f"Invalid PR URL: {pr_identifier}")

    # Determine file extension based on format
    extension = ".json" if output_format == "json" else ".md"

    try:
        # Fetch PR data
        pr_data = fetch_pr_data(pr_number)

        # Checkout PR branch if not specifying a custom branch
        if branch is None:
            current_branch = checkout_pr_branch(pr_number)
        else:
            # If custom branch specified, just switch to it
            subprocess.run(["git", "checkout", branch], check=True)
            current_branch = branch
    except Exception as e:
        raise RuntimeError(f"Failed to prepare PR data: {e}")

    # Build the prompt with detailed instructions
    branching_instructions = f"""
BRANCH HANDLING:
1. You are on the branch: {current_branch}
2. This branch is for PR #{pr_number}: {pr_data['title']}
3. Ensure the tmp/ directory exists: mkdir -p tmp
"""

    file_handling_instructions = f"""
FILE HANDLING INSTRUCTIONS:
1. Create the tmp/ directory if it doesn't exist: mkdir -p tmp
2. Create a filename in this format: tmp/dylan-fix-pr-report-{pr_number}{extension}
3. If the file already exists:
   - Read the existing file to understand previous fix attempts
   - APPEND to the existing file with a clear separator
   - Add a timestamp header: ## PR Fixes [DATE] [TIME]
   - This allows tracking multiple fix attempts over time
"""

    pr_parsing_instructions = f"""
PR PARSING INSTRUCTIONS:
1. Analyze the PR data provided below
2. Identify issues that need fixing:
   - Look for review comments that suggest changes
   - Check for failed CI checks
   - Look for issues mentioned in PR description
3. Create a plan to implement fixes for each identified issue
4. Don't just focus on the PR description - the most critical feedback is usually in the review comments
"""

    implementation_instructions = f"""
IMPLEMENTATION INSTRUCTIONS:
1. For each issue to fix:
   - Review the issue details
   - Create a plan for implementing the fix
   - {"Show the plan and ask for confirmation before proceeding" if interactive else "Proceed with the implementation"}
   - {"Explain what changes would be made without modifying files" if dry_run else "Make the necessary changes to fix the issue"}
   - Run tests if available to verify the fix works
   - Document what was done and why
2. After all fixes are implemented:
   - Run linting and type checking if available
   - Verify all tests pass
   - Document any issues that couldn't be fixed
   - {"Push changes to remote branch if successful" if push else "Don't push changes to remote branch"}
"""

    formatting_instructions = f"""
REPORT FORMATTING INSTRUCTIONS:
1. Generate a detailed PR fix report with:
   - Summary of what was fixed
   - List of issues fixed with reference to review comments
   - For each issue:
     - Description from PR comment
     - Files modified
     - Changes made
     - Test results
   - List of issues not fixed (if any) and why
   - Next steps or recommendations
2. Save the report to: tmp/dylan-fix-pr-report-{pr_number}{extension}
3. Display a summary of the changes made
"""

    # Format PR data as a JSON string with pretty printing
    pr_data_formatted = json.dumps(pr_data, indent=2)

    return f"""
Implement fixes for issues identified in GitHub Pull Request #{pr_number}.

{branching_instructions}

{file_handling_instructions}

{pr_parsing_instructions}

{implementation_instructions}

{formatting_instructions}

INPUT PARAMETERS:
- PR Number: {pr_number}
- Branch: {branch or current_branch}
- Mode: {"Dry run (preview only)" if dry_run else "Live run (apply changes)"}
- Interactive: {"Yes" if interactive else "No"}
- Push Changes: {"Yes" if push else "No"}
- Custom output file: {output_file or "None (use default)"}

PR DATA:
```json
{pr_data_formatted}
```

IMPLEMENTATION APPROACH:

1. Analyze the PR data to identify issues from comments and checks
2. Create a plan for fixing each identified issue
3. {"Preview changes without applying them" if dry_run else "Implement fixes one by one"}
4. Generate a detailed report of what was done
5. {"Push changes to remote if all fixes are implemented successfully" if push else "Keep changes local"}

**IMPORTANT INSTRUCTIONS:**

- Always ensure code changes follow the existing patterns and styles
- {"Do not modify any files, only show what would be changed" if dry_run else "Apply changes carefully, preserving code style and formatting"}
- Include a "Steps Executed" section listing all commands and decisions you made
- Use the exact filename format: tmp/dylan-fix-pr-report-{pr_number}{extension}
- If you encounter any errors, document them clearly in the report
- Focus primarily on the review comments and failed checks as these typically contain the most important issues
  """

if **name** == "**main**": # Example usage
prompt = generate_fix_pr_prompt(pr_identifier="123")
run_claude_fix_pr(prompt)

```

### CLI Entry Point Update

4. `dylan/cli.py` - Updated to add the fix-pr command

```python
"""Root Typer application that dispatches to vertical slices.

Includes 'standup', 'review', 'dev', 'fix-pr', 'pr', and 'release' commands.
"""

import typer
from rich.console import Console
from rich.table import Table

from .utility_library.dylan_dev.dylan_dev_cli import dev
from .utility_library.dylan_fix_pr.dylan_fix_pr_cli import fix_pr
from .utility_library.dylan_pr.dylan_pr_cli import pr
from .utility_library.dylan_release.dylan_release_cli import release_app
from .utility_library.dylan_review.dylan_review_cli import review
from .utility_library.dylan_standup.standup_typer import standup_app
from .utility_library.shared.ui_theme import ARROW, COLORS, SPARK

console = Console()

app = typer.Typer(
    help=f"[{COLORS['primary']}]Dylan[/] [{COLORS['accent']}]{SPARK}[/] AI-powered development utilities",
    add_completion=False,
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)
app.add_typer(standup_app, name="standup", help="Generate daily standup reports from git activity")
app.add_typer(release_app, name="release", help="Create and manage project releases")
app.command(name="review", help="Run AI-powered code reviews on git branches")(review)
app.command(name="dev", help="Implement fixes from code reviews")(dev)
app.command(name="fix-pr", help="Implement fixes from GitHub Pull Requests")(fix_pr)
app.command(name="pr", help="Create pull requests with AI-generated descriptions")(pr)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    """Show welcome message when no command is provided."""
    if ctx.invoked_subcommand is None:
        # Welcome header with flair
        console.print(f"\n[{COLORS['primary']}]{ARROW}[/] [bold]Dylan[/bold] [{COLORS['accent']}]{SPARK}[/]")
        console.print("[dim]AI-powered development utilities using Claude Code[/dim]\n")

        # Commands table with custom styling
        table = Table(
            show_header=True,
            header_style=f"bold {COLORS['primary']}",
            border_style=COLORS['muted'],
            title_style=f"bold {COLORS['accent']}",
            box=None,
        )

        table.add_column("Command", style=COLORS['secondary'], width=12)
        table.add_column("Description", style=COLORS['primary'])
        table.add_column("Example", style="dim")

        table.add_row(
            "standup",
            "Generate daily standup reports",
            "dylan standup --since yesterday"
        )
        table.add_row(
            "review",
            "Run code reviews on branches",
            "dylan review feature-branch"
        )
        table.add_row(
            "dev",
            "Implement fixes from reviews",
            "dylan dev tmp/review.md"
        )
        table.add_row(
            "fix-pr",
            "Implement fixes from PRs",
            "dylan fix-pr 123"
        )
        table.add_row(
            "pr",
            "Create pull requests",
            "dylan pr --target develop"
        )
        table.add_row(
            "release",
            "Manage project releases",
            "dylan release --minor --tag"
        )

        console.print(table)
        help_text = f"\n[{COLORS['muted']}]Use[/] [{COLORS['primary']}]dylan <command> --help[/]"
        console.print(f"{help_text} [{COLORS['muted']}]for detailed options[/]")
        console.print("[dim]Example: dylan review --help[/dim]\n")
````

## Implementation Notes

### CLI Integration

- The implementation follows the same pattern as the existing `dev`, `review`, and `pr` commands
- Creates a completely separate module (`dylan_fix_pr`)
- Uses GitHub CLI (`gh`) through prompt instructions to fetch PR data and manage PR branches
- Leverages the shared interactive mode utilities for consistent behavior

### PR Data Handling

- Fetches complete PR data including comments, reviews, and checks
- Provides the raw PR data to Claude for analysis
- Allows Claude to identify issues from review comments and failed checks

### Implementation Process

- Structured approach for fixing PR issues:
  1. Fetch and analyze PR data
  2. Checkout PR branch (or use specified branch)
  3. Identify issues from PR feedback
  4. Implement fixes for issues
  5. Generate a development report
  6. Optionally push changes to remote

### Safety Measures

- Provides dry-run mode to preview changes
- Interactive mode for confirmation of changes
- Push flag must be explicitly set to push changes to remote
- Detailed error handling and user feedback
- Branch handling respects user-specified branch

## Validation Gates

1. **Functionality Requirements**

   - The command must be accessible via `dylan fix-pr <pr-identifier>`
   - The command must fetch PR data correctly
   - The command must identify issues from PR feedback
   - The command must implement fixes for issues
   - The command must generate a development report
   - The command must support all specified options

2. **Integration Requirements**

   - The command must integrate with the existing Dylan CLI
   - The command must follow the same UI patterns as other commands
   - The command must use the provider interface for Claude Code

3. **Quality Requirements**

   - All code must pass linting and type checking
   - All code must have appropriate error handling
   - All code must follow the project's coding standards
   - The command must provide clear feedback to the user

4. **Testing Requirements**
   - Basic unit tests for core functionality

## Implementation Steps/Testing

1. Implementation of the minimal functionality

   - Instruct Claude by prompt to fetch PR data
   - Test with various PR URLs and numbers
   - Verify data fetching works correctly

2. Implement the fix-pr runner

   - Implement core fix functionality
   - Test with simple PRs first
   - Extend to handle more complex PR feedback
