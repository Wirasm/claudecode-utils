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
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive chat mode with Claude for code review.",
        show_default=True,
    )
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
        "Interactive Mode": format_boolean_option(interactive, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt"
    }))
    console.print()

    # Generate prompt
    # For interactive mode, this will be the initial prompt sent to Claude.
    prompt = generate_review_prompt(branch=branch, output_format=output_format)

    # Run review
    run_claude_review(
        prompt,
        allowed_tools=allowed_tools,
        branch=branch, # Pass branch along, though runner might not use it directly with provider
        output_format=output_format,
        debug=debug,
        interactive=interactive
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(review)
