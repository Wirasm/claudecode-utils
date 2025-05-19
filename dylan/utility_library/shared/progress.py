"""Custom progress indicators for Dylan CLI."""

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .ui_theme import COLORS, DYLAN_SPINNER


def create_dylan_progress(console=None):
    """Create a progress bar with Dylan's custom spinner."""
    # Register our custom spinner first
    register_dylan_spinner()

    # SpinnerColumn will use the custom frames directly
    return Progress(
        SpinnerColumn(spinner_name="dylan", spinner_style=COLORS['primary']),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
        expand=False,
    )

def register_dylan_spinner():
    """Register Dylan's custom spinner with Rich."""
    from rich.spinner import SPINNERS
    SPINNERS["dylan"] = DYLAN_SPINNER


def create_task_with_dylan(progress, message):
    """Create a task with Dylan-themed message."""
    colored_message = f"[{COLORS['primary']}]{message}[/]"
    return progress.add_task(colored_message, total=None)
