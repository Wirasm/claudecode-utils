#!/bin/bash
# Installer for minimal Claude Code prepare-commit-msg hook

echo "Installing minimal Claude Code prepare-commit-msg hook..."

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/prepare_commit_msg/prepare_commit_msg.py .git/hooks/prepare-commit-msg

# Make it executable
chmod +x .git/hooks/prepare-commit-msg

echo "✅ Hook installed successfully!"
echo "This minimal implementation will:"
echo "  - Give Claude COMPLETE AUTONOMY to analyze staged changes"
echo "  - Trust Claude to generate perfect conventional commits"
echo "  - Print the generated message to your terminal"
echo "  - Never block commits on errors"
echo ""
echo "To uninstall: rm .git/hooks/prepare-commit-msg"