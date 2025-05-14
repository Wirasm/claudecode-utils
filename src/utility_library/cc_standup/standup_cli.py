"""
Typer command for stand-up generation.
"""

from __future__ import annotations

import datetime as dt
import pathlib

import typer

from .activity import collect_commits, collect_prs
from .provider import get_provider
from .report import build_prompt, preview

standup_cmd = typer.Typer(add_completion=False)


@standup_cmd.command("run", help="Generate a stand-up report.")
def run(
    since: str = typer.Option(
        None,
        help="ISO datetime or natural language recognised by git (default: yesterday 09:00)",
    ),
    out: pathlib.Path = typer.Option(None, help="Output .md path (default: standup_<date>.md)"),
    open_file: bool = typer.Option(False, "--open", "-o", help="Open file afterwards"),
):
    # 1️⃣  Resolve date range
    if since is None:
        since_dt = (dt.datetime.now() - dt.timedelta(days=1)).replace(hour=9, minute=0)
    else:
        since_dt = dt.datetime.fromisoformat(since)
    since_iso = since_dt.isoformat()

    # 2️⃣  Collect activity
    commits = collect_commits(since_iso)
    prs = collect_prs(since_dt)

    if not commits and not prs:
        typer.secho("No activity found for range.", fg=typer.colors.YELLOW)
        raise typer.Exit()

    # 3️⃣  Prompt Claude
    provider = get_provider()  # only Claude for now
    prompt = build_prompt(commits, prs)
    markdown = provider.generate(prompt)

    # 4️⃣  Show + persist
    preview(markdown)
    outfile = out or pathlib.Path(f"standup_{dt.date.today()}.md")
    outfile.write_text(markdown, encoding="utf-8")
    typer.secho(f"Saved to {outfile}", fg=typer.colors.GREEN)

    if open_file:
        import webbrowser

        webbrowser.open(outfile.resolve().as_uri())
