#!/usr/bin/env python3
"""
Command-line interface for stand-up generation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys
import webbrowser

from rich.console import Console

from .activity import collect_commits, collect_prs
from .provider import get_provider
from .report import build_prompt, preview

console = Console()


def main():
    """Main entry point for the standup command."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a stand-up report from git commits and GitHub PRs.")
    parser.add_argument(
        "--since",
        "-s",
        help="ISO datetime or natural language recognised by git (default: yesterday 09:00)",
    )
    parser.add_argument(
        "--out",
        "-o",
        help="Output .md path (default: standup_<date>.md)",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--open",
        help="Open file afterwards",
        action="store_true",
    )

    # Parse known args to handle unknown arguments gracefully
    args, _ = parser.parse_known_args()

    # Resolve date range
    if args.since is None:
        since_dt = (dt.datetime.now() - dt.timedelta(days=1)).replace(hour=9, minute=0)
    else:
        try:
            since_dt = dt.datetime.fromisoformat(args.since)
        except ValueError:
            console.print(
                f"[red]Error: Invalid date format '{args.since}'. Use ISO format (YYYY-MM-DDTHH:MM:SS).[/red]"
            )
            sys.exit(1)

    since_iso = since_dt.isoformat()

    # Collect activity
    try:
        commits = collect_commits(since_iso)
        prs = collect_prs(since_dt)
    except Exception as e:
        console.print(f"[red]Error collecting activity: {str(e)}[/red]")
        sys.exit(1)

    if not commits and not prs:
        console.print("[yellow]No activity found for the specified date range.[/yellow]")
        sys.exit(0)

    # Create output file path
    outfile = args.out or pathlib.Path(f"standup_{dt.date.today()}.md")

    # Let the user know we're generating the report
    console.print("[yellow]Generating stand-up report...[/yellow]")

    # Prompt Claude
    provider = get_provider()  # only Claude for now
    prompt = build_prompt(commits, prs)
    markdown = provider.generate(prompt)

    # Save the file directly
    outfile.write_text(markdown, encoding="utf-8")

    # Show preview and confirmation
    preview(markdown)
    console.print(f"[green]Report saved to {outfile}[/green]")

    if args.open:
        webbrowser.open(outfile.resolve().as_uri())


if __name__ == "__main__":
    main()
