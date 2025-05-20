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
from ..shared.exit_command import DEFAULT_EXIT_COMMAND, show_exit_command_message
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_release(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    stream: bool = False,
    debug: bool = False,
) -> None:
    """Run Claude code with a release prompt and specified tools.

    Args:
        prompt: The release prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Write, Edit, Bash, LS, Glob)
        output_format: Output format (text, json, stream-json)
        stream: Whether to stream output (default False)
        debug: Whether to print debug information (default False)
    """
    # Default safe tools for release
    if allowed_tools is None:
        allowed_tools = ["Read", "Write", "Edit", "Bash", "LS", "Glob", "MultiEdit", "TodoRead", "TodoWrite"]

    # Print prompt for debugging
    if debug:
        print("\n===== DEBUG: PROMPT =====\n")
        print(prompt)
        print("\n========================\n")

    # We no longer provide a fixed output file - Claude will determine the correct filename
    # based on version and branch information using the format:
    # tmp/dylan-release-vX.Y.Z-from-[branch].<extension>
    output_file = None

    # Get provider and run the release
    provider = get_provider()

    # Always show exit command message, but let the handler thread show its own prompt
    if stream:
        # For streaming mode, still show the prominent message
        show_exit_command_message(
            console,
            DEFAULT_EXIT_COMMAND,
            style="prominent"
        )

    with create_dylan_progress(console=console) as progress:
        # Start the release task
        task = create_task_with_dylan(progress, "Dylan is creating your release...")

        try:
            result = provider.generate(
                prompt,
                output_path=output_file,
                allowed_tools=allowed_tools,
                output_format=output_format,
                stream=stream,
                exit_command=DEFAULT_EXIT_COMMAND if stream else None
            )
            # Update task to complete
            progress.update(task, completed=True)

            # Success message with flair
            console.print()
            console.print(create_status("Release created successfully!", "success"))
            console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory[/]")
            console.print(f"[{COLORS['muted']}]Format: dylan-release-v<version>-from-<branch>.md[/]")
            console.print()

            # Show a nice completion message
            message = f"[{COLORS['primary']}]{ARROW}[/] [bold]Release Summary[/bold] [{COLORS['accent']}]{SPARK}[/]"
            console.print(message)
            console.print(f"[{COLORS['muted']}]Dylan has prepared your release and updated version information.[/]")
            console.print()

            if result and "Mock" not in result:  # Don't show mock results
                console.print(result)
        except Exception as e:
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(f"Error running release: {e}", "error"))
            sys.exit(1)


def generate_release_prompt(
    bump_type: Literal["patch", "minor", "major"] = "patch",
    create_tag: bool = False,
    dry_run: bool = False,
    no_git: bool = False,
    merge_strategy: str = "direct",
    output_format: str = "text",
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
    
    branch_check_instructions = """
BRANCH VERIFICATION:
1. First, determine the current branch: git symbolic-ref --short HEAD
2. Check if user is on develop branch (or equivalent release branch):
   - Check for .branchingstrategy file to determine release_branch
   - If no .branchingstrategy file, assume 'develop' is the release branch
3. CRITICAL: If NOT on release branch (develop), exit with clear error:
   - "ERROR: Please switch to develop branch before creating a release"
   - "Current branch: [current] - Expected: develop"
   - Exit with non-zero status
4. If on correct branch, proceed with release
"""

    file_handling_instructions = f"""
FILE HANDLING INSTRUCTIONS:
1. Create the tmp/ directory if it doesn't exist: mkdir -p tmp  
2. Determine the current version from VERSION DETECTION section
3. Calculate the next version based on bump type
4. Create a filename in this format: tmp/dylan-release-vX.Y.Z-from-[branch]{extension}
   - Replace any slashes in branch names with hyphens
   - Include the new version number in the filename
5. If the file already exists, APPEND your new release report with a clear separator
   - Add a timestamp header: ## Release [DATE] [TIME]
   - This allows tracking multiple release attempts over time
"""

    version_bump_instructions = f"""
VERSION BUMP INSTRUCTIONS:
1. Detect current version:
   - Look for version in: pyproject.toml, package.json, Cargo.toml, version.txt
   - Extract current version (X.Y.Z format)
   - Report which file contains the version
   
2. Calculate new version:
   - {bump_type.capitalize()} bump: {
        "increment Z"
        if bump_type == "patch"
        else "increment Y, reset Z to 0"
        if bump_type == "minor"
        else "increment X, reset Y and Z to 0"
    }
   - Validate new version format (must be X.Y.Z)
   
3. Update version file:
   - Use Edit tool to update the version precisely
   - Preserve file formatting and indentation
   {"- PREVIEW changes only (don't actually apply)" if dry_run else ""}
"""

    changelog_instructions = """
CHANGELOG INSTRUCTIONS:
1. Look for changelog in this order:
   - CHANGELOG.md
   - HISTORY.md
   - NEWS.md
2. Parse the file to find [Unreleased] section
3. Create new version section with date:
   - Format: [X.Y.Z] - YYYY-MM-DD
4. Move all content from [Unreleased] to new section
5. Keep empty [Unreleased] header for future changes
6. Use MultiEdit or Edit tool for this change
"""

    git_instructions = (
        ""
        if no_git
        else f"""
GIT OPERATIONS:
1. Commit the version and changelog changes:
   - git add the changed files
   - Commit with message: "release: version vX.Y.Z"
   
2. Create tag if requested:
   {"- Create an annotated tag: git tag -a vX.Y.Z -m 'Version X.Y.Z'" if create_tag else "- Skip tag creation"}
   
3. Apply merge strategy ({merge_strategy}):
   {
       "- Push changes to develop branch" + "\n"
       + "- Merge develop into main: git checkout main && git merge develop" + "\n"
       + "- Push main branch and tags" + "\n"
       + "- Return to develop branch: git checkout develop"
       if merge_strategy == "direct"
       else "- Push changes to develop branch" + "\n"
       + "- Create PR from develop to main: gh pr create --base main --head develop" + "\n"
       + "- Report PR URL in output"
   }
   
4. Report final git status
"""
    )

    dry_run_note = "**DRY RUN MODE: Show what would be done but don't make actual changes**\n\n" if dry_run else ""

    return f"""
You are a release manager with COMPLETE AUTONOMY to create project releases from develop to main.

{dry_run_note}YOUR MISSION:
1. Verify user is on the develop branch (or equivalent release branch)
2. Apply {bump_type} version bump on the develop branch
3. Update changelog with the new version
4. Create release commit and optionally tag
5. Merge or PR from develop to main branch

{branch_check_instructions}

{file_handling_instructions}

{version_bump_instructions}

{changelog_instructions}

{git_instructions if not no_git else ''}

REPORT GENERATION:
1. Document all actions taken or planned (if dry run)
2. Show before/after versions
3. List all files modified
4. Include any error messages or warnings
5. Save report to: tmp/dylan-release-vX.Y.Z-from-[branch]{extension}

REMEMBER:
- Releases must always start from develop branch
- Follow semantic versioning strictly
- Follow Keep a Changelog format
- Provide clear error messages if prerequisites aren't met
{"- This is a DRY RUN - show changes but do not apply them" if dry_run else ""}

Execute the complete release workflow now and save your report.
"""


if __name__ == "__main__":
    # Example usage
    prompt = generate_release_prompt(bump_type="minor", create_tag=True)
    run_claude_release(prompt)
