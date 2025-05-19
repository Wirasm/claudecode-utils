"""Shared UI theme and styling for Dylan CLI."""

from typing import Any

# Colors and symbols
ARROW = "❯"
SPARK = "✧"
CHECK = "✓"
CROSS = "✗"
SPINNER = "◍"

# Animation timing
SPINNER_INTERVAL_MS = 400  # Milliseconds between spinner frames

# Dylan's thinking spinner frames - ASCII art faces looking around
DYLAN_SPINNER = {
    "interval": SPINNER_INTERVAL_MS,
    "frames": [
        "( o.o) ✧",      # Looking forward
        "( o.o) ✧",      # Stay a bit
        "( o.-) ✧",      # Look right
        "( o.-) ✧",      # Stay right
        "( -.o) ✧",      # Look left
        "( -.o) ✧",      # Stay left
        "( o.o) ✧",      # Back to center
        "( ^.^) ✧",      # Happy/thinking
        "( ^.^) ✧",      # Stay happy
        "( o.o) ✧",      # Back to normal
        "( -.-) ✧",      # Eyes closed/thinking
        "( -.-) ✧",      # Keep thinking
        "( o.o) ✧",      # Open eyes
        "( o.O) ✧",      # Surprised/curious
        "( O.o) ✧",      # Other eye big
        "( o.o) ✧",      # Back to normal
        "( >.o) ✧",      # Squint right
        "( o.<) ✧",      # Squint left
        "( o.o) ✧",      # Normal
        "( @.@) ✧",      # Dizzy/processing
        "( @.@) ✧",      # Still processing
        "( o.o) ✧",      # Recovered
    ]
}

# Color scheme
COLORS = {
    "primary": "#3B82F6",     # Blue
    "secondary": "#8B5CF6",   # Purple
    "success": "#10B981",     # Green
    "error": "#EF4444",       # Red
    "warning": "#F59E0B",     # Amber
    "accent": "#EC4899",      # Pink
    "muted": "#6B7280",       # Gray
}

def create_header(title: str, subtitle: str = "") -> str:
    """Create a stylized header with arrow and spark."""
    header: str = f"[{COLORS['primary']}]{ARROW}[/] [bold]{title}[/bold] [{COLORS['accent']}]{SPARK}[/]"
    if subtitle:
        header += f"\n[dim]{subtitle}[/dim]"
    return header

def create_status(message: str, status: str = "info") -> str:
    """Create a status message with appropriate icon and color."""
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
    """Create a box header with key-value pairs."""
    lines: list[str] = [f"[{COLORS['primary']}]╭─[/] [bold]{title}[/bold]"]

    for key, value in items.items():
        lines.append(f"[{COLORS['primary']}]│[/] [dim]{key}:[/dim] [{COLORS['accent']}]{value}[/]")

    lines.append(f"[{COLORS['primary']}]╰─[/]")
    return "\n".join(lines)
