#!/usr/bin/env python3
"""CLI interface for the Claude Code PR creator using Typer."""

import typer

from .dylan_pr_runner import generate_pr_prompt, run_claude_pr


def pr(
    branch: str | None = typer.Argument(
        default=None, help="Branch to create PR from (optional, defaults to current branch)"
    ),
    target: str = typer.Option(
        "main", "--target", "-t", help="Target branch for PR"
    ),
    tools: str = typer.Option(
        "Read,Bash,Write,Glob,Grep", "--tools", help="Comma-separated list of allowed tools"
    ),
    format: str = typer.Option("text", "--format", help="Output format: text, json, stream-json"),
):
    """Create a pull request using Claude Code."""
    # Parse tools
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Generate prompt
    prompt = generate_pr_prompt(branch=branch, target_branch=target, output_format=format)

    # Run PR creation
    run_claude_pr(prompt, allowed_tools=allowed_tools, output_format=format)


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    typer.run(pr)


if __name__ == "__main__":
    main()
