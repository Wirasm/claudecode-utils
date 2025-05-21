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
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_release(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    debug: bool = False,
    interactive: bool = False,
) -> None:
    """Run Claude code with a release prompt and specified tools.

    Args:
        prompt: The release prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Write, Edit, Bash, LS, Glob)
        output_format: Output format (text, json, stream-json)
        debug: Whether to print debug information (default False)
        interactive: Whether to run in interactive mode (default False)
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
            context_name="release",
            console=console
        )
    else:
        # Non-interactive mode - use progress display and existing output handling
        with create_dylan_progress(console=console) as progress:
            task = create_task_with_dylan(progress, "Dylan is creating your release...")
            try:
                result = provider.generate(
                    prompt,
                    output_path=output_file, # output_file is None, provider handles filename
                    allowed_tools=allowed_tools,
                    output_format=output_format,
                    interactive=False # Explicitly false
                )
                progress.update(task, completed=True)
                console.print()
                console.print(create_status("Release process completed successfully!", "success"))
                console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory[/]")
                console.print(f"[{COLORS['muted']}]Format: dylan-release-v<version>-from-<branch>.md (or .json)[/]")
                console.print()
                message = f"[{COLORS['primary']}]{ARROW}[/] [bold]Release Summary[/bold] [{COLORS['accent']}]{SPARK}[/]"
                console.print(message)
                console.print(f"[{COLORS['muted']}]Dylan has prepared your release and updated version information.[/]")
                console.print()
                if result and "Mock" not in result and "Authentication Error" not in result:
                    console.print(result) # Display the report content
                elif "Authentication Error" in result:
                    # The auth error from the provider is already well-formatted Markdown.
                    console.print(result)

            except RuntimeError as e: # Catch errors from provider.generate()
                progress.update(task, completed=True)
                console.print()
                console.print(create_status(str(e), "error"))
                sys.exit(1)
            except FileNotFoundError: # Should be caught by provider
                progress.update(task, completed=True)
                console.print()
                console.print(create_status("Claude Code not found!", "error"))
                sys.exit(1)
            except Exception as e: # Catch any other unexpected errors
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
1. Set CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
2. Check if user is on develop branch (or equivalent release branch):
   - Check for .branchingstrategy file to determine RELEASE_BRANCH
   - If found, parse release_branch (typically: 'develop')
   - If no .branchingstrategy file, set RELEASE_BRANCH='develop'
3. CRITICAL: If NOT on release branch, exit with clear error:
   - "ERROR: Please switch to $RELEASE_BRANCH branch before creating a release"
   - "Current branch: $CURRENT_BRANCH - Expected: $RELEASE_BRANCH"
   - Explain that releases must always start from the release branch
   - Exit with non-zero status (exit 1)
4. If on correct branch, proceed with release
5. REQUIRED: Report both the current branch and release branch in the metadata
"""

    file_handling_instructions = f"""
FILE HANDLING INSTRUCTIONS:
1. Create the tmp/ directory if it doesn't exist: mkdir -p tmp
2. Determine the current version from VERSION DETECTION section and set CURRENT_VERSION
3. Calculate the next version based on bump type and set NEW_VERSION
4. Create sanitized branch name:
   - CURRENT_BRANCH_SANITIZED=$(echo $CURRENT_BRANCH | sed 's/\\//-/g')
5. Create a filename in this format: tmp/dylan-release-v$NEW_VERSION-from-$CURRENT_BRANCH_SANITIZED{extension}
   - Example: tmp/dylan-release-v1.2.3-from-develop.md
   - DO NOT add timestamps to the filename itself
6. If the file already exists:
   - Read the existing file to understand previous release attempts
   - APPEND to the existing file with a clear separator
   - Add a timestamp header: ## Release Attempt [YYYY-MM-DD HH:MM:SS]
   - This allows tracking multiple release attempts over time
"""

    version_bump_instructions = f"""
VERSION DETECTION AND BUMP:
1. Detect current version by searching in this order:
   - First, check pyproject.toml for version = "X.Y.Z" or version = 'X.Y.Z'
   - If not found, check package.json for "version": "X.Y.Z"
   - If not found, check Cargo.toml for version = "X.Y.Z"
   - If not found, check version.txt (simple file with just the version)
   - Extract current version in semantic version format (X.Y.Z)
   - Set CURRENT_VERSION to this value
   - CRITICAL: Report which file contains the version and what line/pattern was matched

2. Validate current version:
   - Ensure it matches semantic versioning format (X.Y.Z)
   - If invalid, exit with error message and non-zero status

3. Calculate new version:
   - {bump_type.capitalize()} bump: {
        "increment Z (PATCH version)"
        if bump_type == "patch"
        else "increment Y, reset Z to 0 (MINOR version)"
        if bump_type == "minor"
        else "increment X, reset Y and Z to 0 (MAJOR version)"
    }
   - Set NEW_VERSION to this calculated value
   - Validate that NEW_VERSION follows semantic versioning format

4. Update version file:
   - Use Edit or MultiEdit tool to update the version precisely
   - Preserve all file formatting, indentation, and quotes
   - Confirm the change was made successfully by re-reading the file
   {"- PREVIEW changes only (don't actually apply)" if dry_run else ""}
   - CRITICAL: Report the exact file path that was modified and show before/after
"""

    changelog_instructions = """
CHANGELOG MANAGEMENT:
1. Look for changelog file in this order:
   - CHANGELOG.md (most common)
   - HISTORY.md
   - NEWS.md
   - If not found, report clearly in the Steps Executed section

2. Analyze commit history and PR descriptions to generate changelog entries:
   - Use `git log $RELEASE_BRANCH..HEAD --pretty=format:'%h %s'` to get all commits
   - Categorize commits based on conventional commit prefixes:
     * feat: → Added (new features)
     * fix: → Fixed (bug fixes)
     * docs: → Documentation (documentation only changes)
     * style: → Changed (code style, formatting)
     * refactor: → Changed (code refactoring, no functional change)
     * perf: → Changed (performance improvements)
     * test: → Changed (adding or refactoring tests)
     * build: → Changed (build system, dependencies)
     * ci: → Changed (CI configuration)
     * chore: → Changed (maintenance tasks)
   - Check for merged PRs: `gh pr list --state merged --base $RELEASE_BRANCH`
   - For each PR, analyze its title and description for additional information
   - IMPORTANT: Focus on commit messages and PR descriptions, NOT code changes
   - Format each entry as a bullet point with a brief description
   - Group entries by type (Added, Changed, Fixed, etc.)

3. When changelog is found:
   - Read the entire file to understand the structure
   - Verify it follows the Keep a Changelog format (https://keepachangelog.com)
   - Look for [Unreleased] section (must be at the top)
   - If [Unreleased] section doesn't exist, create one
   - If [Unreleased] section exists but is empty, populate it with entries from step 2
   - If [Unreleased] section has content, verify it matches your analysis from step 2
     * If there are discrepancies, report them but PREFER the existing content
     * Only add missing entries from your analysis that aren't already there

4. Create new version section:
   - Format: ## [NEW_VERSION] - YYYY-MM-DD (today's date)
   - Position: immediately after [Unreleased] section
   - Move all content from [Unreleased] to the new section
   - Keep empty [Unreleased] section at the top for future changes
   - Example structure:
     ```
     ## [Unreleased]

     ## [1.2.3] - 2023-04-01
     ### Added
     - New feature description

     ### Fixed
     - Bug fix description
     ```

5. Use the MultiEdit tool for this change to ensure atomic updates:
   - First edit: create the new version section header
   - Second edit: move content from Unreleased to new section
   - Third edit: ensure Unreleased section remains (empty if needed)

6. Verify changes:
   - Re-read the changelog file to confirm structure is correct
   - CRITICAL: Report the exact changes made to the changelog, showing before and after
   - Include the complete list of commits and PRs that were analyzed
"""

    git_instructions = (
        ""
        if no_git
        else f"""
GIT OPERATIONS:
1. Check git status to see which files were modified:
   - git status (should show version file and changelog changes)
   - Verify these are the ONLY files changed before committing

2. Commit the version and changelog changes:
   - git add -v [version-file] [changelog-file]
   - Commit with message: "release: version v$NEW_VERSION"
   - CRITICAL: Show the commit hash and message for verification

3. Tag creation: {
       "Create an annotated tag:\n   - git tag -a v$NEW_VERSION -m 'Version $NEW_VERSION'\n   - Verify tag exists: git tag -l 'v$NEW_VERSION'"
       if create_tag
       else "Skip tag creation (--tag flag not specified)"
   }

4. Apply merge strategy ({merge_strategy}):
{
    (
        "   - Push changes to $RELEASE_BRANCH: git push origin $RELEASE_BRANCH\n"
        + "   - Ensure push succeeded by checking remote status\n"
        + "   - Checkout main branch: git checkout main\n"
        + "   - Pull latest main: git pull origin main\n"
        + "   - Merge $RELEASE_BRANCH into main: git merge $RELEASE_BRANCH\n"
        + "   - Push main branch: git push origin main\n"
        + (
            "   - Push tags to remote: git push origin --tags\n"
            if create_tag
            else ""
        )
        + "   - Return to $RELEASE_BRANCH: git checkout $RELEASE_BRANCH"
    )
    if merge_strategy == "direct"
    else (
        "   - Push changes to $RELEASE_BRANCH: git push origin $RELEASE_BRANCH\n"
        + "   - Create PR from $RELEASE_BRANCH to main using GitHub CLI:\n"
        + "   - gh pr create --base main --head $RELEASE_BRANCH --title \"Release v$NEW_VERSION\" --body \"Release version $NEW_VERSION\"\n"
        + "   - Report PR URL in the output"
    )
}

5. Run git status one final time to verify clean state
6. Report all commands executed, their output, and any errors encountered
"""
    )

    dry_run_note = "**DRY RUN MODE: Show what would be done but don't make actual changes**\n\n" if dry_run else ""

    return f"""
You are a release manager with COMPLETE AUTONOMY to create project releases from the release branch (develop) to main.

{dry_run_note}YOUR MISSION:
1. Verify user is on the correct release branch (typically develop)
2. Apply {bump_type} version bump ({bump_type.upper()}: {
        "increment patch Z in X.Y.Z"
        if bump_type == "patch"
        else "increment minor Y and reset patch Z in X.Y.Z"
        if bump_type == "minor"
        else "increment major X and reset minor Y and patch Z in X.Y.Z"
    })
3. Update changelog by adding a new version section and preserving the [Unreleased] section
4. Create release commit with appropriate message and optionally create an annotated git tag
5. Apply the selected merge strategy ({merge_strategy}): {'merge to main branch' if merge_strategy == 'direct' else 'create PR to main branch'}
6. Document all steps in a comprehensive report with detailed "Steps Executed" section

{branch_check_instructions}

{file_handling_instructions}

{version_bump_instructions}

{changelog_instructions}

{git_instructions if not no_git else ''}

REPORT GENERATION:
1. Document all actions taken or planned (if dry run) with a clear structure:
   - Initial conditions (branch, version file, changelog)
   - Version changes (from CURRENT_VERSION to NEW_VERSION)
   - List all files modified with exact changes
   - Git operations performed (commits, tags, merges)
   - Include any error messages or warnings encountered

2. REQUIRED: Add a "Steps Executed" section that lists ALL steps performed:
   - All bash commands used with their complete output
   - Key decisions made during the process (e.g., which files were modified)
   - Document any issues encountered
   - Include timestamps for major steps

3. REQUIRED: Add "Release Status" section with clear summary:
   - Whether release was successful or failed
   - New version created
   - Files modified
   - Git operations status (commit, tag, merge/PR)
   - Next steps or recommendations

4. Format the report with clear section headers using markdown:
   ```
   ## Release Summary
   Brief overview of what was done

   ## Version Information
   - Current version: X.Y.Z
   - New version: A.B.C
   - Bump type: patch|minor|major

   ## Files Modified
   - /path/to/version/file
   - /path/to/changelog

   ## Git Operations
   - Commit: [hash]
   - Tag: vA.B.C (if created)
   - Branch: develop → main (direct or PR)

   ## Steps Executed
   Detailed list of commands and decisions

   ## Release Status
   Final status and next steps
   ```

5. Save report to: tmp/dylan-release-v$NEW_VERSION-from-$CURRENT_BRANCH_SANITIZED{extension} with timestamp header

REMEMBER:
- Releases MUST always start from the release branch (typically develop)
- Follow semantic versioning strictly (X.Y.Z format)
- Follow Keep a Changelog format (https://keepachangelog.com)
- Provide clear error messages if prerequisites aren't met
- Always APPEND to existing reports with clear timestamps, DO NOT create new files
- Always include both a "Steps Executed" section and a "Release Status" section
- Save reports with the exact filename format specified above, NO timestamps in filenames
- Document ALL commands executed and their output
{"- This is a DRY RUN - show changes but do not apply them" if dry_run else ""}
- Include specific information about which files were modified and how

Execute the complete release workflow now and save your report.
"""


if __name__ == "__main__":
    # Example usage
    prompt = generate_release_prompt(bump_type="minor", create_tag=True)
    run_claude_release(prompt)
