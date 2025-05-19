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
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..provider_clis.provider_claude_code import get_provider
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status

console = Console()


def run_claude_pr(
    prompt: str,
    allowed_tools: list[str] | None = None,
    output_format: Literal["text", "json", "stream-json"] = "text",
) -> None:
    """Run Claude code with a PR creation prompt and specified tools.

    Args:
        prompt: The PR creation prompt to send to Claude
        allowed_tools: List of allowed tools (defaults to Read, Bash, Write)
        output_format: Output format (text, json, stream-json)
    """
    # Default safe tools for PR creation
    if allowed_tools is None:
        allowed_tools = ["Read", "Bash", "Write", "Glob", "Grep"]

    # Determine output file based on format - always in tmp directory
    output_file = "tmp/pr_report.json" if output_format == "json" else "tmp/pr_report.md"

    # Get provider and run the PR creation
    provider = get_provider()

    with Progress(
        SpinnerColumn(spinner_name="dots", style=COLORS['primary']),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        # Start the PR task
        task = progress.add_task(
            f"[{COLORS['primary']}]Dylan is creating your pull request...[/]",
            total=None
        )

        try:
            result = provider.generate(
                prompt, output_path=output_file, allowed_tools=allowed_tools, output_format=output_format
            )

            # Update task to complete
            progress.update(task, completed=True)

            # Success message with flair
            console.print()
            console.print(create_status("Pull request created successfully!", "success"))
            console.print(f"[{COLORS['muted']}]Report saved to:[/] [{COLORS['accent']}]{output_file}[/]")
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
            console.print(f"[{COLORS['muted']}]  npm install -g @anthropic-ai/claude-code[/]")
            console.print(f"\n[{COLORS['muted']}]For more info: https://github.com/anthropics/claude-code[/]")
            sys.exit(1)
        except Exception as e:
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(f"Unexpected error: {e}", "error"))
            console.print(f"\n[{COLORS['muted']}]Please report this issue at:[/]")
            console.print(f"[{COLORS['primary']}]https://github.com/Wirasm/claudecode-utils/issues[/]")
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
    branch_instruction = f"'{branch}'" if branch else "the current branch"
    extension = ".json" if output_format == "json" else ".md"

    return f"""
You are a PR creator with COMPLETE AUTONOMY to analyze commits and create pull requests.

YOUR MISSION:
1. Determine the branch to create PR from ({branch_instruction})
2. Analyze all commits in this branch vs {target_branch}
3. {"Update changelog if requested" if update_changelog else "Skip changelog update"}
4. Create a high-quality pull request

IMPORTANT FILE HANDLING INSTRUCTIONS:
- Save your report to the tmp/ directory
- If tmp/pr_report{extension} already exists, create a new file with timestamp
- Format: tmp/pr_report_YYYYMMDD_HHMMSS{extension}
- Use the Bash tool to check if the file exists first
- DO NOT modify or append to existing files

CRITICAL STEPS - Use Bash and other tools to:

1. FILE HANDLING:
   - Check if tmp/pr_report{extension} exists
   - If it exists, create new filename with timestamp
   - Ensure tmp/ directory exists: mkdir -p tmp

2. GIT CONTEXT DISCOVERY:
   - Current branch: git symbolic-ref --short HEAD
   - Verify branch exists: git rev-parse --verify {branch or "HEAD"}
   - Check if pushed: git ls-remote --heads origin {branch or "$(git symbolic-ref --short HEAD)"}
   - Get default branch: git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   - List existing PRs: gh pr list --head {branch or "$(git symbolic-ref --short HEAD)"}

3. COMMIT ANALYSIS:
   - Get all commits: git log {target_branch}..{branch or "HEAD"} --pretty=format:'%h %s'
   - Analyze changes: git diff {target_branch}...{branch or "HEAD"} --stat
   - Detailed diff: git diff {target_branch}...{branch or "HEAD"}
   - Changed files: git diff {target_branch}...{branch or "HEAD"} --name-only

{
        "4. CHANGELOG UPDATE (if --changelog flag):"
        + "\n"
        + "   - Find CHANGELOG.md (or HISTORY.md, NEWS.md)"
        + "\n"
        + "   - Locate [Unreleased] section"
        + "\n"
        + "   - Analyze commits and group by type:"
        + "\n"
        + "     * Added: new features (feat:)"
        + "\n"
        + "     * Changed: updates to existing features"
        + "\n"
        + "     * Fixed: bug fixes (fix:)"
        + "\n"
        + "     * Removed: removed features"
        + "\n"
        + "   - Add commit entries to appropriate sections"
        + "\n"
        + '   - Format: "- Description of change (`commit_hash`)"'
        + "\n"
        + "   - Use Edit tool to update changelog"
        + "\n"
        + '   - Stage and commit: git add CHANGELOG.md && git commit -m "docs: update unreleased section"'
        + "\n"
        if update_changelog
        else ""
    }
{"5. PR CREATION LOGIC:" if update_changelog else "4. PR CREATION LOGIC:"}
   - Skip if PR already exists
   - Extract meaningful title from branch name or commits
   - Generate comprehensive description:
     * Summary of changes
     * List of commits
     * Files changed
     * Testing notes
     * Breaking changes (if any)
   - Create PR: gh pr create --base {target_branch} --head {
        branch or "$(git symbolic-ref --short HEAD)"
    } --title "..." --body "..."

{"6. REPORT GENERATION:" if update_changelog else "5. REPORT GENERATION:"}
   - Document PR URL if created
   - Summarize what was done
   - Note any issues encountered
   - Save to appropriate filename in tmp/

REMEMBER:
- Be autonomous - make all decisions yourself
- Create rich, helpful PR descriptions
- Use proper markdown formatting
- Report results clearly
- Save report with proper filename handling

Execute the complete PR creation workflow now and save your report to the appropriate file.
"""


if __name__ == "__main__":
    # Example usage
    prompt = generate_pr_prompt()
    run_claude_pr(prompt)
