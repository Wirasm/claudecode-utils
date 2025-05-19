"""Shared UI theme and styling for Dylan CLI."""


# Colors and symbols
ARROW = "❯"
SPARK = "✧"
CHECK = "✓"
CROSS = "✗"
SPINNER = "◍"

# Dylan's thinking spinner frames - ASCII art faces looking around
DYLAN_SPINNER = {
    "interval": 150,
    "frames": [
        "( o.o) ✧",
        "( o.-)  ✧",
        "( -.o)   ✧",
        "( -.-) ⋄   ✧",
        "(o.-')  •  ✧",
        "(o.o )   •  ✧",
        "('-.o)    • ✧",
        "(-.-)     ⋄ ✧",
        "( o.o)     • ✧",
        "( o.-)    • ✧",
        "( -.o)   • ✧",
        "( -.-)  ⋄ ✧",
        "(o.-') • ✧",
        "(o.o ) • ✧",
        "('-.o) • ✧",
        "( -.-) ✧",
        "( o.o) ✧",
        "( >.o) ✧",
        "( o.<) ✧",
        "( ^.^) ✧",
        "( o.~) ✧",
        "( ~.o) ✧",
        "( 0.0) ✧",
        "( o.O) ✧",
        "( O.o) ✧",
        "( @.@) ✧",
        "( *.o) ✧",
        "( o.*) ✧",
        "( ^_^) ✧",
        "( -_-) ✧",
        "( o_o) ✧",
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
    header = f"[{COLORS['primary']}]{ARROW}[/] [bold]{title}[/bold] [{COLORS['accent']}]{SPARK}[/]"
    if subtitle:
        header += f"\n[dim]{subtitle}[/dim]"
    return header

def create_status(message: str, status: str = "info") -> str:
    """Create a status message with appropriate icon and color."""
    icons = {
        "success": f"[{COLORS['success']}]{CHECK}[/]",
        "error": f"[{COLORS['error']}]{CROSS}[/]",
        "working": f"[{COLORS['primary']}]{SPINNER}[/]",
        "info": f"[{COLORS['muted']}]•[/]",
    }

    icon = icons.get(status, icons["info"])
    color = COLORS.get(status, COLORS["primary"])

    return f"{icon} [{color}]{message}[/]"

def create_box_header(title: str, items: dict) -> str:
    """Create a box header with key-value pairs."""
    lines = [f"[{COLORS['primary']}]╭─[/] [bold]{title}[/bold]"]

    for key, value in items.items():
        lines.append(f"[{COLORS['primary']}]│[/] [dim]{key}:[/dim] [{COLORS['accent']}]{value}[/]")

    lines.append(f"[{COLORS['primary']}]╰─[/]")
    return "\n".join(lines)
