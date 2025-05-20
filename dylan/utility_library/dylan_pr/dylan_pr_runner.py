#!/usr/bin/env python3
"""Simple Claude Code PR creator runner.

Builds on concept_library/simple_pr concepts but starts minimal.

This module provides the core PR creation functionality. For CLI usage, use dylan_pr_cli.py

Python API usage:
    from dylan.utility_library.dylan_pr.dylan_pr_runner import run_claude_pr, generate_pr_prompt

    # Create PR for current branch
    prompt = generate_pr_prompt()
    run_claude_pr(prompt)

    # Create PR for specific branch with custom target
    prompt = generate_pr_prompt(branch="feature-branch", target_branch="develop")
    run_claude_pr(prompt, allowed_tools=["Bash", "Read", "Write"], output_format="json")
"""

import sys
from typing import Literal

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.config import CLAUDE_CODE_NPM_PACKAGE, CLAUDE_CODE_REPO_URL, GITHUB_ISSUES_URL
from ..shared.exit_command import DEFAULT_EXIT_COMMAND, show_exit_command_message
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_pr(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
    stream: bool = False,
    debug: bool = False,
) -> None:
    """Run Claude code with a PR creation prompt and specified tools.

    Args:
        prompt: The PR creation prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Bash, Write)
        output_format: Output format (text, json, stream-json)
        stream: Whether to stream output (default False)
        debug: Whether to print debug information (default False)
    """
    # Default safe tools for PR creation
    if allowed_tools is None:
        allowed_tools = ["Read", "Bash", "Write", "Glob", "Grep", "TodoRead", "TodoWrite"]

    # Print prompt for debugging
    if debug:
        print("\n===== DEBUG: PROMPT =====\n")
        print(prompt)
        print("\n========================\n")

    # We no longer provide a fixed output file - Claude will determine the correct filename
    # based on the current branch and target branch using the format:
    # tmp/dylan-pr-[current-branch]-to-[target].<extension>
    output_file = None

    # Get provider and run the PR creation
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
        # Start the PR task
        task = create_task_with_dylan(progress, "Dylan is creating your pull request...")

        try:
            result = provider.generate(
                prompt,
                output_path=output_file,
                allowed_tools=allowed_tools,
                output_format=output_format,
                stream=stream,
                exit_command=DEFAULT_EXIT_COMMAND
            )

            # Update task to complete
            progress.update(task, completed=True)

            # Success message with flair
            console.print()
            console.print(create_status("Pull request created successfully!", "success"))
            console.print(f"[{COLORS['muted']}]Report saved to tmp/ directory with format:[/]")
            console.print(f"[{COLORS['muted']}]dylan-pr-[current-branch]-to-[target].md[/]")
            console.print()

            # Show a nice completion message
            console.print(f"[{COLORS['primary']}]{ARROW}[/] [bold]PR Summary[/bold] [{COLORS['accent']}]{SPARK}[/]")
            console.print(f"[{COLORS['muted']}]Dylan has analyzed your commits and created a PR description.[/]")
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


def generate_pr_prompt(
    branch: str | None = None,
    target_branch: str = "develop",
    update_changelog: bool = False,
    output_format: str = "text",
) -> str:
    """Generate a PR creation prompt.

    Args:
        branch: Branch to create PR from (None = current branch)
        target_branch: Target branch for PR (default: develop)
        update_changelog: Whether to update changelog (default: False)
        output_format: Output format (text, json, stream-json)

    Returns:
        The PR creation prompt string
    """
    extension = ".json" if output_format == "json" else ".md"
    
    branching_instructions = """
BRANCH STRATEGY DETECTION:
1. First, determine the current branch using: git symbolic-ref --short HEAD
2. Check for .branchingstrategy file in repository root
3. If found, parse release_branch (typically: develop) and use as target for PR
4. If not found, check for common development branches (develop, development, dev)
5. If none found, fall back to main/master as the target branch
6. IMPORTANT: Use the specified target branch if one was explicitly provided
7. Report both the current branch and target branch in the metadata
"""

    file_handling_instructions = f"""
FILE HANDLING INSTRUCTIONS:
1. Create the tmp/ directory if it doesn't exist: mkdir -p tmp
2. Determine the current branch: git symbolic-ref --short HEAD
3. Determine the target branch from the BRANCH STRATEGY DETECTION steps
4. Create a filename in this format: tmp/dylan-pr-[current-branch]-to-[target]{extension}
   - Replace any slashes in branch names with hyphens (e.g., feature/foo becomes feature-foo)
5. If the file already exists, APPEND your new PR report to the file with a clear separator
   - Add a timestamp header: ## PR Created [DATE] [TIME]
   - This allows tracking multiple PR attempts over time in the same file
"""

    return f"""
You are a PR creator with COMPLETE AUTONOMY to analyze commits and create pull requests.

YOUR MISSION:
1. Determine the branch to create PR from (current working branch)
2. Determine the target branch (default: develop or from branching strategy)
3. Analyze all commits in this branch vs target branch
4. {"Update changelog if requested" if update_changelog else "Skip changelog update"}
5. Create a high-quality pull request

{branching_instructions}

{file_handling_instructions}

CRITICAL STEPS - Use Bash and other tools to:

1. BRANCH DETERMINATION:
   - Current branch: git symbolic-ref --short HEAD
   - Verify branch exists: git rev-parse --verify HEAD
   - Check if pushed: git ls-remote --heads origin $(git symbolic-ref --short HEAD)
   - Apply BRANCH STRATEGY DETECTION to determine target branch
   - Override with "{target_branch}" if explicitly specified

2. PR PREPARATION:
   - Check for existing PRs: gh pr list --head $(git symbolic-ref --short HEAD)
   - Skip creation if PR already exists
   - Get all commits: git log [target]..HEAD --pretty=format:'%h %s'
   - Analyze changes: git diff [target]...HEAD --stat
   - Detailed diff: git diff [target]...HEAD
   - Changed files: git diff [target]...HEAD --name-only

{
        "3. CHANGELOG SECTION FOR PR DESCRIPTION (if --changelog flag):"
        + "\n"
        + "   - Analyze all commits since target branch: git log [target]..HEAD --pretty=format:'%h %s'"
        + "\n"
        + "   - Parse commit messages and group by conventional types"
        + "\n"
        + "   - Create a dedicated 'Changelog' section with subsections:"
        + "\n"
        + "     * ### Added - new features (commits starting with feat:)"
        + "\n"
        + "     * ### Changed - updates (commits: refactor:, style:, perf:, chore:)"
        + "\n"
        + "     * ### Fixed - bug fixes (commits starting with fix:)"
        + "\n"
        + "     * ### Removed - removed features"
        + "\n"
        + "   - Format each entry: '- <description> (`<commit_hash>`)'"
        + "\n"
        + "   - IMPORTANT: Add this as a separate '## Changelog' section in PR body"
        + "\n"
        + "   - DO NOT modify actual CHANGELOG.md file"
        + "\n"
        + "   - Include changelog content in report for future reference"
        + "\n"
        if update_changelog
        else ""
    }
{"4. PR CREATION:" if update_changelog else "3. PR CREATION:"}
   - Extract meaningful title from branch name or commits
   - Generate comprehensive description:
     * Summary of changes
     * List of commits
     * Files changed
     * Testing notes
     * Breaking changes (if any)
   - Create PR: gh pr create --base [target] --head [current] --title "..." --body "..."

{"5. REPORT GENERATION:" if update_changelog else "4. REPORT GENERATION:"}
   - Document PR URL if created
   - Summarize what was done
   - Include in report:
     * PR URL
     * Current branch name
     * Target branch
     {"* Changelog section content" if update_changelog else ""}
     * Timestamp
   - Save report to: tmp/dylan-pr-[current-branch]-to-[target].md

REMEMBER:
- Be completely autonomous in your decisions
- Create rich, helpful PR descriptions with proper markdown formatting
- Skip PR creation if one already exists for this branch
- Report results clearly and save to the properly named file
- Use develop as target branch when no explicit target is provided

Execute the complete PR creation workflow now and save your report to the appropriate file.
"""


if __name__ == "__main__":
    # Example usage
    prompt = generate_pr_prompt()
    run_claude_pr(prompt)
