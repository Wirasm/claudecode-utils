#!/usr/bin/env python3
"""CLI interface for the Claude Code PR creator using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
)
from .dylan_pr_runner import generate_pr_prompt, run_claude_pr

console = Console()


def pr(
    branch: str | None = typer.Argument(
        default=None,
        help="Source branch for PR (defaults to current branch)",
        metavar="BRANCH",
    ),
    target: str = typer.Option(
        "develop",
        "--target",
        "-t",
        help="Target branch for PR (defaults to develop, falls back to main if develop doesn't exist)",
        show_default=True,
    ),
    no_changelog: bool = typer.Option(
        False,
        "--no-changelog",
        "-n",
        help="Skip generating suggested changelog updates in the PR and report",
        show_default=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without creating a PR or pushing commits",
        show_default=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print debug information (including the full prompt)",
        show_default=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive chat mode with Claude for PR creation.",
        show_default=True,
    )
):
    """Create pull requests with AI-generated descriptions.

    Analyzes commits and generates comprehensive PR descriptions.
    Integrates with GitHub CLI to create actual PRs.

    Examples:
        # Create PR from current branch to develop
        dylan pr

        # Create PR from feature branch to develop
        dylan pr feature/my-feature --target develop

        # Skip changelog suggestions in PR
        dylan pr --no-changelog

        # Preview PR creation without actually creating it
        dylan pr --dry-run
    """
    # Default values
    allowed_tools = ["Read", "Bash", "Write", "Glob", "Grep", "TodoRead", "TodoWrite"]
    output_format = "text"

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Pull Request"))
    console.print()

    # Show PR configuration
    console.print(create_box_header("PR Configuration", {
        "Source": branch or "current branch",
        "Target": target,
        "Changelog": format_boolean_option(not no_changelog, "✓ Enabled (default)", "✗ Disabled"),
        "Mode": "🔍 Dry run" if dry_run else "🚀 Live run",
        "Debug": format_boolean_option(debug, "✓ Enabled", "✗ Disabled"),
        "Interactive Mode": format_boolean_option(interactive, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt"
    }))
    console.print()

    # Generate prompt - changelog is now enabled by default unless --no-changelog is specified
    # For interactive mode, this will be the initial prompt sent to Claude.
    prompt = generate_pr_prompt(
        branch=branch,
        target_branch=target,
        update_changelog=not no_changelog,
        dry_run=dry_run,
        output_format=output_format
    )

    # Run PR creation
    run_claude_pr(
        prompt,
        allowed_tools=allowed_tools,
        output_format=output_format,
        debug=debug,
        interactive=interactive
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(pr)


if __name__ == "__main__":
    main()
