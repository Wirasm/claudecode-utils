#!/usr/bin/env python3
"""CLI interface for the Claude Code release tool using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
)
from .dylan_release_runner import generate_release_prompt, run_claude_release

console = Console()

# Create a separate app for release command to handle options better
release_app = typer.Typer()


@release_app.callback(invoke_without_command=True)
def release(
    bump_type: str = typer.Option(
        "patch",
        "--bump",
        "-b",
        help="Version bump type: 'patch' (0.0.X), 'minor' (0.X.0), or 'major' (X.0.0)",
        show_default=True,
    ),
    tag: bool = typer.Option(False, "--tag", help="Create git tag after release"),
    mode: str = typer.Option(
        "live",
        "--mode",
        "-m",
        help="Mode: 'live' (create release), 'dry-run' (preview only), or 'no-git' (skip git operations)",
        show_default=True,
    ),
    merge_strategy: str = typer.Option(
        "direct", "--merge-strategy", help="Merge strategy: 'direct' or 'pr' (default: direct)"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print debug information (including the full prompt)",
        show_default=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive chat mode with Claude for release management.",
        show_default=True,
    )
):
    """Create a new release with version bump and changelog update."""
    # Default values
    allowed_tools = ["Read", "Write", "Edit", "Bash", "LS", "Glob", "MultiEdit", "TodoRead", "TodoWrite"]
    output_format = "text"

    # Validate bump_type
    if bump_type not in ["patch", "minor", "major"]:
        console.print(f"Invalid bump type: {bump_type}. Using 'patch' instead.", style="warning")
        bump_type = "patch"

    # Parse mode
    dry_run = mode == "dry-run"
    no_git = mode == "no-git"

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Release Management"))
    console.print()

    # Show release configuration
    console.print(create_box_header("Release Configuration", {
        "Version Bump": bump_type.capitalize(),
        "Tag": format_boolean_option(tag, "✓ Create tag", "✗ No tag"),
        "Strategy": merge_strategy,
        "Mode": "🔍 Dry run" if dry_run else "⚠️ No git" if no_git else "🚀 Live run",
        "Interactive Mode": format_boolean_option(interactive, "✓ Enabled", "✗ Disabled"),
        "Debug": format_boolean_option(debug, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt"
    }))
    console.print()

    # Generate prompt
    # For interactive mode, this will be the initial prompt sent to Claude.
    prompt = generate_release_prompt(
        bump_type=bump_type,
        create_tag=tag,
        dry_run=dry_run,
        no_git=no_git,
        merge_strategy=merge_strategy,
        output_format=output_format
    )

    # Run release
    run_claude_release(
        prompt,
        allowed_tools=allowed_tools,
        output_format=output_format,
        debug=debug,
        interactive=interactive
    )


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    release_app()


if __name__ == "__main__":
    main()
