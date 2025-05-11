#!/usr/bin/env -S uv run --script
"""
Simple Reviewer for Code Analysis

This script runs a Claude instance to analyze code and generate a review report.

Usage:
    # Review all changes in a branch compared to the default branch (auto-detected)
    uv run python library/simple_review/simple_review.py <branch_name> [OPTIONS]

    # Review only the latest commit in a branch
    uv run python library/simple_review/simple_review.py <branch_name> --latest-commit [OPTIONS]

    # Review latest commit compared to N commits back
    uv run python library/simple_review/simple_review.py <branch_name> --latest-commit --commits-back N [OPTIONS]

    # Review changes compared to a specific base branch
    uv run python library/simple_review/simple_review.py <branch_name> --base-branch <base_branch> [OPTIONS]

Arguments:
    branch_name             The git branch to review (required)

Options:
    --output OUTPUT         Path to save the review (default: tmp/review_<branch>.md or tmp/review_latest_commit.md)
    --verbose               Enable detailed progress output
    --latest-commit         Review only the latest commit instead of all branch changes
    --commits-back N        When using --latest-commit, compare HEAD to HEAD~N (default: 1)
    --base-branch BASE      Base branch to compare against (default: auto-detected, usually 'main' or 'master')
    --timeout SECONDS       Timeout in seconds for the Claude process (default: 1200, which is 20 minutes)

Examples:
    # Review all changes in development branch compared to auto-detected base branch
    uv run python library/simple_review/simple_review.py development

    # Review only the latest commit in development branch
    uv run python library/simple_review/simple_review.py development --latest-commit

    # Review latest commit compared to 2 commits back
    uv run python library/simple_review/simple_review.py development --latest-commit --commits-back 2

    # Compare development branch to a specific base branch
    uv run python library/simple_review/simple_review.py development --base-branch main

    # Save review to a custom file with verbose output
    uv run python library/simple_review/simple_review.py feature-branch --output reviews/my_review.md --verbose

    # Set a custom timeout for large codebases
    uv run python library/simple_review/simple_review.py large-branch --timeout 2400

Notes:
    - The review focuses on code quality, architecture patterns, and best practices
    - By default compares branch to auto-detected base branch; with --latest-commit compares HEAD to HEAD~1
    - Generates a markdown report with prioritized issues and recommendations
    - Has a configurable timeout (default: 20 minutes) for complex codebases
    - Use --verbose flag to see progress and a preview of the review
    - If a review file already exists, a new file with timestamp will be created
    - The script validates branch names and file paths for security
"""

import argparse
import datetime
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# Constants
TIMEOUT_SECONDS = 1200  # 20 minute timeout
# Regex pattern for valid git branch names
VALID_BRANCH_PATTERN = re.compile(r"^[\w\-\./]+$")
# Default branch name if detection fails
DEFAULT_BRANCH_NAME = "main"
# Template for the reviewer prompt
REVIEWER_PROMPT_TEMPLATE = """
Think hard about this task.

You are a senior code reviewer examining ONLY the changes in {review_target}.
Your task is to provide a thorough, critical review STRICTLY LIMITED to these specific changes.

First run these commands to understand what has changed:
```bash
git diff {compare_cmd} --name-only   # Lists all changed files
git diff {compare_cmd} --stat        # Shows a summary of changes
git diff {compare_cmd}               # See the actual changes
```

Then examine the specific changes in each file before writing your review.

Your review must include these clearly separated sections:

## 1. Summary
Brief overall assessment of the changes.

## 2. Changes Made
Describe what was actually implemented or fixed in these changes. Be specific about what functionality was added, modified, or removed. DO NOT include issues that need fixing in this section.

## 3. Issues to Fix
List problems that need to be addressed, categorized by priority. For each issue:
1. Mark as CRITICAL, HIGH, MEDIUM, or LOW priority
2. Provide the file path and line number
3. Explain the issue with technical reasoning
4. Suggest a specific, actionable fix

Focus your review on these aspects:
1. Consistency with architecture patterns
2. Error handling completeness
3. Input/output validation
4. Security issues
5. Performance concerns
6. Test coverage and quality
7. Code style and maintainability

IMPORTANT: Do not confuse what was fixed with what needs fixing. The "Changes Made" section should only describe what the code changes accomplished, while the "Issues to Fix" section should only list problems that still need to be addressed.

You may examine related files and code when necessary to understand the context of changes, but your feedback should focus on the changed code.

Be specific, actionable, and thorough in your review.

## 4. Recommendations
Provide strategic suggestions beyond specific fixes that could improve the codebase.

Your review will be automatically saved to a file, so focus on creating a detailed, helpful review.

Just write the report file, dont include any other text.
"""


def validate_branch_name(branch_name):
    """Validate that a branch name is safe to use in shell commands.

    Args:
        branch_name: The branch name to validate

    Returns:
        bool: True if the branch name is valid, False otherwise
    """
    return bool(VALID_BRANCH_PATTERN.match(branch_name))


def check_git_repo():
    """Check if the current directory is a git repository.

    Returns:
        bool: True if in a git repository, False otherwise
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, Exception):
        return False


def get_default_branch():
    """Detect the default branch name from the git repository.

    Returns:
        str: The name of the default branch (e.g., 'main' or 'master')
    """
    try:
        # Try to get the default branch from the remote origin HEAD
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Extract the branch name from refs/remotes/origin/HEAD
        default_branch = result.stdout.strip().split("/")[-1]
        return default_branch
    except (subprocess.CalledProcessError, Exception):
        # If that fails, try to get the current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, Exception):
            # Fallback to default if all detection methods fail
            return DEFAULT_BRANCH_NAME


def check_branch_exists(branch_name):
    """Check if a branch exists.

    Args:
        branch_name: The branch name to check

    Returns:
        bool: True if the branch exists, False otherwise
    """
    try:
        subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, Exception):
        return False


def validate_output_path(output_file):
    """Validate that the output path is valid and writable.

    Args:
        output_file: The output file path to validate

    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    try:
        output_path = Path(output_file)

        # Check if the parent directory exists or can be created
        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                return False, f"Cannot create directory {output_path.parent}: {str(e)}"

        # Check if we can write to the parent directory
        if not os.access(str(output_path.parent), os.W_OK):
            return False, f"No write permission for directory: {output_path.parent}"

        # Try to open the file for writing (and close it immediately)
        if output_path.exists():
            # Check if we can write to the existing file
            if not os.access(str(output_path), os.W_OK):
                return False, f"No write permission for file: {output_path}"
        else:
            try:
                # Try to create and write to the file
                open(output_path, "a").close()
                # Remove the empty file we just created
                output_path.unlink()
            except (PermissionError, OSError) as e:
                return False, f"Cannot write to file {output_path}: {str(e)}"
        return True, ""
    except Exception as e:
        return False, f"Invalid output path: {str(e)}"


def get_unique_filename(output_file):
    """Generate a unique filename if the original file already exists.

    Args:
        output_file: The original output file path

    Returns:
        str: A unique filename that doesn't exist yet
    """
    output_path = Path(output_file)
    if not output_path.exists():
        return output_file

    # If file exists, add timestamp to make it unique
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = output_path.stem
    suffix = output_path.suffix
    # Use Path object for proper path handling to avoid path traversal issues
    new_filename = str(output_path.parent / f"{stem}_{timestamp}{suffix}")

    return new_filename


def check_base_branch_exists(base_branch):
    """Check if the base branch exists.

    Args:
        base_branch: The base branch name to check

    Returns:
        bool: True if the branch exists, False otherwise
    """
    try:
        subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{base_branch}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, Exception):
        try:
            # Try checking remote branches as well
            subprocess.run(
                ["git", "show-ref", "--verify", f"refs/remotes/origin/{base_branch}"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, Exception):
            return False


def run_review(
    branch_name,
    output_file,
    verbose=False,
    latest_commit=False,
    base_branch=None,
    timeout=TIMEOUT_SECONDS,
    commits_back=1,
):
    """Run Claude to review code and generate a report.

    Args:
        branch_name: The git branch to review
        output_file: Path to save the review
        verbose: Enable detailed progress output
        latest_commit: Review only the latest commit instead of all branch changes
        base_branch: Base branch to compare against (default: auto-detected)
        timeout: Timeout in seconds for the Claude process
        commits_back: When using latest_commit, compare HEAD to HEAD~commits_back (default: 1)

    Returns:
        bool: True if the review was successful, False otherwise
    """
    # Check if we're in a git repository
    if not check_git_repo():
        print("Error: Not in a git repository")
        return False

    # Validate branch name
    if not validate_branch_name(branch_name):
        print(f"Error: Invalid branch name '{branch_name}'")
        return False

    # Check if branch exists
    if not check_branch_exists(branch_name):
        print(f"Error: Branch '{branch_name}' does not exist")
        return False

    # Validate output path
    is_valid, error_message = validate_output_path(output_file)
    if not is_valid:
        print(f"Error: {error_message}")
        return False

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Log if verbose
    if verbose:
        print(f"Running code review for branch: {branch_name}")
        print(f"Output will be saved to: {output_file}")
    # Determine what to review
    if latest_commit:
        review_target = f"the latest commit in branch '{branch_name}' compared to {commits_back} commit(s) back"
        compare_cmd = f"HEAD~{commits_back}...HEAD"
        if verbose:
            print(f"Reviewing latest commit compared to {commits_back} commit(s) back")
    else:
        # Use the provided base_branch or detect the default branch
        default_branch = base_branch or get_default_branch()

        # Validate the base branch if it was explicitly provided
        if base_branch and not check_base_branch_exists(base_branch):
            print(f"Error: Base branch '{base_branch}' does not exist")
            return False

        # Sanitize branch names for display (they've already been validated)
        safe_branch_name = shlex.quote(branch_name)
        safe_default_branch = shlex.quote(default_branch)

        review_target = f"branch '{safe_branch_name}' compared to {safe_default_branch}"
        # Create a safe comparison command
        compare_cmd = f"{default_branch}...{branch_name}"

        if verbose:
            print(f"Reviewing all changes between {default_branch} and {branch_name}")
    # Create reviewer prompt using the template
    # Use a safer approach by formatting the template with validated values
    reviewer_prompt = REVIEWER_PROMPT_TEMPLATE.format(
        review_target=review_target, compare_cmd=compare_cmd
    )
    # Run Claude with the prompt
    if verbose:
        print("Running Claude with review prompt...")
    try:
        # Configure Claude command
        cmd = [
            "claude",
            "-p",
            reviewer_prompt,
            "--allowedTools",
            "Bash,Grep,Read,LS,Glob,Task",
            "--output-format",
            "text",
        ]
        # Run Claude and capture output
        if verbose:
            print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        output = result.stdout

        # Debug output
        if verbose:
            print(f"Command exit code: {result.returncode}")
            print(f"Output length: {len(output)}")
            if len(output) > 0:
                print(f"Output preview: {output[:100]}...")
            else:
                print("Output is empty")
            if result.stderr:
                print(f"Error output: {result.stderr}")
        # Get a unique filename if the file already exists
        unique_output_file = get_unique_filename(output_file)

        # Write output to file with explicit error handling
        try:
            # Write the actual review content to the file
            with open(unique_output_file, "w") as f:
                f.write(output)
        except (IOError, OSError) as e:
            print(f"Error: Failed to write to file {unique_output_file}: {str(e)}")
            return False

        # Update output_file variable if it changed
        if unique_output_file != output_file and verbose:
            print(f"File already existed. Saved to: {unique_output_file}")
            output_file = unique_output_file
        if verbose:
            print("Review complete!")
            print(f"Full review saved to: {output_file}")
            # Print a preview
            lines = output.split("\n")
            preview = "\n".join(lines[:15]) + "\n..."
            print(f"\nPreview of review:\n{preview}")
        return True
    except subprocess.TimeoutExpired:
        print(f"Error: Claude review process timed out after {timeout // 60} minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run code review with Claude")
    parser.add_argument(
        "branch", help="Git branch to review (compared to the base branch by default)"
    )
    parser.add_argument(
        "--output", help="Output file path for the review (default: review_<branch>.md)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--latest-commit",
        action="store_true",
        help="Review only the latest commit (HEAD vs HEAD~N)",
    )
    parser.add_argument(
        "--commits-back",
        type=int,
        default=1,
        help="When using --latest-commit, compare HEAD to HEAD~N (default: 1)",
    )
    parser.add_argument(
        "--base-branch",
        help="Base branch to compare against (default: auto-detected, usually 'main' or 'master')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"Timeout in seconds for the Claude process (default: {TIMEOUT_SECONDS})",
    )
    args = parser.parse_args()
    # Always create tmp directory
    os.makedirs("tmp", exist_ok=True)

    # Set default output file if not specified
    if args.output:
        output_file = args.output
    else:
        if args.latest_commit:
            output_file = f"tmp/review_latest_commit.md"
        else:
            output_file = f"tmp/review_{args.branch}.md"
    # Run the review
    success = run_review(
        args.branch,
        output_file,
        verbose=args.verbose,
        latest_commit=args.latest_commit,
        base_branch=args.base_branch,
        timeout=args.timeout,
        commits_back=args.commits_back,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
