"""Exit command utilities and messaging for CLI interfaces.

This module provides utilities for displaying exit command information to users
and handling exit command functionality consistently across the CLI.
"""

import threading

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
    """Add exit command to provider options.

    Args:
        options: Provider options dict

    Returns:
        Updated options dict with exit_command
    """
    # Clone the options
    updated_options = options.copy()

    # Always add exit command if not already present
    if 'exit_command' not in updated_options:
        updated_options['exit_command'] = DEFAULT_EXIT_COMMAND

    return updated_options


def setup_exit_command_handler(process, exit_command: str = None) -> threading.Event:
    """Sets up an exit command handler for any process.

    This simplified handler helps with process termination and tracking.
    The user can press Ctrl+C to exit the process.

    Args:
        process: The subprocess.Popen process to send signals to
        exit_command: Not used in simplified implementation

    Returns:
        threading.Event that will be set when exit is triggered
    """
    exit_triggered = threading.Event()

    def process_monitor():
        """Monitor for process termination."""
        try:
            # Wait for process to complete or be terminated
            process.wait()
        except Exception:
            # Process might already be gone, ignore errors
            import sys
            print("Process monitoring error", file=sys.stderr)
        finally:
            # Always set the exit triggered flag
            exit_triggered.set()

    # Start process monitor thread
    monitor_thread = threading.Thread(target=process_monitor, daemon=True)
    monitor_thread.start()

    return exit_triggered
