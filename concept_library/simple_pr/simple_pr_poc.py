#!/usr/bin/env -S uv run --script

"""
Simple PR Manager for Creating Pull Requests

This script runs a Claude instance to create or update a pull request based on validated changes.

Usage:
    # Create PR with default options based on validation report
    uv run python concept_library/simple_pr/simple_pr_poc.py <validation_file> [--title <pr_title>] [--output <output_file>] [--verbose]

    # Create PR for a specific branch
    uv run python concept_library/simple_pr/simple_pr_poc.py <validation_file> --branch <branch_name> --base <base_branch> [--title <pr_title>] [--output <output_file>] [--verbose]

    # Only generate PR description without actually creating PR
    uv run python concept_library/simple_pr/simple_pr_poc.py <validation_file> --dry-run [--output <output_file>] [--verbose]

Arguments:
    validation_file        Path to the validation report file confirming changes are ready (required)
    --branch BRANCH        Git branch containing changes (default: development-wip)
    --base BASE            Base branch to merge changes into (default: main)
    --title TITLE          Title for the pull request (default: generated from branch name)
    --output OUTPUT        Path to save the PR report (default: tmp/pr_<branch>.md)
    --verbose              Enable detailed progress output
    --dry-run              Generate PR description without creating the PR

Examples:
    # Create a PR based on validation report
    uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md --title "Add PipedriveSettings configuration class"

    # Create a PR for a specific branch into main
    uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md --branch feature-branch --base main --verbose

    # Generate PR description without creating PR
    uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md --dry-run --output tmp/pr_description.md

    # Complete workflow example (review, develop, validate, create PR)
    uv run python concept_library/simple_review/simple_review_poc.py development-wip --output tmp/review.md
    uv run python concept_library/simple_dev/simple_dev_poc.py tmp/review.md --output tmp/dev_report.md
    uv run python concept_library/simple_validator/simple_validator_poc.py tmp/review.md tmp/dev_report.md --output tmp/validation.md
    uv run python concept_library/simple_pr/simple_pr_poc.py tmp/validation.md --title "Implement configuration management"

Notes:
    - Only proceeds if validation report shows PASSED status
    - Uses GitHub CLI (gh) to create pull requests
    - Generates comprehensive PR descriptions based on development report
    - Has a 10-minute timeout for PR creation
    - Use --verbose flag to see progress and a preview of the PR description
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def check_validation_status(validation_file, verbose=False):
    """Check if validation report shows PASSED status"""
    if not Path(validation_file).exists():
        print(f"Error: Validation file not found at {validation_file}")
        return False

    with open(validation_file) as f:
        content = f.read()

    # Check for validation status
    passed = "VALIDATION: PASSED" in content

    if verbose:
        print(f"Validation status: {'PASSED' if passed else 'FAILED'}")

    return passed


def run_pr_creation(
    validation_file,
    output_file,
    branch_name="development-wip",
    base_branch="main",
    pr_title=None,
    verbose=False,
    dry_run=False,
):
    """Run Claude to create a PR and generate a PR report"""
    # Check that validation has passed
    validation_passed = check_validation_status(validation_file, verbose)
    if not validation_passed:
        print("Error: Validation has not passed. Cannot create PR.")
        return False

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate default PR title if not provided
    if not pr_title:
        # Try to extract a meaningful title from branch name
        clean_branch = branch_name.replace("development-", "").replace("-", " ")
        clean_branch = re.sub(
            r"(?<![A-Z])[A-Z]", lambda x: f" {x.group(0)}", clean_branch
        )  # Add space before capital letters
        clean_branch = clean_branch.strip().title()
        pr_title = f"Add {clean_branch}" if clean_branch else f"Changes from {branch_name}"

    # Log if verbose
    if verbose:
        print("Running PR creation for:")
        print(f"  Validation file: {validation_file}")
        print(f"  Branch: {branch_name}")
        print(f"  Base branch: {base_branch}")
        print(f"  PR title: {pr_title}")
        print(f"  Output will be saved to: {output_file}")
        print(f"  Dry run: {dry_run}")

    # Create PR manager prompt
    pr_manager_prompt = f"""
Think hard about this task.

You are a PR manager responsible for preparing a high-quality pull request.
Your task is to:

1. Read the validation report at {validation_file} to confirm validation has passed
2. Run 'git diff {base_branch}...{branch_name}' to see all changes
3. Create a comprehensive PR description including:
   - Summary of changes
   - List of issues fixed
   - Testing performed
   - Any known limitations or future work

Follow these steps:
1. First, check if validation has passed. Only proceed if it shows "VALIDATION: PASSED"
2. Understand the changes by running git commands to analyze what has changed
3. Generate a PR description with the following sections:
   ## Changes
   [Summary of what was changed and why]

   ## Issues Addressed
   [List of specific issues that were fixed]

   ## Testing
   [Summary of tests performed]

   ## Notes
   [Any other information or future considerations]

4. If running in dry-run mode, return only the PR description
5. If not in dry-run mode, also push the branch and create the PR:
   - Run 'git push -u origin {branch_name}' to push the branch
   - Use 'gh pr create --base {base_branch} --head {branch_name} --title "{pr_title}"' with your generated description

Remember to be thorough in your analysis but concise in your PR description.
Focus on what would be most helpful for a reviewer to understand these changes.

Write your PR report in markdown format, and if creating a PR, include the PR URL at the end.
"""

    # Run Claude with the prompt
    if verbose:
        print("Running Claude with PR creation prompt...")

    try:
        # Configure Claude command
        cmd = [
            "claude",
            "-p",
            pr_manager_prompt,
            "--allowedTools",
            "Bash,Grep,Read,LS,Glob,Task",
            "--output-format",
            "text",
        ]

        # Debug prompt if verbose
        if verbose:
            print(f"Validation file exists: {Path(validation_file).exists()}")

            try:
                with open(validation_file) as f:
                    validation_preview = f.read(500)
                    print(f"Validation file preview (first 500 chars):\n{validation_preview}...")
            except Exception as e:
                print(f"Error reading validation file: {e}")

        # Run Claude and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=600,  # 10 minute timeout
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
            output = f"""# PR Creation Report

No content was returned from Claude. This could be due to a processing error or configuration issue.

{"PR Description would be generated here" if dry_run else "PR creation was attempted but encountered issues."}
"""

        # Write output to file
        with open(output_file, "w") as f:
            f.write(output)

        # Determine if PR was created by looking for PR URL in output
        pr_created = False
        pr_url = None

        if not dry_run:
            # Look for PR URL in output (typical format: https://github.com/owner/repo/pull/123)
            pr_url_match = re.search(r"https://github\.com/[^/]+/[^/]+/pull/\d+", output)
            if pr_url_match:
                pr_url = pr_url_match.group(0)
                pr_created = True

        if verbose:
            print("PR creation process complete!")
            if not dry_run:
                if pr_created:
                    print(f"PR successfully created: {pr_url}")
                else:
                    print("PR may not have been created. Check the output for details.")
            else:
                print("Dry run complete - PR description generated but PR not created")

            print(f"Full PR report saved to: {output_file}")

            # Print a preview
            lines = output.split("\n")
            preview = "\n".join(lines[:15]) + "\n..."
            print(f"\nPreview of PR report:\n{preview}")

        return pr_created if not dry_run else True
    except subprocess.TimeoutExpired:
        print("Error: Claude PR creation process timed out after 10 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run PR creation with Claude")
    parser.add_argument("validation", help="Path to the validation report file")
    parser.add_argument(
        "--branch",
        default="development-wip",
        help="Git branch containing changes (default: development-wip)",
    )
    parser.add_argument(
        "--base", default="main", help="Base branch to merge changes into (default: main)"
    )
    parser.add_argument(
        "--title", help="Title for the pull request (default: generated from branch name)"
    )
    parser.add_argument(
        "--output", help="Output file path for the PR report (default: tmp/pr_<branch>.md)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate PR description without creating the PR"
    )

    args = parser.parse_args()

    # Set default output file if not specified
    if args.output:
        output_file = args.output
    else:
        # Create tmp directory if it doesn't exist
        os.makedirs("tmp", exist_ok=True)
        output_file = f"tmp/pr_{args.branch}.md"

    # Run the PR creation
    success = run_pr_creation(
        args.validation, output_file, args.branch, args.base, args.title, args.verbose, args.dry_run
    )

    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
