#!/usr/bin/env python3
"""
Minimal post-push hook using Claude Code - automatic PR creation.
Follows concept library philosophy: let Claude handle everything with minimal wrapper.
"""
import subprocess
import sys


def call_claude(prompt: str, allowed_tools: list[str] | None = None) -> tuple[int, str]:
    """Call Claude Code with minimal wrapper - trust it completely."""
    if allowed_tools is None:
        allowed_tools = ["Bash", "Read", "Write", "Edit", "LS", "Glob"]

    cmd = ["claude", "-p", prompt, "--allowedTools"] + allowed_tools

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return 0, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or e.stderr or "").strip()


def generate_pr_prompt() -> str:
    """Generate prompt that gives Claude complete control over PR creation."""
    return """
You are a PR creator with COMPLETE AUTONOMY to analyze pushed commits and create pull requests.

YOUR MISSION:
1. Determine current branch and remote configuration
2. Analyze all pushed commits
3. Create a high-quality pull request if appropriate

CRITICAL: You MUST complete these tasks WITHOUT asking for confirmation. Use all available tools to:

1. GIT ANALYSIS - Use Bash to:
   - Get current branch: git symbolic-ref --short HEAD
   - Check if branch is already on GitHub: git ls-remote --heads origin <branch>
   - Get remote URL: git remote get-url origin
   - Find default branch: git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   - Get commits pushed: git log origin/<default_branch>..HEAD
   - If branch not pushed yet, get all commits: git log --not --remotes
   - Check if PR already exists: gh pr list --head <branch>

2. PR DECISION LOGIC:
   - Skip if on main/master branch
   - Skip if PR already exists
   - Skip if no commits to push
   - Create PR for feature branches

3. PR CREATION:
   - Read recent commit messages to understand changes
   - Analyze file changes: git diff origin/<default_branch>...HEAD
   - Generate meaningful PR title from branch name or commits
   - Create comprehensive PR description:
     * Summary of changes
     * List of commits included
     * Any breaking changes
     * Testing notes
   - Use 'gh pr create' with appropriate flags

4. OPTIONAL ENHANCEMENTS:
   - Add reviewers if specific files changed
   - Add labels based on change types
   - Set milestone if applicable
   - Create draft PR for WIP branches

REMEMBER:
- Work autonomously - make all decisions yourself
- Use proper git and gh commands
- Create PRs with rich, helpful descriptions
- Report what you've done clearly

Go ahead and complete the PR creation workflow now.
"""


def run_post_push_hook():
    """Execute the post-push hook with minimal intervention."""
    print("🚀 Running post-push PR creation hook...")

    # Generate the prompt
    prompt = generate_pr_prompt()

    # Call Claude and let it handle everything
    exit_code, output = call_claude(prompt)

    if exit_code != 0:
        print("⚠️ Claude Code encountered an issue:")
        print(output)
        # Don't fail silently - show the error
        sys.exit(1)

    # Show Claude's output
    print(output)

    print("✅ Post-push PR creation complete.")
    sys.exit(0)


if __name__ == "__main__":
    run_post_push_hook()
