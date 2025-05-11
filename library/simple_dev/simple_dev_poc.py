#!/usr/bin/env -S uv run --script

"""
Simple Developer for Implementing Code Fixes

This script runs a Claude instance to implement fixes based on a code review.

Usage:
    # Implement fixes from a review (default branch: development-wip)
    uv run python scripts/simple_dev.py <review_file> [--output <output_file>] [--verbose]

    # Implement fixes for a specific branch
    uv run python scripts/simple_dev.py <review_file> --branch <branch_name> [--output <output_file>] [--verbose]

    # Implement fixes for the latest commit only
    uv run python scripts/simple_dev.py <review_file> --latest-commit [--branch <branch_name>] [--output <output_file>] [--verbose]

Arguments:
    review                  Path to the review file to implement fixes from (required)
    --branch BRANCH         Git branch to work on (default: development-wip)
    --output OUTPUT         Path to save the development report (default: dev_report_<branch>.md)
    --verbose               Enable detailed progress output
    --latest-commit         Work on only the latest commit instead of all branch changes

Examples:
    # Implement fixes from review_development-wip.md on the development-wip branch
    uv run python scripts/simple_dev.py review_development-wip.md

    # Implement fixes from review_latest_commit.md for the latest commit
    uv run python scripts/simple_dev.py review_latest_commit.md --latest-commit

    # Implement fixes for a feature branch with custom output file
    uv run python scripts/simple_dev.py reviews/feature_review.md --branch feature-branch --output reports/feature_fixes.md --verbose

    # Full development cycle example (review then fix)
    uv run python scripts/simple_review.py development-wip --latest-commit --output review_latest.md
    uv run python scripts/simple_dev.py review_latest.md --latest-commit --output dev_report_latest.md

Notes:
    - The development process follows a review/fix workflow
    - Focuses on implementing fixes for CRITICAL and HIGH priority issues first
    - Creates, updates, or deletes files as needed based on the review
    - Runs with a 60-minute timeout for complex implementations
    - Generates a markdown report detailing all changes made
    - Use --verbose flag to see progress and a preview of the report
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_development(review_file, output_file, branch_name, verbose=False, latest_commit=False):
    """Run Claude to implement fixes based on a review and generate a report"""
    # Validate that review file exists
    review_path = Path(review_file)
    if not review_path.exists():
        if verbose:
            print(f"Error: Review file not found at {review_file}")
        return False

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine what to work on
    if latest_commit:
        work_target = f"the latest commit in branch '{branch_name}'"
        compare_cmd = f"HEAD~1...HEAD"
        if verbose:
            print(f"Working on only the latest commit")
    else:
        work_target = f"branch '{branch_name}' compared to main"
        compare_cmd = f"main...{branch_name}"
        if verbose:
            print(f"Working on all changes between main and {branch_name}")

    # Log if verbose
    if verbose:
        print(f"Running development process based on review: {review_file}")
        print(f"Working on branch: {branch_name}")
        print(f"Output will be saved to: {output_file}")

    # Create developer prompt
    developer_prompt = f"""
Think hard about this task.

You are a senior developer implementing fixes based on a code review.
Your task is to:

1. Read the review at {review_file}
2. Create a plan to address all CRITICAL and HIGH priority issues identified in the review
3. Implement fixes for these issues one by one
4. Test your changes to ensure they work properly
5. Document your changes clearly

For each issue you fix:
1. First understand the issue thoroughly
2. Plan your approach to fixing it
3. Implement the solution using appropriate tools
4. Verify your fix addresses the issue
5. Document what you did and why it fixes the issue

Run 'git diff {compare_cmd}' first to understand the current code.
Use the review to guide your fixes.

First, read the review file and create a prioritized list of issues to fix.
Then address each issue one by one, documenting your changes clearly.

When you make code changes, use appropriate tools like Edit, Bash, etc.
When implementing fixes, run tests with 'uv run pytest' to verify them when applicable.

Write your development report in markdown format with the following sections:
1. Summary (overview of what you fixed and general approach)
2. Issues Fixed (detail on each issue and how you fixed it)
   - 2.1 CRITICAL Issues
   - 2.2 HIGH Priority Issues
3. Implementation Notes (any challenges encountered or alternatives considered)
4. Test Results (results of running tests after your changes)
5. Next Steps (any issues that couldn't be fixed or require further work)

Your report will be automatically saved to a file, so focus on implementing high-quality fixes.
"""

    # Run Claude with the prompt
    if verbose:
        print("Running Claude with development prompt...")

    try:
        # Configure Claude command
        cmd = [
            "claude",
            "-p",
            developer_prompt,
            "--allowedTools",
            "Bash,Grep,Read,LS,Glob,Task,Edit,MultiEdit,Write",
            "--output-format",
            "text",
        ]

        # Debug prompt if verbose
        if verbose:
            print(f"Review file contents first few lines:")
            with open(review_file, "r") as f:
                print(f.readlines()[:5])

        # Run Claude and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=3600,  # 60 minute timeout - development can take longer
        )
        output = result.stdout

        # Debug result if verbose
        if verbose:
            print(f"Claude stdout length: {len(output)}")
            print(f"Claude stderr length: {len(result.stderr) if result.stderr else 0}")
            print(f"Claude return code: {result.returncode}")
            if not output.strip():
                print("WARNING: Empty output from Claude!")
                if result.stderr:
                    print(f"First 200 chars of stderr: {result.stderr[:200]}")

        # Ensure we have at least minimal content
        if not output.strip():
            output = "# Development Report\n\nNo content was returned from Claude. This could be due to a processing error or configuration issue."

        # Write output to file
        with open(output_file, "w") as f:
            f.write(output)

        if verbose:
            print("Development phase complete!")
            print(f"Full development report saved to: {output_file}")

            # Print a preview
            lines = output.split("\n")
            preview = "\n".join(lines[:15]) + "\n..."
            print(f"\nPreview of development report:\n{preview}")

        return True
    except subprocess.TimeoutExpired:
        print(f"Error: Claude development process timed out after 30 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run code development process with Claude")
    parser.add_argument("review", help="Path to the review file to use as input")
    parser.add_argument("--branch", default="development-wip", help="Git branch to work on (default: development-wip)")
    parser.add_argument(
        "--output", help="Output file path for the development report (default: dev_report_<branch>.md)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--latest-commit", action="store_true", help="Work on only the latest commit (HEAD vs HEAD~1)")

    args = parser.parse_args()

    # Set default output file if not specified
    if args.output:
        output_file = args.output
    else:
        # Create tmp directory if it doesn't exist
        os.makedirs("tmp", exist_ok=True)

        if args.latest_commit:
            output_file = f"tmp/dev_report_latest_commit.md"
        else:
            output_file = f"tmp/dev_report_{args.branch}.md"

    # Run the development process
    success = run_development(args.review, output_file, args.branch, args.verbose, args.latest_commit)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
