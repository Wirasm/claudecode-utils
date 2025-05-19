"""Custom progress indicators for Dylan CLI."""

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.spinner import SPINNERS

from .ui_theme import COLORS, DYLAN_SPINNER

# Register Dylan's custom spinner once at module load
SPINNERS["dylan"] = DYLAN_SPINNER


def create_dylan_progress(console=None):
    """Create a progress bar with Dylan's custom spinner."""
    # SpinnerColumn will use the custom frames directly
    return Progress(
        SpinnerColumn(spinner_name="dylan", style=COLORS['primary']),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
        expand=False,
    )


def create_task_with_dylan(progress, message):
    """Create a task with Dylan-themed message."""
    colored_message = f"[{COLORS['primary']}]{message}[/]"
    return progress.add_task(colored_message, total=None)
