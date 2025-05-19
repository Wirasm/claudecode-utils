#!/usr/bin/env python3
"""
prepare-commit-msg — AI Conventional Commit writer (Max-plan-aware)

This hook generates conventional commit messages using Claude Code by analyzing
staged changes. Works with both Max OAuth and API key authentication.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

# Git provides these arguments to the hook
MSG_FILE = sys.argv[1]
COMMIT_SOURCE = sys.argv[2] if len(sys.argv) > 2 else ""

# Skip for merge/squash commits
if COMMIT_SOURCE in {"merge", "squash"}:
    sys.exit(0)

# 1️⃣ Get staged diff
diff = subprocess.run(
    ["git", "diff", "--cached", "--unified=0"],
    text=True, capture_output=True, check=True
).stdout

if not diff.strip():
    sys.exit(0)

# 2️⃣ Build prompt
prompt = textwrap.dedent(f"""
    You are an expert release engineer. From the staged diff below,
    output *only* a Conventional Commit message:
      type(scope?): description  ← ≤72 chars, imperative
      blank line
      wrapped body (what + why)
      optional "BREAKING CHANGE:" footer
    Allowed types: feat, fix, docs, style, refactor, test, chore.
    Diff:
    ```diff
    {diff}
    ```
""").strip()

def call_claude():
    return subprocess.run(
        ["claude", "-p", "--max-turns", "3", prompt],
        text=True, capture_output=True
    )

# 3️⃣ First try (cached Max token or last-used auth)
result = call_claude()

# 4️⃣ On auth failure, retry if an API key is available
if result.returncode != 0 and os.getenv("ANTHROPIC_API_KEY"):
    env = os.environ.copy()
    env["CLAUDE_AUTH"] = "api-key"  # force API path
    result = subprocess.run(
        ["claude", "-p", "--max-turns", "3", prompt],
        text=True, capture_output=True, env=env
    )

# 5️⃣ If still failing, bail but don't block commit
if result.returncode != 0 or not result.stdout.strip():
    sys.exit(0)

Path(MSG_FILE).write_text(result.stdout.strip() + "\n")
print("✔ Claude Code wrote commit message")
