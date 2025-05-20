#!/usr/bin/env python3
"""CLI interface for the Claude Code review runner using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
    format_tool_count,
)
from .dylan_review_runner import generate_review_prompt, run_claude_review

console = Console()


def review(
    branch: str | None = typer.Argument(
        default=None,
        help="Branch to review (defaults to latest changes against base branch)",
        metavar="BRANCH",
    ),
    tools: str = typer.Option(
        "Read,Glob,Grep,LS,Bash,Write",
        "--tools",
        "-t",
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
):
    """Run AI-powered code review using Claude Code.

    Reviews git branches or latest changes against the base branch (develop/main).
    Generates detailed feedback with issue identification and suggested fixes.

    Examples:
        # Review latest changes against base branch
        dylan review

        # Review specific feature branch
        dylan review feature/my-feature

        # Generate JSON output for automation
        dylan review --format json

        # Limit tools for security
        dylan review --tools "Read,LS"
    """
    # Parse tools first
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Code Review"))
    console.print()

    # Show review configuration
    console.print(create_box_header("Review Configuration", {
        "Branch": branch or "latest changes",
        "Format": format,
        "Tools": format_tool_count(allowed_tools),
        "Stream": format_boolean_option(stream, "✓ Enabled", "✗ Disabled"),
        "Exit": "/exit (type to quit at any time)"
    }))
    console.print()

    # Generate prompt
    prompt = generate_review_prompt(branch=branch, output_format=format)

    # Run review
    run_claude_review(
        prompt,
        allowed_tools=allowed_tools,
        output_format=format,
        stream=stream
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(review)
