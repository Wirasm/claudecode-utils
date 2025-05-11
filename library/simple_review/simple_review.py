#!/usr/bin/env -S uv run --script
"""
Simple Reviewer for Code Analysis
This script runs a Claude instance to analyze code and generate a review report.
Usage:
    # Review all changes in a branch compared to main
    uv run python library/simple_review/simple_review.py <branch_name> [--output <output_file>] [--verbose]
    # Review only the latest commit in a branch
    uv run python library/simple_review/simple_review.py <branch_name> --latest-commit [--output <output_file>] [--verbose]
    # Example usage for reviewing latest commit in development branch
    uv run python library/simple_review/simple_review.py development --latest-commit
    # Example usage for reviewing all changes in development branch
    uv run python library/simple_review/simple_review.py development
Arguments:
    branch_name             The git branch to review (required)
    --output OUTPUT         Path to save the review (default: review_<branch>.md or review_latest_commit.md)
    --verbose               Enable detailed progress output
    --latest-commit         Review only the latest commit instead of all branch changes
Examples:
    # Review all changes in development branch compared to main
    uv run python library/simple_review/simple_review.py development
    # Review only the latest commit in development branch
    uv run python library/simple_review/simple_review.py development --latest-commit
    # Save review to a custom file with verbose output
    uv run python library/simple_review/simple_review.py feature-branch --output reviews/my_review.md --verbose
Notes:
    - The review focuses on code quality, architecture patterns, and best practices
    - By default compares branch to main; with --latest-commit compares HEAD to HEAD~1
    - Generates a markdown report with prioritized issues and recommendations
    - Has a 20-minute timeout for complex codebases
    - Use --verbose flag to see progress and a preview of the review
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

# Constants
TIMEOUT_SECONDS = 1200  # 20 minute timeout
# Regex pattern for valid git branch names
VALID_BRANCH_PATTERN = re.compile(r'^[\w\-\./]+$')

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
    except subprocess.CalledProcessError:
        return False

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
    except subprocess.CalledProcessError:
        return False

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
    new_filename = f"{output_path.parent}/{stem}_{timestamp}{suffix}"
    
    return new_filename


def run_review(branch_name, output_file, verbose=False, latest_commit=False):
    """Run Claude to review code and generate a report.
    
    Args:
        branch_name: The git branch to review
        output_file: Path to save the review
        verbose: Enable detailed progress output
        latest_commit: Review only the latest commit instead of all branch changes
        
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
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Log if verbose
    if verbose:
        print(f"Running code review for branch: {branch_name}")
        print(f"Output will be saved to: {output_file}")
    # Determine what to review
    if latest_commit:
        review_target = f"the latest commit in branch '{branch_name}'"
        compare_cmd = "HEAD~1...HEAD"
        if verbose:
            print("Reviewing only the latest commit")
    else:
        review_target = f"branch '{branch_name}' compared to main"
        # Use array form for safety instead of string interpolation
        compare_cmd = f"main...{branch_name}"
        if verbose:
            print(f"Reviewing all changes between main and {branch_name}")
    # Create reviewer prompt
    reviewer_prompt = f"""
Think hard about this task.
You are a senior code reviewer examining ONLY the changes in {review_target}.
Your task is to provide a thorough, critical review STRICTLY LIMITED to these specific changes.
Focus your review on these aspects:
1. Consistency with vertical slice architecture patterns
2. API error handling completeness
3. Input/output validation in models
4. Proper use of shared utilities (ID conversion, response formatting)
5. Security issues
6. Performance concerns
7. Test coverage and quality
For each issue found:
1. Mark as CRITICAL, HIGH, MEDIUM, or LOW priority
2. Provide the file path and line number (preferably of changed code)
3. Clearly indicate if the issue is in changed code or in related context
4. Explain the issue with technical reasoning
5. Suggest a specific, actionable fix
First run:
1. 'git diff {compare_cmd} --name-only' to see which files were changed
2. 'git diff {compare_cmd}' to see the actual line-by-line changes
Focus primarily on reviewing the changed lines and files, as these are what need to be evaluated for the PR/diff.
You may examine related files and code when necessary to understand the context of changes, but:
1. Your feedback should focus on issues in the changed code
2. Only mention issues in unchanged code if they directly impact the changes being reviewed
3. Always prioritize reviewing the actual diff changes first
Your primary job is to review what changed in the diff, while having the freedom to explore context when it helps your analysis.
Start by running these commands to understand what has changed:
```bash
git diff {compare_cmd} --name-only   # Lists all changed files
git diff {compare_cmd} --stat        # Shows a summary of changes
```
Then examine the specific changes in each file before writing your review.
Write your review in markdown format with the following sections:
1. Summary (overall assessment and key themes)
2. Issue List (all issues categorized by priority)
   - 2.1 Issues in Changed Code
   - 2.2 Context-Related Issues (if any)
3. Recommendations (strategic suggestions beyond specific fixes)
Your review will be automatically saved to a file, so focus on creating a detailed, helpful review.
"""
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_SECONDS,
        )
        output = result.stdout
        # Get a unique filename if the file already exists
        unique_output_file = get_unique_filename(output_file)
        
        # Write output to file
        with open(unique_output_file, "w") as f:
            f.write(output)
            
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
        print(f"Error: Claude review process timed out after 20 minutes")
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
        "branch",
        help="Git branch to review (compared to main by default)"
    )
    parser.add_argument(
        "--output",
        help="Output file path for the review (default: review_<branch>.md)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--latest-commit",
        action="store_true",
        help="Review only the latest commit (HEAD vs HEAD~1)"
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
        branch_name=args.branch,
        output_file=output_file,
        verbose=args.verbose,
        latest_commit=args.latest_commit
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
