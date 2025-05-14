#!/usr/bin/env -S uv run --script
"""Utility script to configure an allow‑list of Claude Code tools.

Usage (project-scoped):
    uv run python scripts/setup_tools.py          # writes .claude/settings.json

Usage (user-scoped):
    uv run python scripts/setup_tools.py --global # writes ~/.claude.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# --- default allow‑list -------------------------------------------------------
_DEFAULT_TOOLS: dict[str, dict[str, bool]] = {
    # Tools that ask for write‑permission.  Flag as safe so the model is not
    # blocked by interactive prompts every time it edits a file or runs a test.
    "Bash": {"allowed": True},
    "Edit": {"allowed": True},
    "MultiEdit": {"allowed": True},
    "Write": {"allowed": True},
    "NotebookEdit": {"allowed": True},
    "WebFetch": {"allowed": True},
    # Read‑only / low‑risk tools (kept for completeness—already allowed by
    # default, but being explicit avoids surprises if defaults change).
    "Agent": {"allowed": True},
    "Glob": {"allowed": True},
    "Grep": {"allowed": True},
    "LS": {"allowed": True},
    "Read": {"allowed": True},
    "NotebookRead": {"allowed": True},
    "TodoRead": {"allowed": True},
    "TodoWrite": {"allowed": True},
    "WebSearch": {"allowed": True},
}


# -----------------------------------------------------------------------------


def _config_path(project_scope: bool) -> Path:
    if project_scope:
        root = Path.cwd()
        cfg_dir = root / ".claude"
        cfg_dir.mkdir(exist_ok=True)
        return cfg_dir / "settings.json"
    # user‑scope
    return Path.home() / ".claude.json"


def setup_allowed_tools(project_scope: bool = True) -> None:
    """Write / update the Claude settings JSON with our allow‑list."""

    cfg_file = _config_path(project_scope)

    # Read existing config (ignore if malformed).
    existing: dict = {}
    if cfg_file.exists():
        try:
            existing = json.loads(cfg_file.read_text())
        except json.JSONDecodeError:
            pass

    existing.setdefault("allowedTools", {}).update(_DEFAULT_TOOLS)

    cfg_file.write_text(json.dumps(existing, indent=2))
    scope = "project" if project_scope else "global"
    print(
        f"✅  Updated {scope} Claude tool config → {cfg_file.relative_to(Path.home() if not project_scope else Path.cwd())}"
    )


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure Claude tool allow‑list.")
    parser.add_argument(
        "--global",
        dest="user_scope",
        action="store_true",
        help="Write to ~/.claude.json instead of project .claude/settings.json",
    )
    args = parser.parse_args()
    setup_allowed_tools(project_scope=not args.user_scope)
