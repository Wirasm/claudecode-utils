"""Exit command utilities and messaging for CLI interfaces.

This module provides utilities for displaying exit command information to users
and handling exit command functionality consistently across the CLI.
"""

from rich.console import Console
from rich.panel import Panel

from .ui_theme import COLORS

# Default exit command
DEFAULT_EXIT_COMMAND = "/exit"


def create_exit_command_panel(exit_command: str = DEFAULT_EXIT_COMMAND) -> Panel:
    """Create a panel displaying exit command information.

    Args:
        exit_command: The exit command to display (defaults to "/exit")

    Returns:
        Rich Panel object with exit command information
    """
    message = (
        f"Type [{COLORS['secondary']}]{exit_command}[/] at any time to gracefully exit"
    )
    return Panel(
        message,
        expand=False,
        padding=(1, 2),
        border_style=COLORS['muted'],
        title="Exit Command",
        title_align="left",
    )


def show_exit_command_message(
    console: Console,
    exit_command: str = DEFAULT_EXIT_COMMAND,
    show_panel: bool = False,
    style: str = "tip",
) -> None:
    """Display exit command information to the user.

    Args:
        console: Rich console instance for display
        exit_command: The exit command to display (defaults to "/exit")
        show_panel: Whether to show as a panel (True) or simple message (False)
        style: Style of message - "tip" (subtle), "standard" (normal), or "prominent" (highlighted)
    """
    if show_panel:
        panel = create_exit_command_panel(exit_command)
        console.print(panel)
    elif style == "prominent":
        console.print()
        console.print(
            f"[bold {COLORS['warning']}]⚠️  Type [{COLORS['secondary']}]"
            f"{exit_command}[/][bold {COLORS['warning']}] at any time to exit gracefully ⚠️[/]",
            highlight=False
        )
        console.print()
    elif style == "standard":
        console.print(
            f"[{COLORS['primary']}]Type [{COLORS['secondary']}]"
            f"{exit_command}[/][{COLORS['primary']}] at any time to exit.[/]"
        )
    else:  # "tip" style (default)
        console.print(
            f"[{COLORS['muted']}]Tip: Type [{COLORS['secondary']}]"
            f"{exit_command}[/][{COLORS['muted']}] at any time to exit.[/]"
        )


def format_provider_options(options: dict) -> dict:
    """Add exit command to provider options if streaming is enabled.

    Args:
        options: Provider options dict

    Returns:
        Updated options dict with exit_command if streaming is enabled
    """
    # Clone the options
    updated_options = options.copy()

    # If streaming is enabled, add exit command
    if updated_options.get('stream', False):
        # Only add if not already present
        if 'exit_command' not in updated_options:
            updated_options['exit_command'] = DEFAULT_EXIT_COMMAND

    return updated_options
