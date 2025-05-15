#!/usr/bin/env -S uv run --script
"""
Automated Bug Triaging using Claude Code - A simplified version that delegates work to Claude Code.

This tool:
1. Fetches GitHub issues from a repository
2. Asks Claude Code to analyze issues, categorize them, and generate a report
3. Uses natural language prompting instead of structured programming

Typical usage:
    # Analyze all open issues in a repository
    uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo

    # Analyze a specific issue
    uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --issue 123

    # Analyze issues with a specific label
    uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --label bug

    # Generate a markdown report
    uv run python concept_library/automated_bug_triage/bug_triage_claude_poc.py --repo owner/repo --output report.md

Arguments:
    --repo          Repository name in format "owner/repo"
    --issue         Specific issue number to analyze (optional)
    --label         Filter issues by label (optional)
    --max-issues    Maximum number of issues to analyze (default: 10)
    --output        Output file path for the report (default: bug_triage_report.md)
    --claude-model  Claude CLI executable name (default: "claude")
    --verbose       Print detailed logs
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Constants
DEFAULT_MAX_ISSUES = 10
DEFAULT_OUTPUT = "bug_triage_report.md"
DEFAULT_MODEL = "claude"


def log(message, verbose=False):
    """Print log message if verbose mode is enabled."""
    if verbose:
        print(f"[BUG TRIAGE] {message}")


def run_claude_task(prompt, model=DEFAULT_MODEL, verbose=False):
    """Run a task with Claude Code."""
    log(f"Running Claude Code with prompt: {prompt[:50]}...", verbose)

    # Create a temporary file for the prompt
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        prompt_file = f.name
        f.write(prompt)

    try:
        # Run Claude with the prompt
        cmd = [model, "-p", "@" + prompt_file, "--allowedTools", "Bash,Write,Read", "--print"]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        claude_output = result.stdout

        log(f"Claude Code output received: {len(claude_output)} characters", verbose)
        return claude_output

    except subprocess.CalledProcessError as e:
        log(f"Error running Claude: {e.stderr if hasattr(e, 'stderr') else str(e)}", verbose)
        return f"Error: {str(e)}"
    finally:
        # Clean up the temporary file
        try:
            os.unlink(prompt_file)
        except:
            pass


def main():
    """Main entry point for the bug triage tool using Claude Code."""
    parser = argparse.ArgumentParser(description="Automated bug triaging tool using Claude Code")
    parser.add_argument("--repo", required=True, help="Repository name in format 'owner/repo'")
    parser.add_argument("--issue", help="Specific issue number to analyze")
    parser.add_argument("--label", help="Filter issues by label")
    parser.add_argument(
        "--max-issues",
        type=int,
        default=DEFAULT_MAX_ISSUES,
        help=f"Maximum number of issues to analyze (default: {DEFAULT_MAX_ISSUES})",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT, help=f"Output file path for the report (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--claude-model", default=DEFAULT_MODEL, help=f"Claude CLI executable name (default: {DEFAULT_MODEL})"
    )
    parser.add_argument("--verbose", action="store_true", help="Print detailed logs")

    args = parser.parse_args()

    # Validate repository name format
    if "/" not in args.repo:
        print(f"Error: Repository name must be in the format 'owner/repo', got '{args.repo}'")
        sys.exit(1)

    # Build the prompt for Claude Code
    prompt = f"""
I need you to create a bug triage report for GitHub issues. Please follow these steps:

1. Fetch GitHub Issues:
   - Repository: {args.repo}
   {f"- Specific issue: {args.issue}" if args.issue else ""}
   {f"- Label filter: {args.label}" if args.label else ""}
   - Maximum issues to analyze: {args.max_issues}
   - Use the GitHub CLI (gh) to fetch the issues

2. For each issue:
   - Analyze the severity (critical, high, medium, low)
   - Determine the bug type (functional, UI/UX, performance, security, etc.)
   - Try to assign it to the most appropriate component based on the repository structure
   - Generate clear reproduction steps
   - Suggest potential approaches for fixing the issue

3. Generate a comprehensive Markdown report:
   - Include a summary section with statistics by severity, type, and component
   - For each issue, include:
     * Title and issue number with a link to GitHub
     * Severity (with emoji: 🔴critical, 🟠high, 🟡medium, 🟢low)
     * Bug type
     * Component
     * Reproduction steps as a numbered list
     * Fix suggestions as bullet points
     * Brief reasoning for the categorization
   - Sort issues by severity (critical first, then high, medium, low)
   - Save the report to: {args.output} if not specified, default to bug_triage_report.md in the project root

4. Use the GitHub CLI to:
   - Fetch the issues (gh issue list/view)
   - Get repository structure (gh api)
   - Feel free to use any other gh commands that might help

The final report should be well-formatted, easy to read, and provide a clear overview of all analyzed issues with actionable information.

Please execute this task step by step, showing your work along the way.
"""

    # Run the task with Claude Code
    print(f"Starting bug triage for {args.repo}...")
    result = run_claude_task(prompt, model=args.claude_model, verbose=args.verbose)

    # Print completion message
    print(f"Bug triage report has been generated: {args.output}")


if __name__ == "__main__":
    main()
