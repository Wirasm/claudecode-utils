"""Provider abstraction - only Claude Code is implemented in this POC.

Add a new class + update get_provider() when you want GPT/Gemini/Ollama.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Final


class Provider(ABC):
    """Minimal LLM provider interface."""

    @abstractmethod
    def generate(self, prompt: str) -> str: ...


# ---------- Claude Code implementation ---------- #
class ClaudeProvider(Provider):
    _BIN: Final[str] = shutil.which("claude") or "claude"

    def generate(self, prompt: str) -> str:
        """Generate markdown for standup report using Claude."""
        # Build command with standard options
        cmd = [self._BIN, "-p", prompt, "--output-format", "text"]

        # We don't strictly require CLAUDE_API_KEY if user has Claude Code Max
        # subscription, which is authenticated via OAuth
        if "CLAUDE_API_KEY" not in os.environ:
            print("Note: CLAUDE_API_KEY environment variable not set.", file=sys.stderr)
            print("      Using existing Claude Code authentication if available.", file=sys.stderr)
            print(
                "      For Claude Code Max users this should work automatically.", file=sys.stderr
            )

        try:
            return subprocess.check_output(cmd, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Claude Code CLI not found. Install with:\n  npm i -g @anthropic-ai/claude-code"
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_msg = getattr(exc, "stderr", None) or str(exc)
            if "CLAUDE_API_KEY" not in os.environ:
                return self._handle_auth_error(error_msg)
            raise RuntimeError(f"Claude Code returned non-zero exit:\n{error_msg}") from exc

    def generate_and_save(self, prompt: str, output_path: str) -> str:
        """Generate markdown for standup report and save it directly to a file."""
        # Modify the prompt to instruct Claude to write the file
        file_directive = f"\n\nIMPORTANT: Generate the full Markdown standup report and save it directly to the file {output_path} using the Write tool WITHOUT asking for confirmation. Do not wait for user input before generating and saving the report. Once you've saved the file, please confirm it was saved successfully."
        modified_prompt = prompt + file_directive

        # We don't strictly require CLAUDE_API_KEY if user has Claude Code Max
        # subscription, which is authenticated via OAuth
        if "CLAUDE_API_KEY" not in os.environ:
            print("Note: CLAUDE_API_KEY environment variable not set.", file=sys.stderr)
            print("      Using existing Claude Code authentication if available.", file=sys.stderr)
            print(
                "      For Claude Code Max users this should work automatically.", file=sys.stderr
            )

        try:
            # Run Claude with the prompt - use text mode to get the response directly
            cmd = [self._BIN, "-p", modified_prompt]

            # Execute Claude Code with the prompt
            return subprocess.check_output(cmd, text=True)

        except FileNotFoundError as exc:
            raise RuntimeError(
                "Claude Code CLI not found. Install with:\n  npm i -g @anthropic-ai/claude-code"
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_msg = getattr(exc, "stderr", None) or str(exc)
            if "CLAUDE_API_KEY" not in os.environ:
                return self._handle_auth_error(error_msg)
            raise RuntimeError(f"Claude Code returned non-zero exit:\n{error_msg}") from exc

    def _handle_auth_error(self, error_msg: str) -> str:
        """Handle authentication errors with helpful suggestions."""
        auth_error = (
            "Authentication failed. You need to either:\n"
            "1. Set the CLAUDE_API_KEY environment variable, or\n"
            "2. Make sure you're logged in with 'claude /login' if using Claude Code Max.\n\n"
            "For Claude Max subscribers: In a separate terminal, run 'claude' and complete\n"
            "the authentication process before running this tool again.\n\n"
            "For API users: Export your key with: export CLAUDE_API_KEY=your_key_here"
        )

        # If authentication failed, we return a Markdown formatted report
        # that explains the issue instead of hard failing
        return f"""# ⚠️ Authentication Error

{auth_error}

## Debugging Information
```
{error_msg}
```

## Example Stand-up Report (Mock)
Your stand-up report would typically appear here after authentication.

### Yesterday
- Worked on feature X
- Fixed bug Y

### Today
- Continue implementation of Z
- Code review for PR #123

### Blockers
- None currently
"""


def get_provider(name: str | None = None) -> Provider:
    """Factory - returns a Provider instance. Only 'claude' for now."""
    if name and name.lower() not in {"claude", "anthropic"}:
        raise ValueError(f"Unknown provider '{name}'. Only 'claude' supported in POC.")
    return ClaudeProvider()
