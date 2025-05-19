#!/usr/bin/env python3
"""
Standalone pre-push hook using Claude Code - minimal wrapper, maximum trust.
This follows the concept library philosophy: minimal validation, let Claude handle everything.
"""

import subprocess
import sys


def call_claude(prompt: str, allowed_tools: list[str] | None = None) -> tuple[int, str]:
    """Call Claude Code with minimal wrapper - trust it to do everything."""
    # Default tools if none specified
    if allowed_tools is None:
        allowed_tools = ["Bash", "Read", "Write", "Edit", "LS", "Glob"]

    # Build command
    cmd = ["claude", "-p", prompt]

    # Add allowed tools
    if allowed_tools:
        cmd.extend(["--allowedTools"] + allowed_tools)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return 0, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or e.stderr or "").strip()


def generate_pre_push_prompt() -> str:
    """Generate prompt that gives Claude complete control over the pre-push process."""
    return """
You are a pre-push hook with COMPLETE AUTONOMY to analyze commits and update project files.

YOUR MISSION:
1. Discover what commits are being pushed
2. Analyze their impact
3. Update necessary files (version, changelog, etc.)
4. Ensure the project is ready for push

CRITICAL: You MUST complete these tasks WITHOUT asking for confirmation. Use all available tools to:

1. GIT ANALYSIS - Use Bash to:
   - Find the latest tag: git describe --tags --abbrev=0 (might fail if no tags)
   - Get current branch: git symbolic-ref --short HEAD
   - Find remote tracking branch: git rev-parse --abbrev-ref --symbolic-full-name @{u}
   - Get commits being pushed: git log origin/main..HEAD --pretty=format:"%h %s %b" (adjust for actual remote)
   - If no remote, get all commits: git log --pretty=format:"%h %s %b"
   - Check for uncommitted changes: git status --porcelain

2. VERSION MANAGEMENT:
   - Read pyproject.toml to find current version
   - Analyze commit messages for semantic versioning hints:
     - feat: → minor bump
     - fix:, docs:, chore: → patch bump
     - BREAKING CHANGE → major bump (We are still in development phase, so avoid major bumps unless speficied by the user)
   - Update version in pyproject.toml if needed

3. CHANGELOG UPDATES:
   - Read CHANGELOG.md
   - Create new section with today's date
   - Group changes by type (Added, Changed, Fixed, etc.)
   - Include commit hashes and messages
   - Format properly in Markdown

4. OPTIONAL CHECKS (if you detect they're needed):
   - Run tests if test files were modified
   - Update documentation if API changes detected
   - Check for TODOs or FIXMEs in changed files

REMEMBER:
- Work autonomously - make all decisions yourself
- Use proper git commands to get FULL context
- Update files directly with Write/Edit tools
- Report what you've done at the end

Go ahead and complete the entire pre-push workflow now.
"""


def run_pre_push_hook():
    """Execute the pre-push hook with minimal intervention."""
    print("🚀 Running pre-push hook with Claude Code...")

    # Generate the prompt
    prompt = generate_pre_push_prompt()

    # Call Claude and let it handle everything
    exit_code, output = call_claude(prompt)

    if exit_code != 0:
        print("⚠️ Claude Code encountered an issue:")
        print(output)
        # Don't block push on Claude errors
        sys.exit(0)

    # Show Claude's output
    print(output)

    # Check if any files were modified
    try:
        diff_result = subprocess.run(["git", "diff", "--quiet"], capture_output=True)
        if diff_result.returncode != 0:
            print("\n⚠️ Files were modified during pre-push hook.")
            print("Please review changes and commit before pushing:")
            print("  git add -A")
            print("  git commit -m 'chore: pre-push updates'")
            print("  git push")
            sys.exit(1)  # Block the push
    except Exception as e:
        print(f"Error checking git status: {e}")

    print("✅ Pre-push checks complete. Proceeding with push...")
    sys.exit(0)


if __name__ == "__main__":
    run_pre_push_hook()
