"""Shared utilities for Dylan CLI."""

from .error_handling import handle_dylan_errors
from .progress import create_dylan_progress, create_task_with_dylan
from .ui_theme import (
    ARROW,
    CHECK,
    COLORS,
    CROSS,
    SPARK,
    SPINNER,
    create_box_header,
    create_header,
    create_status,
    format_boolean_option,
    format_tool_count,
)

__all__ = [
    # Error handling
    "handle_dylan_errors",
    # Progress
    "create_dylan_progress",
    "create_task_with_dylan",
    # UI theme symbols
    "ARROW",
    "CHECK",
    "COLORS",
    "CROSS",
    "SPARK",
    "SPINNER",
    # UI theme functions
    "create_box_header",
    "create_header",
    "create_status",
    "format_boolean_option",
    "format_tool_count",
]
