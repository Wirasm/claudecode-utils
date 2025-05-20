#!/usr/bin/env python3
"""CLI interface for the Claude Code review runner using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
)
from .dylan_review_runner import generate_review_prompt, run_claude_review

console = Console()


def review(
    branch: str | None = typer.Argument(
        default=None,
        help="Branch to review (defaults to latest changes against base branch)",
        metavar="BRANCH",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print debug information (including the full prompt)",
        show_default=True,
    ),
):
    """Run AI-powered code review using Claude Code.

    Reviews git branches or latest changes against the base branch (develop/main).
    Generates detailed feedback with issue identification and suggested fixes.

    Examples:
        # Review latest changes against base branch
        dylan review

        # Review specific feature branch
        dylan review feature/my-feature

        # Show debug information including the prompt
        dylan review --debug
    """
    # Default values
    allowed_tools = ["Read", "Glob", "Grep", "LS", "Bash", "Write"]
    output_format = "text"

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Code Review"))
    console.print()

    # Show review configuration
    console.print(create_box_header("Review Configuration", {
        "Branch": branch or "current branch",
        "Debug": format_boolean_option(debug, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt"
    }))
    console.print()

    # Generate prompt
    prompt = generate_review_prompt(branch=branch, output_format=output_format)

    # Run review
    run_claude_review(
        prompt,
        allowed_tools=allowed_tools,
        output_format=output_format,
        debug=debug
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(review)
