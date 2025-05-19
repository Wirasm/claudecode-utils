#!/usr/bin/env python3
"""CLI interface for the Claude Code release tool using Typer."""

import typer

from .dylan_release_runner import generate_release_prompt, run_claude_release

# Create a separate app for release command to handle options better
release_app = typer.Typer()


@release_app.callback(invoke_without_command=True)
def release(
    patch: bool = typer.Option(False, "--patch", help="Patch version bump (default)"),
    minor: bool = typer.Option(False, "--minor", help="Minor version bump"),
    major: bool = typer.Option(False, "--major", help="Major version bump"),
    tag: bool = typer.Option(False, "--tag", help="Create git tag after release"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git operations"),
    tools: str = typer.Option(
        "Read,Write,Edit,Bash,LS,Glob", "--tools", help="Comma-separated list of allowed tools"
    ),
    format: str = typer.Option("text", "--format", help="Output format: text, json, stream-json"),
):
    """Create a new release with version bump and changelog update."""
    # Determine bump type
    if major:
        bump_type = "major"
    elif minor:
        bump_type = "minor"
    else:
        bump_type = "patch"  # Default

    # Parse tools
    allowed_tools = [tool.strip() for tool in tools.split(",")]

    # Generate prompt
    prompt = generate_release_prompt(
        bump_type=bump_type,
        create_tag=tag,
        dry_run=dry_run,
        no_git=no_git,
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
