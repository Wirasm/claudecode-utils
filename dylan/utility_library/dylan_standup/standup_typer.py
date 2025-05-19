#!/usr/bin/env python3
"""Typer wrapper for standup CLI to integrate with the main CLI."""

import sys
from pathlib import Path

import typer

from .standup_cli import main as standup_main

standup_app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_show_locals=False,
)


@standup_app.callback(invoke_without_command=True)
def standup(
    since: str | None = typer.Option(
        None,
        "--since",
        "-s",
        help="ISO datetime or natural language recognised by git (default: yesterday 09:00)",
    ),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output .md path (default: standup_<date>.md)"),
    open: bool = typer.Option(False, "--open", help="Open file afterwards"),
):
    """Generate a stand-up report from git commits and GitHub PRs."""
    # Reconstruct sys.argv to pass to the argparse-based main function
    args = ["standup"]

    if since:
        args.extend(["--since", since])

    if out:
        args.extend(["--out", str(out)])

    if open:
        args.append("--open")

    # Replace sys.argv temporarily
    original_argv = sys.argv
    sys.argv = args

    try:
        standup_main()
    finally:
        # Restore original argv
        sys.argv = original_argv
