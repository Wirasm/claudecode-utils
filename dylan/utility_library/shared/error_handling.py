"""Shared error handling utilities for Dylan CLI.

This module provides consistent error handling across all Dylan utilities,
with proper formatting and user-friendly error messages.

Example usage:
    >>> from dylan.utility_library.shared.error_handling import handle_dylan_errors
    >>> @handle_dylan_errors()
    ... def my_function(progress, task, console):
    ...     # Function will be wrapped with error handling
    ...     pass
"""

import sys
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.progress import Progress

from .config import CLAUDE_CODE_INSTALL_CMD, CLAUDE_CODE_REPO_URL, GITHUB_ISSUES_URL
from .ui_theme import COLORS, create_status


def handle_dylan_errors(
    utility_name: str | None = None,
    github_url: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for consistent error handling across Dylan utilities.

    Args:
        utility_name: Name of the utility for error context
        github_url: Optional custom GitHub issues URL

    Returns:
        Decorator function for error handling
    """
    github_issues_url = github_url or GITHUB_ISSUES_URL

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(progress: Progress, task: int, console: Console, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(progress, task, console, *args, **kwargs)
            except RuntimeError as e:
                progress.update(task, completed=True)
                console.print()
                error_context = f"{utility_name}: " if utility_name else ""
                console.print(create_status(f"{error_context}{str(e)}", "error"))
                sys.exit(1)
            except FileNotFoundError:
                progress.update(task, completed=True)
                console.print()
                error_context = f" while running {utility_name}" if utility_name else ""
                console.print(create_status(f"Claude Code not found{error_context}!", "error"))
                console.print(f"\n[{COLORS['warning']}]Please install Claude Code:[/]")
                console.print(f"[{COLORS['muted']}]  {CLAUDE_CODE_INSTALL_CMD}[/]")
                console.print(f"\n[{COLORS['muted']}]For more info: {CLAUDE_CODE_REPO_URL}[/]")
                sys.exit(1)
            except Exception as e:
                progress.update(task, completed=True)
                console.print()
                error_context = f"in {utility_name} " if utility_name else ""
                console.print(create_status(f"Unexpected error {error_context}: {e}", "error"))
                console.print(f"\n[{COLORS['muted']}]Please report this issue at:[/]")
                console.print(f"[{COLORS['primary']}]{github_issues_url}[/]")
                # Include utility context in debug mode
                if utility_name:
                    console.print(f"\n[{COLORS['muted']}]Utility: {utility_name}[/]")
                    console.print(f"[{COLORS['muted']}]Error type: {type(e).__name__}[/]")
                sys.exit(1)

        return wrapper
    return decorator
