"""Root Typer application that dispatches to vertical slices.

Includes 'standup', 'review', 'dev', 'pr', and 'release' commands.
"""

import typer
from rich.console import Console
from rich.table import Table

from .utility_library.dylan_dev.dylan_dev_cli import dev
from .utility_library.dylan_pr.dylan_pr_cli import pr
from .utility_library.dylan_release.dylan_release_cli import release_app
from .utility_library.dylan_review.dylan_review_cli import review
from .utility_library.dylan_standup.standup_typer import standup_app
from .utility_library.shared.ui_theme import ARROW, COLORS, SPARK

console = Console()

app = typer.Typer(
    help=f"[{COLORS['primary']}]Dylan[/] [{COLORS['accent']}]{SPARK}[/] AI-powered development utilities",
    add_completion=False,
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)
app.add_typer(standup_app, name="standup", help="Generate daily standup reports from git activity")
app.add_typer(release_app, name="release", help="Create and manage project releases")
app.command(name="review", help="Run AI-powered code reviews on git branches")(review)
app.command(name="dev", help="Implement fixes from code reviews")(dev)
app.command(name="pr", help="Create pull requests with AI-generated descriptions")(pr)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    """Show welcome message when no command is provided."""
    if ctx.invoked_subcommand is None:
        # Welcome header with flair
        console.print(f"\n[{COLORS['primary']}]{ARROW}[/] [bold]Dylan[/bold] [{COLORS['accent']}]{SPARK}[/]")
        console.print("[dim]AI-powered development utilities using Claude Code[/dim]\n")

        # Commands table with custom styling
        table = Table(
            show_header=True,
            header_style=f"bold {COLORS['primary']}",
            border_style=COLORS['muted'],
            title_style=f"bold {COLORS['accent']}",
            box=None,
        )

        table.add_column("Command", style=COLORS['secondary'], width=12)
        table.add_column("Description", style=COLORS['primary'])
        table.add_column("Example", style="dim")

        table.add_row(
            "standup",
            "Generate daily standup reports",
            "dylan standup --since yesterday"
        )
        table.add_row(
            "review",
            "Run code reviews on branches",
            "dylan review feature-branch"
        )
        table.add_row(
            "dev",
            "Implement fixes from reviews",
            "dylan dev tmp/review.md"
        )
        table.add_row(
            "pr",
            "Create pull requests",
            "dylan pr --target develop"
        )
        table.add_row(
            "release",
            "Manage project releases",
            "dylan release --minor --tag"
        )

        console.print(table)
        help_text = f"\n[{COLORS['muted']}]Use[/] [{COLORS['primary']}]dylan <command> --help[/]"
        console.print(f"{help_text} [{COLORS['muted']}]for detailed options[/]")
        console.print("[dim]Example: dylan review --help[/dim]\n")
