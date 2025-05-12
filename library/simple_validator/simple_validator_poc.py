#!/usr/bin/env -S uv run --script

"""
Simple Validator for Development Quality Assurance

This script runs a Claude instance to validate fixes implemented based on a code review.

Usage:
    # Validate fixes with default options
    uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> [--output <output_file>] [--verbose]

    # Validate fixes for a specific branch
    uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> --branch <branch_name> [--output <output_file>] [--verbose]

    # Validate only the latest commit
    uv run python library/simple_validator/simple_validator_poc.py <review_file> <dev_report_file> --latest-commit [--branch <branch_name>] [--output <output_file>] [--verbose]

Arguments:
    review_file             Path to the review file containing issues (required)
    dev_report_file         Path to the development report file (required)
    --branch BRANCH         Git branch to validate (default: development-wip)
    --output OUTPUT         Path to save the validation report (default: tmp/validation_<branch>.md)
    --verbose               Enable detailed progress output
    --latest-commit         Validate only the latest commit instead of all branch changes

Examples:
    # Validate fixes from review and dev report files with default branch
    uv run python library/simple_validator/simple_validator_poc.py tmp/review_latest_commit.md tmp/dev_report_latest_commit.md

    # Validate fixes for a specific branch with verbose output
    uv run python library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --branch feature-branch --verbose

    # Complete workflow example (review, implement, validate)
    uv run python library/simple_review/simple_review_poc.py development-wip --output tmp/review.md
    uv run python library/simple_dev/simple_dev_poc.py tmp/review.md --output tmp/dev_report.md
    uv run python library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --output tmp/validation.md

Notes:
    - The validator checks if all CRITICAL and HIGH issues from the review have been fixed
    - It will run tests to ensure the implementation passes all tests
    - The validation report will include explicit PASSED/FAILED status
    - Has a 15-minute timeout for complex validations
    - Use --verbose flag to see progress and a preview of the validation report
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_validation(
    review_file,
    dev_report_file,
    output_file,
    branch_name="development-wip",
    verbose=False,
    latest_commit=False,
):
    """Run Claude to validate fixes and generate a validation report"""
    # Validate that input files exist
    review_path = Path(review_file)
    dev_report_path = Path(dev_report_file)

    if not review_path.exists():
        if verbose:
            print(f"Error: Review file not found at {review_file}")
        return False

    if not dev_report_path.exists():
        if verbose:
            print(f"Error: Development report file not found at {dev_report_file}")
        return False

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine what to validate
    if latest_commit:
        validation_target = f"the latest commit in branch '{branch_name}'"
        compare_cmd = f"HEAD~1...HEAD"
        if verbose:
            print(f"Validating only the latest commit")
    else:
        validation_target = f"branch '{branch_name}' compared to main"
        compare_cmd = f"main...{branch_name}"
        if verbose:
            print(f"Validating all changes between main and {branch_name}")

    # Log if verbose
    if verbose:
        print(f"Running validation for:")
        print(f"  Review file: {review_file}")
        print(f"  Development report: {dev_report_file}")
        print(f"  Branch: {branch_name}")
        print(f"  Output will be saved to: {output_file}")

    # Create validator prompt
    validator_prompt = f"""
Think hard about this task.

You are a validator responsible for ensuring code quality after development changes.
Your task is to:

1. Read the original review at {review_file}
2. Read the development report at {dev_report_file}
3. Run 'git diff {compare_cmd}' to see all current changes
4. Verify that ALL CRITICAL and HIGH issues from the review have been fixed
5. Run 'uv run pytest' to ensure all tests pass
6. Check code quality, focusing on:
   - Proper error handling
   - Input validation
   - Security concerns
   - Adherence to the vertical slice architecture
   - Consistent use of patterns and utilities
7. Write a validation report answering:
   - Have all CRITICAL and HIGH issues been fixed? (Yes/No for each)
   - Are there any new issues introduced by the fixes? (Yes/No)
   - Do all tests pass? (Yes/No)
   - Is the code ready for PR? (Yes/No)
   - If not ready, what specific issues remain?

Be rigorous in your assessment - we want high-quality code.
Provide specific evidence and file paths for your conclusions.

Your validation report must end with ONE of these lines exactly as shown:
- VALIDATION: PASSED (if all critical and high issues are fixed with no new issues)
- VALIDATION: FAILED (if any critical/high issues remain or new issues were introduced)

Write your validation report in markdown format with the following sections:
1. Summary (overall assessment)
2. Issues Assessment (evaluation of each critical/high issue from the review)
3. Test Results (output from running tests)
4. Code Quality Evaluation (assessment of overall code quality)
5. Conclusion (final determination with PASSED/FAILED status)

Begin by summarizing both the original review and the development report.
Then analyze the current state of the code to determine if ALL issues have been properly addressed.
"""

    # Run Claude with the prompt
    if verbose:
        print("Running Claude with validation prompt...")

    try:
        # Configure Claude command
        cmd = [
            "claude",
            "-p",
            validator_prompt,
            "--allowedTools",
            "Bash,Grep,Read,LS,Glob,Task",
            "--output-format",
            "text",
        ]

        # Debug prompt if verbose
        if verbose:
            print(f"Review file exists: {review_path.exists()}")
            print(f"Dev report file exists: {dev_report_path.exists()}")
            try:
                with open(review_file, "r") as f:
                    review_preview = f.read(500)
                    print(f"Review file preview (first 500 chars):\n{review_preview}...")
            except Exception as e:
                print(f"Error reading review file: {e}")

        # Run Claude and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=900,  # 15 minute timeout
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
            output = """# Validation Report

No content was returned from Claude. This could be due to a processing error or configuration issue.

VALIDATION: FAILED
"""

        # Write output to file
        with open(output_file, "w") as f:
            f.write(output)

        # Parse validation result
        validation_passed = "VALIDATION: PASSED" in output

        if verbose:
            print("Validation complete!")
            print(f"Validation result: {'PASSED' if validation_passed else 'FAILED'}")
            print(f"Full validation report saved to: {output_file}")

            # Print a preview
            lines = output.split("\n")
            preview = "\n".join(lines[:15]) + "\n..."
            print(f"\nPreview of validation report:\n{preview}")

        return validation_passed
    except subprocess.TimeoutExpired:
        print(f"Error: Claude validation process timed out after 15 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run code validation with Claude")
    parser.add_argument("review", help="Path to the review file")
    parser.add_argument("dev_report", help="Path to the development report file")
    parser.add_argument(
        "--branch",
        default="development-wip",
        help="Git branch to validate (default: development-wip)",
    )
    parser.add_argument(
        "--output",
        help="Output file path for the validation report (default: tmp/validation_<branch>.md)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--latest-commit",
        action="store_true",
        help="Validate only the latest commit (HEAD vs HEAD~1)",
    )

    args = parser.parse_args()

    # Set default output file if not specified
    if args.output:
        output_file = args.output
    else:
        # Create tmp directory if it doesn't exist
        os.makedirs("tmp", exist_ok=True)

        if args.latest_commit:
            output_file = f"tmp/validation_latest_commit.md"
        else:
            output_file = f"tmp/validation_{args.branch}.md"

    # Run the validation
    validation_passed = run_validation(
        args.review, args.dev_report, output_file, args.branch, args.verbose, args.latest_commit
    )

    # Exit with appropriate status code
    sys.exit(0 if validation_passed else 1)


if __name__ == "__main__":
    main()
