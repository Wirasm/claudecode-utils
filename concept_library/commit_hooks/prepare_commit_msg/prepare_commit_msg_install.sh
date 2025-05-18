#!/bin/bash
# Simple installer for Claude Code prepare-commit-msg hook

echo "Installing Claude Code prepare-commit-msg hook..."

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg.py .git/hooks/prepare-commit-msg

# Make it executable
chmod +x .git/hooks/prepare-commit-msg

echo "✅ Hook installed successfully!"
echo "Now your commits will use Claude Code to generate conventional commit messages."
echo ""
echo "To uninstall: rm .git/hooks/prepare-commit-msg"