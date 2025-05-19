"""Custom progress indicators for Dylan CLI.

This module provides progress bar functionality with custom spinners
specific to the Dylan CLI, allowing for visual consistency across utilities.

Example usage:
    >>> from dylan.utility_library.shared.progress import create_dylan_progress
    >>> with create_dylan_progress() as progress:
    ...     task = progress.add_task("Processing...", total=None)
    ...     # Do work
    ...     progress.update(task, advance=1)
"""


from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.spinner import SPINNERS

from .ui_theme import COLORS, DYLAN_SPINNER, SIMPLE_SPINNER

# Register Dylan's custom spinners once at module load
SPINNERS["dylan"] = DYLAN_SPINNER
SPINNERS["dylan_simple"] = SIMPLE_SPINNER


def create_dylan_progress(console: Console | None = None, simple: bool = False) -> Progress:
    """Create a progress bar with Dylan's custom spinner.

    Args:
        console: Optional console instance
        simple: Use simple spinner for better performance

    Returns:
        Configured Progress instance
    """
    spinner_name = "dylan_simple" if simple else "dylan"
    return Progress(
        SpinnerColumn(spinner_name=spinner_name, style=COLORS['primary']),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
        expand=False,
    )


def create_task_with_dylan(progress: Progress, message: str) -> int:
    """Create a task with Dylan-themed message."""
    colored_message: str = f"[{COLORS['primary']}]{message}[/]"
    return progress.add_task(colored_message, total=None)
