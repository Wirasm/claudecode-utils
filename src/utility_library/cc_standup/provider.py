"""
Provider abstraction - only Claude Code is implemented in this POC.
Add a new class + update get_provider() when you want GPT/Gemini/Ollama.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
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
        if "CLAUDE_API_KEY" not in os.environ:
            raise RuntimeError("CLAUDE_API_KEY not set - export your key before running.")

        cmd = [self._BIN, "-p", prompt, "--output-format", "text"]
        try:
            return subprocess.check_output(cmd, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Claude Code CLI not found. Install with:\n  npm i -g @anthropic-ai/claude-code"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Claude Code returned non-zero exit:\n{exc.stderr}") from exc


def get_provider(name: str | None = None) -> Provider:
    """Factory - returns a Provider instance. Only 'claude' for now."""
    if name and name.lower() not in {"claude", "anthropic"}:
        raise ValueError(f"Unknown provider '{name}'. Only 'claude' supported in POC.")
    return ClaudeProvider()
