#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.8"
# dependencies = [] # No external Python deps needed if using Claude CLI
# ///

"""
Extreme-Simple Agentic Review Loop

Relying almost entirely on Claude's abilities via clear prompting.
Even basic git operations are handled through Claude.

Usage:
    # Review latest commit
    uv run python library/full_review_loop/extreme_simple_loop.py --latest

    # Review a specific branch against main
    uv run python library/full_review_loop/extreme_simple_loop.py --branch feature-branch
"""

import argparse
import datetime
import os
import subprocess
import time
from pathlib import Path


def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_claude(prompt, role):
    """Run Claude with a given prompt."""
    log(f"Running {role}...")

    # Determine allowed tools based on role
    if role == "developer":
        allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write"
    else:
        allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch"

    try:
        result = subprocess.run(
            [
                "claude",
                "--output-format",
                "text",
                "-p",
                prompt,
                "--allowedTools",
                allowed_tools,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=1200,  # 20 minute timeout
        )
        log(f"{role.capitalize()} completed")
        return result.stdout
    except Exception as e:
        log(f"Error running {role}: {e}")
        return f"Error: {e}"


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Extreme-Simple Agentic Review Loop")

    # Source selection (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--latest", action="store_true", help="Review latest commit")
    source_group.add_argument("--branch", help="Review specific branch against base branch")

    # Base branch
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison (default: main)")

    # Output directory
    parser.add_argument("--output-dir", help="Directory for output files (default: tmp/extreme_loop_TIMESTAMP)")

    args = parser.parse_args()

    # Set up output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = int(time.time())
        output_dir = Path("tmp") / f"extreme_loop_{timestamp}"

    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Log start
    if args.latest:
        log("Starting review of latest commit")
        compare_mode = "--latest"
    else:
        log(f"Starting review of branch '{args.branch}' against '{args.base_branch}'")
        compare_mode = f"--branch {args.branch} --base-branch {args.base_branch}"

    log(f"Output directory: {output_dir}")

    # Step 1: Review Phase
    review_prompt = f"""
Think hard about this task.

You are a senior code reviewer. Your task is to identify issues in code changes.

First, determine what changes we're reviewing:
{f"Compare the latest commit to its parent" if args.latest else f"Compare branch '{args.branch}' to '{args.base_branch}'"}

Steps:
1. Determine the best git diff command to use based on the comparison mode
2. Run that command to see the changes
3. Analyze the changes thoroughly for issues
4. For each issue, mark its priority (CRITICAL, HIGH, MEDIUM, LOW)
5. For each issue, provide the file path and line number
6. Suggest specific fixes for each issue

Format your review as follows:

## Summary
[Overview of the changes and key issues]

## Issue List
[List all issues, grouped by priority]

## Recommendations
[Any strategic or architectural recommendations]

Start with ## Summary without any introductory text.
"""
    review_output = run_claude(review_prompt, "reviewer")
    review_file = output_dir / "review.md"
    with open(review_file, "w") as f:
        f.write(review_output)
    log(f"Review saved to {review_file}")

    # Step 2: Development Phase
    dev_prompt = f"""
Think hard about this task.

You are a senior developer implementing fixes based on a code review. 

Context:
{f"We're reviewing the latest commit" if args.latest else f"We're reviewing branch '{args.branch}' against '{args.base_branch}'"}

Steps:
1. Read the review report at {review_file}
2. Figure out the right git diff command to see the changes being reviewed
3. Identify all CRITICAL and HIGH priority issues from the review
4. Implement fixes for each issue using Edit, MultiEdit, or Write tools
5. Stage and commit your changes with descriptive messages
6. Run any relevant tests to verify your fixes

Format your report as follows:

## Summary
[Overview of the changes you've made]

## Issues Fixed
[Details of each issue you addressed]

## Implementation Notes
[Technical challenges or decisions]

## Test Results
[Results of any tests you ran]

Start with ## Summary without any introductory text.
"""
    dev_output = run_claude(dev_prompt, "developer")
    dev_file = output_dir / "development.md"
    with open(dev_file, "w") as f:
        f.write(dev_output)
    log(f"Development report saved to {dev_file}")

    # Step 3: Validation Phase
    validation_prompt = f"""
Think hard about this task.

You are a validator checking if a developer has properly fixed issues identified in a code review.

Context:
{f"We're reviewing the latest commit" if args.latest else f"We're reviewing branch '{args.branch}' against '{args.base_branch}'"}

Steps:
1. Read the review report at {review_file}
2. Read the developer's report at {dev_file}
3. Determine the right git diff command to examine current changes
4. Verify each CRITICAL and HIGH issue has been properly addressed
5. Check if any new issues were introduced by the fixes
6. Run tests if applicable to verify functionality

Format your validation report as follows:

## Summary
[Overall assessment]

## Issues Verified
[Status of each CRITICAL/HIGH issue]

## Code Quality
[Assessment of the final code]

## Conclusion
[Your final determination]

Your conclusion MUST end with one of these lines:
VALIDATION: PASSED (if all critical and high issues are fixed properly)
VALIDATION: FAILED (if issues remain or new ones were introduced)

Start with ## Summary without any introductory text.
"""
    validation_output = run_claude(validation_prompt, "validator")
    validation_file = output_dir / "validation.md"
    with open(validation_file, "w") as f:
        f.write(validation_output)
    log(f"Validation report saved to {validation_file}")

    # Check validation result
    if "VALIDATION: PASSED" in validation_output:
        log("Validation PASSED!")
    else:
        log("Validation FAILED. See report for details.")

    # Final summary
    log("Process completed successfully")
    log(f"All reports saved to {output_dir}")


if __name__ == "__main__":
    main()
