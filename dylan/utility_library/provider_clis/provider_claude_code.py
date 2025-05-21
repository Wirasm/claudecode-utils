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
        # If no output path is specified, trust the prompt to handle file saving
        if not output_path:
            # Ensure the tmp directory exists
            tmp_directive = """
IMPORTANT: Make sure to create the tmp/ directory if it doesn't exist: mkdir -p tmp
"""
            return prompt + tmp_directive

        # If an output path is specified, add it to the prompt
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
        prompt: str | None = None,  # Prompt is optional for interactive mode
        output_format: str = "text",
        allowed_tools: list[str] | None = None,
        interactive: bool = False,
    ) -> list[str]:
        """Build the command to run Claude Code CLI.

        Args:
            prompt: The prompt to send to the provider (for non-interactive)
            output_format: Output format (text, json, stream-json) (for non-interactive)
            allowed_tools: Optional list of allowed tools
            interactive: Whether to build command for interactive mode

        Returns:
            Command as list of strings
        """
        if interactive:
            cmd = [self._BIN]
            if allowed_tools:
                cmd.extend(["--allowedTools"] + allowed_tools)
            return cmd

        # Non-interactive mode
        if prompt is None:
            raise ValueError("Prompt cannot be None for non-interactive mode.")
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
        interactive: bool = False,
    ) -> str:
        """Generate content using Claude Code with proper interrupt handling.

        Args:
            prompt: The prompt to send to the provider
            output_path: Optional path to save output to (will be added to prompt)
            allowed_tools: Optional list of allowed tools
            output_format: Output format (text, json, stream-json)
            timeout: Optional timeout in seconds (for non-interactive mode)
            stream: Whether to stream output (for non-interactive use)
            exit_command: Custom command to gracefully exit (for non-interactive mode)
            interactive: Whether to run in interactive mode

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

        if interactive:
            print("Entering interactive Claude session...", file=sys.stderr)
            # output_path, output_format, timeout, stream, exit_command are ignored in interactive mode
            # _prepare_prompt is also skipped
            cmd = self._build_command(
                prompt=None,  # Prompt is not part of the command itself for interactive
                allowed_tools=allowed_tools,
                interactive=True,
            )
            try:
                process_input = prompt.encode() if prompt else None
                # For interactive mode, claude takes over stdin/stdout/stderr
                # We send the initial prompt (if any) via stdin.
                result = subprocess.run(cmd, input=process_input) # No check=True, handle return code manually
                
                if result.returncode != 0:
                    # Users can exit claude with Ctrl+D (EOF) which might result in a non-zero code.
                    # Or they might use a command like /quit.
                    # We don't want to raise an error for normal interactive exits.
                    # However, if claude crashes, this might indicate an issue.
                    # For now, we'll just print a message if returncode is non-zero.
                    print(f"Claude interactive session exited with code {result.returncode}.", file=sys.stderr)
                return "Interactive session ended."
            except KeyboardInterrupt:
                # subprocess.run handles SIGINT by terminating the child and then re-raising.
                print("\nInteractive Claude session terminated by user.", file=sys.stderr)
                # No need to manually terminate proc, subprocess.run does this.
                raise # Re-raise KeyboardInterrupt
            except FileNotFoundError as exc: # Should be caught by the check above, but as a safeguard
                raise RuntimeError(
                    f"Claude Code CLI not found. Install with:\n  {CLAUDE_CODE_INSTALL_CMD}"
                ) from exc
            except Exception as e: # Catch any other unexpected errors during interactive session
                raise RuntimeError(f"Error during interactive Claude session: {e}") from e
        else:
            # Existing non-interactive logic
            is_using_api_key = "CLAUDE_API_KEY" in os.environ

            prepared_prompt = self._prepare_prompt(prompt, output_path)
            cmd = self._build_command(
                prepared_prompt, output_format, allowed_tools, interactive=False
            )

            if is_using_api_key:
                print("Using Claude API key for authentication...", file=sys.stderr)
            else:
                print("Using Claude Code Max subscription...", file=sys.stderr)

            try:
                with subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                ) as proc:
                    output_lines = []
                    from ..shared.exit_command import setup_exit_command_handler
                    exit_triggered = setup_exit_command_handler(proc, exit_command if stream else None)

                    try:
                        if stream:
                            for line in stream_process_output(proc, timeout, None):
                                print(line)
                                output_lines.append(line)
                                if exit_triggered.is_set():
                                    break
                        else:
                            if proc.stdout:
                                for line in proc.stdout:
                                    output_lines.append(line.strip())
                                    if exit_triggered.is_set():
                                        break
                    except TimeoutError as e:
                        terminate_process(proc)
                        raise RuntimeError(f"Claude Code process timed out after {timeout} seconds") from e

                    return_code = proc.wait()
                    stderr_output = proc.stderr.read() if proc.stderr else ""
                    return self._handle_process_result(return_code, output_lines, stderr_output)

            except FileNotFoundError as exc:
                raise RuntimeError(
                    f"Claude Code CLI not found. Install with:\n  {CLAUDE_CODE_INSTALL_CMD}"
                ) from exc
            except subprocess.CalledProcessError as exc: # Should be less likely with Popen
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
