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
    def generate(
        self,
        prompt: str,
        *,
        output_path: str | None = None,
        allowed_tools: list[str] | None = None,
        output_format: str = "text",
    ) -> str:
        """Generate content using the provider.

        Args:
            prompt: The prompt to send to the provider
            output_path: Optional path to save output to (will be added to prompt)
            allowed_tools: Optional list of allowed tools
            output_format: Output format (text, json, stream-json)

        Returns:
            The generated content or confirmation message
        """
        ...


# ---------- Claude Code implementation ---------- #
class ClaudeProvider(Provider):
    _BIN: Final[str] = shutil.which("claude") or "claude"

    def generate(
        self,
        prompt: str,
        *,
        output_path: str | None = None,
        allowed_tools: list[str] | None = None,
        output_format: str = "text",
    ) -> str:
        """Generate content using Claude Code."""
        # Modify prompt if output path is specified
        if output_path:
            file_extension = os.path.splitext(output_path)[1].lower()
            if file_extension == ".json":
                file_directive = f"""

IMPORTANT: Generate the full report and save it directly to the file {output_path} using the Write tool WITHOUT asking for confirmation. Do not wait for user input before generating and saving the report. Ensure the output is valid JSON with proper escaping. Once you've saved the file, please confirm it was saved successfully."""
            else:
                file_directive = f"""

IMPORTANT: Generate the full report and save it directly to the file {output_path} using the Write tool WITHOUT asking for confirmation. Do not wait for user input before generating and saving the report. Once you've saved the file, please confirm it was saved successfully."""
            prompt = prompt + file_directive

        # Build command
        cmd = [self._BIN, "-p", prompt]

        # Add output format if not text
        if output_format != "text":
            cmd.extend(["--output-format", output_format])

        # Add allowed tools if specified
        if allowed_tools:
            cmd.extend(["--allowedTools"] + allowed_tools)

        # Check authentication
        if "CLAUDE_API_KEY" not in os.environ:
            print("Note: CLAUDE_API_KEY environment variable not set.", file=sys.stderr)
            print("      Using existing Claude Code authentication if available.", file=sys.stderr)
            print("      For Claude Code Max users this should work automatically.", file=sys.stderr)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Claude Code CLI not found. Install with:\n  npm i -g @anthropic-ai/claude-code"
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr or str(exc)
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
