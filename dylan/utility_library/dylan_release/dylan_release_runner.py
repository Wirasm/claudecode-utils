#!/usr/bin/env python3
"""Simple Claude Code release runner.

Builds on the minimal philosophy of dylan utilities.

This module provides the core release functionality. For CLI usage, use dylan_release_cli.py

Python API usage:
    from dylan.utility_library.dylan_release.dylan_release_runner import run_claude_release, generate_release_prompt

    # Create a patch release
    prompt = generate_release_prompt(bump_type="patch")
    run_claude_release(prompt)

    # Create a minor release with tag
    prompt = generate_release_prompt(bump_type="minor", create_tag=True)
    run_claude_release(prompt, allowed_tools=["Bash", "Read", "Write", "Edit"])
"""

import sys
from typing import Literal

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.progress import create_dylan_progress, create_task_with_dylan


def run_claude_release(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
) -> None:
    """Run Claude code with a release prompt and specified tools.

    Args:
        prompt: The release prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Write, Edit, Bash)
        output_format: Output format (text, json, stream-json)
    """
    # Default safe tools for release
    if allowed_tools is None:
        allowed_tools = ["Read", "Write", "Edit", "Bash", "LS", "Glob"]

    # Determine output file based on format - always in tmp directory
    output_file = "tmp/release_report.json" if output_format == "json" else "tmp/release_report.md"

    console = Console()

    # Create progress bar
    with create_dylan_progress(console) as progress:
        task = create_task_with_dylan(progress, "Creating release...")

        # Get provider and run the release
        provider = get_provider()
        try:
            result = provider.generate(
                prompt,
                output_path=output_file,
                allowed_tools=allowed_tools,
                output_format=output_format
            )
            progress.update(task, completed=True)
            console.print("\n✅ Release process completed successfully")
            console.print(f"📝 Report saved to: {output_file}")
            if result:
                console.print(result)
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n❌ Error running release: {e}")
            sys.exit(1)


def generate_release_prompt(
    bump_type: Literal["patch", "minor", "major"] = "patch",
    create_tag: bool = False,
    dry_run: bool = False,
    no_git: bool = False,
    merge_strategy: str = "direct",
    output_format: str = "text"
) -> str:
    """Generate a release prompt.

    Args:
        bump_type: Type of version bump (patch, minor, major)
        create_tag: Whether to create a git tag
        dry_run: Preview changes without applying
        no_git: Skip git operations
        merge_strategy: Merge strategy for releases (direct, pr)
        output_format: Output format (text, json, stream-json)

    Returns:
        The release prompt string
    """
    extension = ".json" if output_format == "json" else ".md"

    git_instructions = "" if no_git else f"""
5. GIT OPERATIONS:
   - Create commit: "release: version X.Y.Z"
   {'- Create git tag: v{new_version}' if create_tag else '- Skip tag creation'}
6. MERGE STRATEGY ({merge_strategy}):
   {"- If on release branch (e.g., develop):" + '\n' +
    "  * Commit changes on release branch" + '\n' +
    "  * Push release branch" + '\n' +
    "  * Merge release branch to production branch (main)" + '\n' +
    "  * Tag on production branch if requested" + '\n' +
    "  * Push production branch and tags" + '\n' +
    "- If already on production branch (main):" + '\n' +
    "  * Create tag if requested" + '\n' +
    "  * Push branch and tags"
    if merge_strategy == "direct" else
    "- If on release branch (e.g., develop):" + '\n' +
    "  * Commit changes on release branch" + '\n' +
    "  * Push release branch" + '\n' +
    "  * Create a pull request from release branch to production branch" + '\n' +
    "  * Report PR URL"}
   - Report git status after operations
"""

    dry_run_note = "**DRY RUN MODE: Show what would be done but don't make actual changes**\n\n" if dry_run else ""

    return f"""
You are a release manager with COMPLETE AUTONOMY to create project releases.

{dry_run_note}YOUR MISSION:
1. Detect current branch and branching strategy
2. Apply {bump_type} version bump on the appropriate release branch
3. Update changelog appropriately
4. Create release commit and optionally tag
5. Handle merging based on merge strategy: {merge_strategy}

IMPORTANT FILE HANDLING INSTRUCTIONS:
- Save your report to the tmp/ directory
- If tmp/release_report{extension} already exists, create a new file with timestamp
- Format: tmp/release_report_YYYYMMDD_HHMMSS{extension}
- Use the Bash tool to check if the file exists first
- DO NOT modify or append to existing files

CRITICAL STEPS - Use Bash and other tools to:

1. BRANCH DETECTION AND STRATEGY:
   - Detect current branch: git symbolic-ref --short HEAD
   - Check for .branchingstrategy file and parse it if exists
   - If on 'main' and .branchingstrategy exists:
     * Read release_branch from .branchingstrategy file
     * Switch to the release branch (e.g., develop)
   - If no .branchingstrategy file, check for common release branches:
     * develop, development, staging, release
     * If found, use the first matching branch as release branch
   - If no strategy found, proceed on current branch

2. VERSION DETECTION:
   - Look for version in this order:
     a. pyproject.toml (version = "X.Y.Z")
     b. package.json ("version": "X.Y.Z")
     c. Cargo.toml (version = "X.Y.Z")
     d. version.txt or VERSION (just X.Y.Z)
   - Extract current version using appropriate method
   - Report which file contains the version

3. VERSION CALCULATION:
   - Current version: X.Y.Z
   - {bump_type.capitalize()} bump: {
        'increment Z' if bump_type == 'patch' else
        'increment Y, reset Z to 0' if bump_type == 'minor' else
        'increment X, reset Y and Z to 0'
    }
   - Calculate new version accordingly
   - Validate version format (must be X.Y.Z)

3. VERSION UPDATE:
   - Update version in the detected file
   - Preserve file formatting and structure
   - Use Edit tool for precise updates
   {'- PREVIEW changes only' if dry_run else ''}

4. CHANGELOG UPDATE:
   - Look for changelog in this order:
     a. CHANGELOG.md
     b. HISTORY.md
     c. NEWS.md
   - Find [Unreleased] section
   - Create new section: [X.Y.Z] - YYYY-MM-DD
   - Move all [Unreleased] content to new section
   - Keep [Unreleased] header for future changes
   {'- PREVIEW changes only' if dry_run else ''}

{git_instructions if not no_git else ''}

7. REPORT GENERATION:
   - Document all actions taken
   - Show before/after versions
   - List files modified
   - Include any error messages
   - Save to appropriate filename in tmp/

REMEMBER:
- Be completely autonomous
- Work with any project structure
- Use standard version formats (X.Y.Z)
- Follow Keep a Changelog format
- Report everything clearly
{'- This is a DRY RUN - show changes but do not apply them' if dry_run else ''}

Execute the complete release workflow now and save your report.
"""


if __name__ == "__main__":
    # Example usage
    prompt = generate_release_prompt(bump_type="minor", create_tag=True)
    run_claude_release(prompt)
