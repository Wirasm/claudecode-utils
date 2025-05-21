"""Interactive session utilities for Claude interactions.

Shared utilities for running interactive sessions with the Claude provider.
"""

import sys

from rich.console import Console

from ..config import (
    CLAUDE_CODE_NPM_PACKAGE,
    CLAUDE_CODE_REPO_URL,
    GITHUB_ISSUES_URL,
)
from ..ui_theme import COLORS, create_status


def run_interactive_session(
    provider,
    prompt,
    allowed_tools,
    output_format,
    context_name="session",
    console=None,
):
    """Run an interactive session with the provider.

    Args:
        provider: The provider instance
        prompt: The initial prompt to send
        allowed_tools: List of allowed tools
        output_format: Output format
        context_name: Context-specific name (e.g., "PR", "release", "review")
        console: Rich console instance

    Returns:
        Result message from the session
    """
    if console is None:
        console = Console()

    console.print(f"[{COLORS['info']}]Entering interactive {context_name} session with Claude...[/]")
    console.print(f"[{COLORS['muted']}]The generated prompt will be sent as initial input.[/]")
    console.print(f"[{COLORS['muted']}]Type your messages directly to Claude below.[/]")
    console.print(f"[{COLORS['muted']}]Use Claude's exit command or Ctrl+D to end the session.[/]")
    console.print()

    try:
        result = provider.generate(
            prompt=prompt,
            allowed_tools=allowed_tools,
            output_format=output_format,
            interactive=True
        )
        console.print()
        console.print(create_status(result, "info"))
        console.print(f"[{COLORS['muted']}]Interactive {context_name} session concluded.[/]")
        return result
    except KeyboardInterrupt:
        console.print()
        console.print(create_status(f"Interactive {context_name} session terminated by user.", "warning"))
        return f"Interactive {context_name} session terminated by user."
    except RuntimeError as e:
        console.print()
        console.print(create_status(str(e), "error"))
        sys.exit(1)
    except FileNotFoundError:
        console.print()
        console.print(create_status("Claude Code not found!", "error"))
        console.print(f"\n[{COLORS['warning']}]Please install Claude Code:[/]")
        console.print(f"[{COLORS['muted']}]  npm install -g {CLAUDE_CODE_NPM_PACKAGE}[/]")
        console.print(f"\n[{COLORS['muted']}]For more info: {CLAUDE_CODE_REPO_URL}[/]")
        sys.exit(1)
    except Exception as e:
        console.print()
        console.print(create_status(f"Unexpected error during interactive session: {e}", "error"))
        console.print(f"\n[{COLORS['muted']}]Please report this issue at:[/]")
        console.print(f"[{COLORS['primary']}]{GITHUB_ISSUES_URL}[/]")
        sys.exit(1)
