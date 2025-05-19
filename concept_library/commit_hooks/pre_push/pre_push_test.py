#!/usr/bin/env python3
"""
Test script for the pre-push version bump hook during development.

Usage:
    python concept_library/commit_hooks/pre_push/pre_push_test.py
"""

import subprocess
import sys

# Run the hook in test mode
print("Testing pre-push version bump hook...")
print("-" * 40)

# Run the hook directly
result = subprocess.run(
    [sys.executable, "concept_library/commit_hooks/pre_push/pre_push_version_bump.py"], capture_output=True, text=True
)

print(f"Exit code: {result.returncode}")
print(f"Output:\n{result.stdout}")
if result.stderr:
    print(f"Errors:\n{result.stderr}")

# Check if any files were modified
diff_result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
if diff_result.stdout:
    print("\nModified files:")
    print(diff_result.stdout)

    # Show the diff
    diff_content = subprocess.run(["git", "diff"], capture_output=True, text=True)
    print("\nChanges:")
    print(diff_content.stdout)
