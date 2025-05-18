#!/usr/bin/env python3
"""
Test script for the prepare-commit-msg hook during development.

Usage:
    python concept_library/commit_hooks/test_hook.py
"""
import subprocess
import tempfile
import sys
from pathlib import Path

# Stage a test file change
test_file = Path("test_commit_hook.txt")
test_file.write_text("Testing commit hook\n")
subprocess.run(["git", "add", str(test_file)])

# Create a temporary commit message file
with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_COMMIT_MSG") as f:
    commit_msg_file = f.name
    f.write("")  # Empty initial message

# Run the hook
result = subprocess.run(
    [sys.executable, "concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg.py", commit_msg_file],
    capture_output=True,
    text=True
)

print(f"Hook exit code: {result.returncode}")
print(f"Hook stdout: {result.stdout}")
print(f"Hook stderr: {result.stderr}")

# Read the generated commit message
if Path(commit_msg_file).exists():
    commit_msg = Path(commit_msg_file).read_text()
    print(f"\nGenerated commit message:\n{commit_msg}")
    Path(commit_msg_file).unlink()  # Clean up

# Clean up test file
subprocess.run(["git", "reset", "HEAD", str(test_file)])
test_file.unlink(missing_ok=True)
