"""Shared error handling utilities for Dylan CLI."""

import sys
from collections.abc import Callable

from rich.console import Console
from rich.progress import Progress

from .ui_theme import COLORS, create_status


def handle_dylan_errors(
    func: Callable,
    progress: Progress,
    task: int,
    console: Console,
    github_url: str | None = None,
) -> Callable:
    """Decorator for consistent error handling across Dylan utilities.

    Args:
        func: The function to wrap
        progress: Progress bar instance
        task: Task ID for progress updates
        console: Console instance for output
        github_url: Optional custom GitHub issues URL

    Returns:
        Wrapped function with error handling
    """
    github_issues_url = github_url or "https://github.com/Wirasm/dylan/issues"

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(str(e), "error"))
            sys.exit(1)
        except FileNotFoundError:
            progress.update(task, completed=True)
            console.print()
            console.print(create_status("Claude Code not found!", "error"))
            console.print(f"\n[{COLORS['warning']}]Please install Claude Code:[/]")
            console.print(f"[{COLORS['muted']}]  npm install -g @anthropic-ai/claude-code[/]")
            console.print(f"\n[{COLORS['muted']}]For more info: https://github.com/anthropics/claude-code[/]")
            sys.exit(1)
        except Exception as e:
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(f"Unexpected error: {e}", "error"))
            console.print(f"\n[{COLORS['muted']}]Please report this issue at:[/]")
            console.print(f"[{COLORS['primary']}]{github_issues_url}[/]")
            sys.exit(1)

    return wrapper
