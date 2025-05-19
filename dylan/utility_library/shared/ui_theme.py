"""Shared UI theme and styling for Dylan CLI.

This module provides a consistent visual theme across all Dylan utilities,
including colors, symbols, spinners, and formatting functions.

Example usage:
    >>> from dylan.utility_library.shared.ui_theme import create_header, COLORS
    >>> print(create_header("My Command", "Running..."))
    ❯ My Command ✧
    Running...
"""

from typing import Any

# Colors and symbols
ARROW = "❯"
SPARK = "✧"
CHECK = "✓"
CROSS = "✗"
SPINNER = "◍"

# Animation timing
SPINNER_INTERVAL_MS = 400  # Milliseconds between spinner frames
DEFAULT_SPINNER_INTERVAL_MS = 200  # Default interval for simpler spinners

# Dylan's thinking spinner frames - ASCII art faces looking around
# Reduced from 22 to 12 frames for better performance
DYLAN_SPINNER = {
    "interval": SPINNER_INTERVAL_MS,
    "frames": [
        "( o.o) ✧",      # Looking forward
        "( o.-) ✧",      # Look right
        "( -.o) ✧",      # Look left
        "( o.o) ✧",      # Back to center
        "( ^.^) ✧",      # Happy/thinking
        "( o.o) ✧",      # Back to normal
        "( -.-) ✧",      # Eyes closed/thinking
        "( o.o) ✧",      # Open eyes
        "( o.O) ✧",      # Surprised/curious
        "( o.o) ✧",      # Back to normal
        "( @.@) ✧",      # Dizzy/processing
        "( o.o) ✧",      # Recovered
    ]
}

# Simple spinner for better performance when needed
SIMPLE_SPINNER = {
    "interval": DEFAULT_SPINNER_INTERVAL_MS,
    "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
}

# Color scheme - Using hex codes consistently for all colors
COLORS = {
    "primary": "#3B82F6",     # Blue
    "secondary": "#8B5CF6",   # Purple
    "success": "#10B981",     # Green
    "error": "#EF4444",       # Red
    "warning": "#F59E0B",     # Amber
    "accent": "#EC4899",      # Pink
    "muted": "#6B7280",       # Gray
    "info": "#3B82F6",        # Same as primary
    "working": "#3B82F6",     # Same as primary
}

def create_header(title: str, subtitle: str = "") -> str:
    """Create a stylized header with arrow and spark.

    Args:
        title: The main title
        subtitle: Optional subtitle

    Returns:
        Formatted header string
    """
    header: str = f"[{COLORS['primary']}]{ARROW}[/] [bold]{title}[/bold] [{COLORS['accent']}]{SPARK}[/]"
    if subtitle:
        header += f"\n[dim]{subtitle}[/dim]"
    return header

def create_status(message: str, status: str = "info") -> str:
    """Create a status message with appropriate icon and color.

    Args:
        message: The message to display
        status: The status type (success, error, working, info)

    Returns:
        Formatted status message
    """
    icons: dict[str, str] = {
        "success": f"[{COLORS['success']}]{CHECK}[/]",
        "error": f"[{COLORS['error']}]{CROSS}[/]",
        "working": f"[{COLORS['primary']}]{SPINNER}[/]",
        "info": f"[{COLORS['muted']}]•[/]",
    }

    icon: str = icons.get(status, icons["info"])
    color: str = COLORS.get(status, COLORS["primary"])

    return f"{icon} [{color}]{message}[/]"

def create_box_header(title: str, items: dict[str, Any]) -> str:
    """Create a box header with key-value pairs.

    Args:
        title: The header title
        items: Key-value pairs to display

    Returns:
        Formatted box header
    """
    lines: list[str] = [f"[{COLORS['primary']}]╭─[/] [bold]{title}[/bold]"]

    for key, value in items.items():
        lines.append(f"[{COLORS['primary']}]│[/] [dim]{key}:[/dim] [{COLORS['accent']}]{value}[/]")

    lines.append(f"[{COLORS['primary']}]╰─[/]")
    return "\n".join(lines)


def format_tool_count(tools: list[str]) -> str:
    """Format tool count for display.

    Args:
        tools: List of tool names

    Returns:
        Formatted tool count string
    """
    return f"{len(tools)} tools enabled"


def format_boolean_option(enabled: bool, true_text: str = "✓ Enabled", false_text: str = "✗ Disabled") -> str:
    """Format a boolean option for display.

    Args:
        enabled: The boolean value
        true_text: Text to show when True
        false_text: Text to show when False

    Returns:
        Formatted option string
    """
    return true_text if enabled else false_text
