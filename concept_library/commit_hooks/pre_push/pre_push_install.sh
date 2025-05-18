#!/bin/bash
# Installer for Claude Code pre-push version bump hook

echo "Installing Claude Code pre-push version bump hook..."

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/pre_push/pre_push_version_bump.py .git/hooks/pre-push

# Make it executable
chmod +x .git/hooks/pre-push

echo "✅ Hook installed successfully!"
echo "The hook will:"
echo "  - Check commits since last version tag"
echo "  - Generate semantic version bump (never major during development)"
echo "  - Update pyproject.toml and CHANGELOG.md"
echo "  - Exit to let you review and commit changes"
echo ""
echo "To uninstall: rm .git/hooks/pre-push"