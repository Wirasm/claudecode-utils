#!/usr/bin/env python3
"""CLI interface for the Claude Code PR creator using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
    format_tool_count,
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
        help="Skip updating the [Unreleased] section in CHANGELOG.md",
        show_default=True,
    ),
    tools: str = typer.Option(
        "Read,Bash,Write,Glob,Grep",
        "--tools",
        help="Comma-separated list of allowed tools for Claude",
        show_default=True,
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text (markdown), json, or stream-json",
        show_default=True,
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        "-s",
        help="Stream output in real-time (enables exit command)",
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
    """Create pull requests with AI-generated descriptions.

    Analyzes commits and generates comprehensive PR descriptions.
    Integrates with GitHub CLI to create actual PRs.

    Examples:
        # Create PR from current branch to main
        dylan pr

        # Create PR from feature branch to develop
        dylan pr feature/my-feature --target develop

        # Update changelog while creating PR
        dylan pr --changelog

        # Create PR with custom target and tools
        dylan pr --target develop --tools "Read,Bash"
    """
    # Parse tools first
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Pull Request"))
    console.print()

    # Show PR configuration
    console.print(create_box_header("PR Configuration", {
        "Source": branch or "current branch",
        "Target": target,
        "Changelog": format_boolean_option(not no_changelog, "✓ Enabled (default)", "✗ Disabled"),
        "Tools": format_tool_count(allowed_tools),
        "Stream": format_boolean_option(stream, "✓ Enabled", "✗ Disabled"),
        "Exit": format_boolean_option(stream, "/exit (type to quit at any time)", "Ctrl+C to interrupt")
    }))
    console.print()

    # Generate prompt - changelog is now enabled by default unless --no-changelog is specified
    prompt = generate_pr_prompt(
        branch=branch,
        target_branch=target,
        update_changelog=not no_changelog,
        output_format=format
    )

    # Run PR creation
    run_claude_pr(prompt, allowed_tools=allowed_tools, output_format=format, stream=stream, debug=debug)


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(pr)


if __name__ == "__main__":
    main()
