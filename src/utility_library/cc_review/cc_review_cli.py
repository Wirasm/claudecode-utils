#!/usr/bin/env python3
"""
CLI interface for the Claude Code review runner using Typer.
"""

from typing import List, Optional

import typer
from rich import print

from .cc_review_runner import generate_review_prompt, run_claude_review
from .cc_review_utils import pretty_print_json_file

review_cmd = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@review_cmd.callback(invoke_without_command=True)
def review(
    branch: Optional[str] = typer.Argument(
        None, help="Branch to review (optional, defaults to latest changes)"
    ),
    tools: str = typer.Option(
        "Read,Glob,Grep,LS,Bash,Write", "--tools", help="Comma-separated list of allowed tools"
    ),
    format: str = typer.Option("text", "--format", help="Output format: text, json, stream-json"),
    pretty_print: Optional[str] = typer.Option(
        None, "--pretty-print", help="Pretty print a JSON file instead of running a review"
    ),
    pretty_output: Optional[str] = typer.Option(
        None,
        "--pretty-output",
        help="Save pretty-printed JSON to this file (use with --pretty-print)",
    ),
):
    """Run a code review using Claude Code."""
    # Handle pretty-print mode
    if pretty_print:
        pretty_print_json_file(pretty_print, pretty_output)
        return

    # Normal review mode
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
