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
import subprocess
import time
from pathlib import Path


def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_claude(prompt, role, custom_tools=None):
    """Run Claude with a given prompt.
    
    Args:
        prompt: The prompt to send to Claude
        role: The role of the Claude instance (reviewer, developer, validator)
        custom_tools: Optional custom tools string to override defaults
    """
    log(f"Running {role}...")

    # If custom tools are provided, use them, otherwise use role-based defaults
    if custom_tools:
        allowed_tools = custom_tools
    else:
        # Determine allowed tools based on role
        if role == "developer":
            allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write"
        else:
            allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch"

    try:
        # Construct command arguments as a list to prevent command injection
        cmd = [
            "claude",
            "--output-format",
            "text",
            "-p",
            prompt,
            "--allowedTools",
            allowed_tools,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=args.timeout,  # Configurable timeout
                shell=False,  # Explicitly disable shell to prevent command injection
            )
            log(f"{role.capitalize()} completed")
            return result.stdout

        except subprocess.TimeoutExpired as e:
            log(f"Timeout error running {role}: Process exceeded {e.timeout} seconds")
            return f"Error: Timeout error: Process exceeded {e.timeout} seconds"

        except subprocess.CalledProcessError as e:
            log(f"Process error running {role}: Command failed with exit code {e.returncode}")
            error_details = f"Command failed with exit code {e.returncode}\nStderr: {e.stderr}"
            return f"Error: {error_details}"

    except FileNotFoundError as e:
        log(f"File not found error: {e}")
        return "Error: Claude CLI not found. Please ensure it's installed and in your PATH."

    except PermissionError as e:
        log(f"Permission error: {e}")
        return f"Error: Permission denied: {e}"

    except Exception as e:
        # Fallback for any unexpected errors
        log(f"Unexpected error running {role}: {e}")
        return f"Error: Unexpected error: {e}"


def main():
    # Initialize success tracking
    success = False

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

    # Tool configuration
    parser.add_argument("--reviewer-tools",
                        help="Comma-separated list of tools for reviewer (default: Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch)")
    parser.add_argument("--developer-tools",
                        help="Comma-separated list of tools for developer (default: Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write)")
    parser.add_argument("--validator-tools",
                        help="Comma-separated list of tools for validator (default: same as reviewer)")

    # Other options
    parser.add_argument("--timeout", type=int, default=1200,
                        help="Timeout in seconds for Claude calls (default: 1200)")

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
        # Validate branch names to prevent command injection
        import re

        def is_valid_branch_name(name):
            """Validate branch name contains only allowed characters."""
            # Typical allowed characters in git branch names
            return bool(re.match(r'^[a-zA-Z0-9_/.-]+$', name))

        # Validate branch names for security
        if not is_valid_branch_name(args.branch):
            log(f"Error: Invalid branch name format: '{args.branch}'")
            return 1

        if not is_valid_branch_name(args.base_branch):
            log(f"Error: Invalid base branch name format: '{args.base_branch}'")
            return 1

        log(f"Starting review of branch '{args.branch}' against '{args.base_branch}'")

        # Safely construct arguments without string interpolation
        compare_mode = "--branch {} --base-branch {}".format(
            args.branch.replace("'", "").replace('"', ""),
            args.base_branch.replace("'", "").replace('"', "")
        )

    log(f"Output directory: {output_dir}")

    # Step 1: Review Phase
    review_prompt = f"""
Think hard about this task.

You are a senior code reviewer. Your task is to identify issues in code changes.

First, determine what changes we're reviewing:
{"Compare the latest commit to its parent" if args.latest else f"Compare branch '{args.branch}' to '{args.base_branch}'"}

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
    review_output = run_claude(review_prompt, "reviewer", args.reviewer_tools)
    review_file = output_dir / "review.md"
    with open(review_file, "w") as f:
        f.write(review_output)
    log(f"Review saved to {review_file}")

    # Step 2: Development Phase
    dev_prompt = f"""
Think hard about this task.

You are a senior developer implementing fixes based on a code review. 

Context:
{"We're reviewing the latest commit" if args.latest else f"We're reviewing branch '{args.branch}' against '{args.base_branch}'"}

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
    dev_output = run_claude(dev_prompt, "developer", args.developer_tools)
    dev_file = output_dir / "development.md"
    with open(dev_file, "w") as f:
        f.write(dev_output)
    log(f"Development report saved to {dev_file}")

    # Step 3: Validation Phase
    validation_prompt = f"""
Think hard about this task.

You are a validator checking if a developer has properly fixed issues identified in a code review.

Context:
{"We're reviewing the latest commit" if args.latest else f"We're reviewing branch '{args.branch}' against '{args.base_branch}'"}

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
    validation_output = run_claude(validation_prompt, "validator", args.validator_tools)
    validation_file = output_dir / "validation.md"
    with open(validation_file, "w") as f:
        f.write(validation_output)
    log(f"Validation report saved to {validation_file}")

    # Check validation result using robust regex pattern matching
    import re

    # Define regex patterns to match the exact validation decision phrases
    # Using anchored patterns with line boundaries for exact matches
    passed_pattern = re.compile(r'^VALIDATION:\s*PASSED\s*$', re.MULTILINE)
    failed_pattern = re.compile(r'^VALIDATION:\s*FAILED\s*$', re.MULTILINE)

    if passed_pattern.search(validation_output):
        log("Validation PASSED!")
        success = True
    elif failed_pattern.search(validation_output):
        log("Validation FAILED. See report for details.")
        success = False
    else:
        log("Warning: No valid validation decision found in output.")
        log("Expected 'VALIDATION: PASSED' or 'VALIDATION: FAILED' in the output.")

        # Attempt to infer result from content if no explicit decision found
        if any(marker in validation_output.lower() for marker in
              ["all issues resolved", "successfully fixed", "no issues remain"]):
            log("Inferring PASSED based on validation content")
            success = True
        else:
            log("Inferring FAILED based on validation content")
            success = False

    # Final summary
    result_msg = "Process completed: " + ("PASSED" if success else "FAILED")
    log(result_msg)
    log(f"All reports saved to {output_dir}")

    # Return appropriate exit code based on success
    return 0 if success else 1


if __name__ == "__main__":
    main()
