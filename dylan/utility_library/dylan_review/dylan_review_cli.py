#!/usr/bin/env python3
"""CLI interface for the Claude Code review runner using Typer."""


import typer

from .dylan_review_runner import generate_review_prompt, run_claude_review


def review(
    branch: str | None = typer.Argument(
        None, help="Branch to review (optional, defaults to latest changes)"
    ),
    tools: str = typer.Option(
        "Read,Glob,Grep,LS,Bash,Write", "--tools", help="Comma-separated list of allowed tools"
    ),
    format: str = typer.Option("text", "--format", help="Output format: text, json, stream-json"),
):
    """Run a code review using Claude Code."""
    # Parse tools
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Generate prompt
    prompt = generate_review_prompt(branch=branch, output_format=format)

    # Run review
    run_claude_review(prompt, allowed_tools=allowed_tools, output_format=format)


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(review)
