"""Provider abstraction - only Claude Code is implemented in this POC.

Add a new class + update get_provider() when you want GPT/Gemini/Ollama.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Final

from ..shared.config import (
    CLAUDE_CODE_INSTALL_CMD,
    CLAUDE_CODE_NOT_FOUND_MSG,
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

    def stream_output(  # noqa: C901
        self,
        proc: subprocess.Popen,
        timeout: int | None = None,
        exit_command: str | None = None,
    ) -> Iterator[str]:
        """Stream output from a subprocess line by line with optional timeout.

        Args:
            proc: The subprocess.Popen process object
            timeout: Optional timeout in seconds for the entire process
            exit_command: Custom command to listen for to exit gracefully

        Yields:
            Lines of output from the process

        Raises:
            TimeoutError: If the process exceeds the timeout
            subprocess.CalledProcessError: If the process exits with a non-zero code
            KeyboardInterrupt: If the process is interrupted by user
        """
        start_time = time.time()

        try:
            # Check for user input if exit_command is specified and in stream mode
            if exit_command:
                import sys
                import threading

                exit_triggered = threading.Event()

                def input_listener():
                    """Listen for user input in a separate thread."""
                    while not exit_triggered.is_set():
                        try:
                            user_input = input()
                            if user_input.strip() == exit_command:
                                print(f"\nExit command '{exit_command}' detected. Shutting down...", file=sys.stderr)
                                exit_triggered.set()
                                # Send SIGINT to Claude process
                                proc.send_signal(signal.SIGINT)
                        except (EOFError, KeyboardInterrupt):
                            break
                        except Exception:  # noqa: S110
                            # Ignore other errors in the input thread - don't crash the daemon thread
                            # This is intentionally suppressed as the input thread is non-critical
                            pass

                # Start input listener thread if exit_command is specified
                input_thread = threading.Thread(target=input_listener, daemon=True)
                input_thread.start()

            # Main output streaming loop
            for line in proc.stdout:
                if timeout and (time.time() - start_time > timeout):
                    raise TimeoutError("Process exceeded timeout")

                # Check if exit was triggered in the input thread
                if exit_command and exit_triggered.is_set():
                    break

                yield line.strip()

        except (KeyboardInterrupt, SystemExit) as e:
            print("\nProcess interrupted by user. Attempting graceful shutdown...", file=sys.stderr)
            # First try SIGINT (like Ctrl+C) which Claude Code CLI handles specially
            proc.send_signal(signal.SIGINT)

            # Give it a few seconds to clean up
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Graceful shutdown timed out, terminating process...", file=sys.stderr)
                proc.terminate()  # SIGTERM
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Termination timed out, killing process...", file=sys.stderr)
                    proc.kill()  # SIGKILL

            raise KeyboardInterrupt() from e

    def generate(  # noqa: C901
        self,
        prompt: str,
        *,
        output_path: str | None = None,
        allowed_tools: list[str] | None = None,
        output_format: str = "text",
        timeout: int | None = None,
        stream: bool = False,
        exit_command: str | None = None,
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
        # Check if Claude is available
        if not self._BIN or self._BIN == "claude":
            claude_path = shutil.which("claude")
            if not claude_path:
                raise RuntimeError(CLAUDE_CODE_NOT_FOUND_MSG)

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
            # Use Popen instead of run for better control over the process
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            ) as proc:
                output_lines = []
                try:
                    # Stream output if requested, otherwise collect all lines
                    if stream:
                        for line in self.stream_output(proc, timeout, exit_command):
                            print(line)
                            output_lines.append(line)
                    else:
                        for line in self.stream_output(proc, timeout, exit_command if stream else None):
                            output_lines.append(line)

                except TimeoutError as e:
                    proc.send_signal(signal.SIGINT)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        try:
                            proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                    raise RuntimeError(f"Claude Code process timed out after {timeout} seconds") from e

                # Wait for the process to complete and check return code
                return_code = proc.wait()

                # Process stderr
                stderr = proc.stderr.read()

                # Handle return codes
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
    if name and name.lower() != "claude":
        raise ValueError(f"Unknown provider '{name}'. Only 'claude' supported in POC.")
    return ClaudeProvider()
