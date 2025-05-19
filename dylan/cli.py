"""Root Typer application that dispatches to vertical slices.

Includes 'standup', 'review', and 'pr' commands.
"""

import typer
from rich import print

from .utility_library.dylan_pr.dylan_pr_cli import pr
from .utility_library.dylan_review.dylan_review_cli import review
from .utility_library.dylan_standup.standup_typer import standup_app

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(standup_app, name="standup", help="Generate Markdown stand-up report")
app.command(name="review", help="Run code reviews using Claude Code")(review)
app.command(name="pr", help="Create pull requests using Claude Code")(pr)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context):
    """Show help if no sub-command supplied."""
    if ctx.invoked_subcommand is None:
        print("[yellow]Nothing to do - choose a sub-command.[/]")
        typer.echo(app.get_help())
