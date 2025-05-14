"""
Root Typer application that dispatches to vertical slices.
For now only the 'standup' command is registered.
"""

import typer
from rich import print

from .utility_library.cc_standup.standup_cli import standup_cmd

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(standup_cmd, name="standup", help="Generate Markdown stand-up report")


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context):
    """Show help if no sub-command supplied."""
    if ctx.invoked_subcommand is None:
        print("[yellow]Nothing to do - choose a sub-command.[/]")
        typer.echo(app.get_help())
