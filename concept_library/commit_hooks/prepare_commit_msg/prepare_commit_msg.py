#!/usr/bin/env python3
"""
Minimal prepare-commit-msg hook using Claude Code - maximum trust approach.
Follows concept library philosophy: let Claude handle everything with minimal wrapper.
"""

import subprocess
import sys
from pathlib import Path

# Git provides these arguments
MSG_FILE = sys.argv[1]
COMMIT_SOURCE = sys.argv[2] if len(sys.argv) > 2 else ""

# Skip for merge/squash commits
if COMMIT_SOURCE in {"merge", "squash"}:
    sys.exit(0)


def call_claude(prompt: str) -> tuple[int, str]:
    """Call Claude Code with minimal wrapper - trust it completely."""
    cmd = ["claude", "-p", prompt, "--allowedTools", "Bash", "Read"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return 0, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or e.stderr or "").strip()


def generate_commit_prompt() -> str:
    """Generate prompt that gives Claude full control over commit message generation."""
    return """
You are a commit message generator with COMPLETE AUTONOMY.

YOUR MISSION:
1. Analyze the staged changes using git diff --cached
2. Generate a perfect conventional commit message
3. Return ONLY the commit message - no explanations

CRITICAL: Use Bash to get the full staged diff and do a quick analysis to get an understanding of changes.

COMMIT MESSAGE REQUIREMENTS:
- Format: type(scope?): description
- Type must be one of: feat, fix, docs, style, refactor, test, chore, build, ci, perf
- Description: imperative mood, lowercase, no period, ≤72 chars
- Include body if needed (what + why)
- Add "BREAKING CHANGE:" footer if applicable

STEPS:
1. Use: git diff --cached --unified=3
2. Analyze the changes thoroughly
3. Determine the primary type of change
4. Identify the scope if clear
5. Write a concise, meaningful description
6. Add body if changes are complex
7. Check for breaking changes

RETURN: Only the formatted commit message, nothing else.
"""


def main():
    """Execute the prepare-commit-msg hook with minimal intervention."""
    # Generate prompt
    prompt = generate_commit_prompt()

    # Call Claude
    exit_code, message = call_claude(prompt)

    if exit_code != 0 or not message:
        # Don't block commits on errors
        print("⚠️ Claude couldn't generate commit message - proceeding without")
        sys.exit(0)

    # Write the message
    Path(MSG_FILE).write_text(message + "\n")

    # Print the message to terminal for user visibility
    print("✅ Claude generated commit message:")
    print("─" * 50)
    print(message)
    print("─" * 50)

    sys.exit(0)


if __name__ == "__main__":
    main()
