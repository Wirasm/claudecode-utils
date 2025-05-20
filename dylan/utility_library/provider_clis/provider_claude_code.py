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

from ..shared.config import (
    CLAUDE_CODE_INSTALL_CMD,
    CLAUDE_CODE_NOT_FOUND_MSG,
)
from ..shared.exit_command import DEFAULT_EXIT_COMMAND
from .shared.subprocess_utils import (
    stream_process_output,
    terminate_process,
)


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

    def _prepare_prompt(self, prompt: str, output_path: str | None = None) -> str:
        """Prepare prompt with output path directive if needed.

        Args:
            prompt: The prompt to send to the provider
            output_path: Optional path to save output to

        Returns:
            The prepared prompt
        """
        if not output_path:
            return prompt

        file_extension = os.path.splitext(output_path)[1].lower()
        if file_extension == ".json":
            file_directive = f"""

IMPORTANT: Generate the full report and save it directly to the file {output_path} using the Write tool WITHOUT asking for confirmation. Do not wait for user input before generating and saving the report. Ensure the output is valid JSON with proper escaping. Once you've saved the file, please confirm it was saved successfully."""
        else:
            file_directive = f"""

IMPORTANT: Generate the full report and save it directly to the file {output_path} using the Write tool WITHOUT asking for confirmation. Do not wait for user input before generating and saving the report. Once you've saved the file, please confirm it was saved successfully."""
        return prompt + file_directive

    def _build_command(
        self,
        prompt: str,
        output_format: str = "text",
        allowed_tools: list[str] | None = None,
    ) -> list[str]:
        """Build the command to run Claude Code CLI.

        Args:
            prompt: The prompt to send to the provider
            output_format: Output format (text, json, stream-json)
            allowed_tools: Optional list of allowed tools

        Returns:
            Command as list of strings
        """
        cmd = [self._BIN, "-p", prompt]

        # Add output format if not text
        if output_format != "text":
            cmd.extend(["--output-format", output_format])

        # Add allowed tools if specified
        if allowed_tools:
            cmd.extend(["--allowedTools"] + allowed_tools)

        return cmd

    def _handle_process_result(
        self,
        return_code: int,
        output_lines: list[str],
        stderr: str,
    ) -> str:
        """Handle the result of the Claude Code process.

        Args:
            return_code: The process return code
            output_lines: The collected output lines
            stderr: The standard error output

        Returns:
            The final output or error message

        Raises:
            KeyboardInterrupt: If the process was interrupted
            RuntimeError: If the process encountered an error
        """
        if return_code == 0:
            return "\n".join(output_lines)
        elif return_code == 130:  # SIGINT (Ctrl+C)
            print("Process was interrupted by user", file=sys.stderr)
            raise KeyboardInterrupt()
        else:
            error_msg = stderr or f"Process exited with code {return_code}"
            if "CLAUDE_API_KEY" not in os.environ:
                return self._handle_auth_error(error_msg)
            raise RuntimeError(f"Claude Code returned non-zero exit:\n{error_msg}")

    def generate(
        self,
        prompt: str,
        *,
        output_path: str | None = None,
        allowed_tools: list[str] | None = None,
        output_format: str = "text",
        timeout: int | None = None,
        stream: bool = False,
        exit_command: str | None = DEFAULT_EXIT_COMMAND,
    ) -> str:
        """Generate content using Claude Code with proper interrupt handling.

        Args:
            prompt: The prompt to send to the provider
            output_path: Optional path to save output to (will be added to prompt)
            allowed_tools: Optional list of allowed tools
            output_format: Output format (text, json, stream-json)
            timeout: Optional timeout in seconds
            stream: Whether to stream output (for interactive use)
            exit_command: Custom command to gracefully exit (e.g., "/exit" or "/quit")

        Returns:
            The generated content or confirmation message

        Raises:
            RuntimeError: If Claude Code CLI is not found or returns an error
            KeyboardInterrupt: If the process is interrupted
        """
        # Check if Claude is available and display appropriate message
        if not self._BIN or self._BIN == "claude":
            claude_path = shutil.which("claude")
            if not claude_path:
                raise RuntimeError(CLAUDE_CODE_NOT_FOUND_MSG)

        # Determine authentication method
        is_using_api_key = "CLAUDE_API_KEY" in os.environ

        # Prepare prompt and command
        prepared_prompt = self._prepare_prompt(prompt, output_path)
        cmd = self._build_command(prepared_prompt, output_format, allowed_tools)

        # Show authentication method in use
        if is_using_api_key:
            print("Using Claude API key for authentication...", file=sys.stderr)
        else:
            print("Using Claude Code Max subscription...", file=sys.stderr)

        try:
            # Use Popen instead of run for better control over the process
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            ) as proc:
                output_lines = []
                # Set up exit command listener but only in streaming mode
                # In non-streaming mode, users should use Ctrl+C to interrupt
                from ..shared.exit_command import setup_exit_command_handler
                exit_triggered = setup_exit_command_handler(proc, exit_command if stream else None)

                try:
                    # Stream output if requested, otherwise collect all lines
                    if stream:
                        for line in stream_process_output(proc, timeout, None):  # No exit command here, already set up
                            print(line)
                            output_lines.append(line)
                            if exit_triggered.is_set():
                                break
                    else:
                        # For non-streaming mode, still use a loop to check exit_triggered
                        if proc.stdout:
                            for line in proc.stdout:
                                output_lines.append(line.strip())
                                if exit_triggered.is_set():
                                    break

                except TimeoutError as e:
                    terminate_process(proc)
                    raise RuntimeError(f"Claude Code process timed out after {timeout} seconds") from e

                # Wait for the process to complete and check return code
                return_code = proc.wait()
                stderr = proc.stderr.read() if proc.stderr else ""

                # Handle return code and produce final output
                return self._handle_process_result(return_code, output_lines, stderr)

        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Claude Code CLI not found. Install with:\n  {CLAUDE_CODE_INSTALL_CMD}"
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
            "1. Have an active Claude Code Max subscription, or\n"
            "2. Set the CLAUDE_API_KEY environment variable\n\n"
            "For Claude Max subscribers: Run 'claude /login' in a terminal and complete\n"
            "the authentication process before running this tool again.\n\n"
            "For API users: Add your key to .env file or export with: export CLAUDE_API_KEY=your_key_here"
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
    if name and name.lower() != "claude":
        raise ValueError(f"Unknown provider '{name}'. Only 'claude' supported in POC.")
    return ClaudeProvider()
