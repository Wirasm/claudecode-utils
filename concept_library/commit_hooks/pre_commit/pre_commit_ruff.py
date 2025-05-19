#!/usr/bin/env python3
"""
pre-commit hook - Run ruff linter before commits
Prevents commits with linting errors
"""

import subprocess
import sys


def run_ruff():
    """Run ruff check on staged Python files"""
    # Get list of staged Python files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True
    )

    # Filter for Python files
    python_files = [f for f in result.stdout.splitlines() if f.endswith(".py")]

    if not python_files:
        return 0  # No Python files to check

    print("Running ruff on staged Python files...")

    # Run ruff check
    ruff_result = subprocess.run(["uv", "run", "ruff", "check"] + python_files, capture_output=True, text=True)

    if ruff_result.returncode != 0:
        print("❌ Ruff found issues:")
        print(ruff_result.stdout)
        if ruff_result.stderr:
            print(ruff_result.stderr)
        print("\nFix these issues before committing, or run:")
        print("  uv run ruff check --fix")
        return 1

    print("✅ Ruff check passed")
    return 0


if __name__ == "__main__":
    sys.exit(run_ruff())
