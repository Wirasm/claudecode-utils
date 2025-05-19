#!/bin/bash
# Installer for minimal Claude Code post-push PR creation hook

echo "Installing minimal Claude Code post-push PR creation hook..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the hook to .git/hooks/
cp concept_library/commit_hooks/post_push/post_push_pr_creator.py .git/hooks/post-push

# Make it executable
chmod +x .git/hooks/post-push

echo "✅ Hook installed successfully!"
echo "This minimal implementation will:"
echo "  - Give Claude COMPLETE AUTONOMY to analyze pushed commits"
echo "  - Trust Claude to decide if a PR should be created"
echo "  - Allow Claude to generate rich PR descriptions"
echo "  - Use GitHub CLI to create PRs automatically"
echo "  - Report what actions were taken"
echo ""
echo "Note: Requires GitHub CLI (gh) to be installed and authenticated"
echo "To uninstall: rm .git/hooks/post-push"