#!/bin/bash
# Installer for Claude Code pre-push hook (minimal autonomous version)

echo "Installing Claude Code pre-push hook (minimal autonomous version)..."

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/pre_push/pre_push_version_bump.py .git/hooks/pre-push

# Make it executable
chmod +x .git/hooks/pre-push

echo "✅ Hook installed successfully!"
echo "The hook will:"
echo "  - Give Claude COMPLETE AUTONOMY to analyze commits"
echo "  - Let Claude decide version bumps based on commit messages"
echo "  - Trust Claude to update CHANGELOG.md with proper formatting"
echo "  - Allow Claude to run additional checks if needed"
echo "  - Exit gracefully on errors (never block pushes)"
echo ""
echo "This is the minimal implementation that trusts Claude completely."
echo "To uninstall: rm .git/hooks/pre-push"