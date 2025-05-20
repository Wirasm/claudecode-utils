#!/usr/bin/env python3
"""CLI interface for the Claude Code release tool using Typer."""

import typer
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
    format_tool_count,
)
from .dylan_release_runner import generate_release_prompt, run_claude_release

console = Console()

# Create a separate app for release command to handle options better
release_app = typer.Typer()


@release_app.callback(invoke_without_command=True)
def release(
    major: bool = typer.Option(False, "--major", help="Bump major version (X.0.0)"),
    minor: bool = typer.Option(False, "--minor", help="Bump minor version (0.X.0)"),
    patch: bool = typer.Option(False, "--patch", help="Bump patch version (0.0.X)"),
    tag: bool = typer.Option(False, "--tag", help="Create git tag for the release"),
    merge_strategy: str = typer.Option(
        "direct", "--merge-strategy", help="Merge strategy: direct, pr, or none"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't make actual changes"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git operations"),
    tools: str = typer.Option(
        "Read,Bash,Write,Glob,Grep", "--tools", help="Comma-separated list of allowed tools"
    ),
    format: str = typer.Option("text", "--format", help="Output format: text, json, stream-json"),
):
    """Create a new release with version bump and changelog update."""
    # Parse tools first
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Determine bump type
    if major:
        bump_type = "major"
    elif minor:
        bump_type = "minor"
    else:
        bump_type = "patch"  # Default

    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "Release Management"))
    console.print()

    # Show release configuration
    console.print(create_box_header("Release Configuration", {
        "Version Bump": bump_type.capitalize(),
        "Tag": format_boolean_option(tag, "✓ Create tag", "✗ No tag"),
        "Strategy": merge_strategy,
        "Mode": "🔍 Dry run" if dry_run else "🚀 Live run",
        "Git Operations": format_boolean_option(not no_git, "✓ Enabled", "✗ Disabled"),
        "Tools": format_tool_count(allowed_tools)
    }))
    console.print()

    # Generate prompt
    prompt = generate_release_prompt(
        bump_type=bump_type,
        create_tag=tag,
        dry_run=dry_run,
        no_git=no_git,
        merge_strategy=merge_strategy,
        output_format=format
    )

    # Run release
    run_claude_release(prompt, allowed_tools=allowed_tools, output_format=format)


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    release_app()


if __name__ == "__main__":
    main()
