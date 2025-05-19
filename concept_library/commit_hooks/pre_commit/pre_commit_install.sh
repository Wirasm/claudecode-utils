#!/bin/bash
# Installer for ruff pre-commit hook

echo "Installing ruff pre-commit hook..."

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/pre_commit/pre_commit_ruff.py .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit

echo "✅ Hook installed successfully!"
echo "The hook will:"
echo "  - Run ruff on staged Python files before each commit"
echo "  - Prevent commits if linting errors are found"
echo "  - Suggest fixes with 'uv run ruff check --fix'"
echo ""
echo "To uninstall: rm .git/hooks/pre-commit"