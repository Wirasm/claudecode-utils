#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Claude-Driven Review Loop

An orchestration script that leverages Claude Code itself to manage
the review and development process, with artifacts stored in a shared directory.

Flow:
1. Review: Initial code review
2. Developer: Implements fixes
3. Review: Re-reviews the fixes (pass/reject)
   - If reject: Back to Developer step
   - If pass: Proceed to Validator
4. Validator: Validates the fixes (pass/reject)
   - If reject: Back to Developer step
   - If pass: Complete

Usage:
    # Review latest commit
    uv run python library/full_review_loop/claude_driven_review_loop.py --latest

    # Review a specific branch with max iterations
    uv run python library/full_review_loop/claude_driven_review_loop.py --branch feature-branch --max-iterations 3
"""

import argparse
import datetime
import os
import subprocess
import time
import uuid
from pathlib import Path


#######################
# Step 1: Logging
# Logging helper for timestamped messages
#######################
def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


#######################
# Step 2: Claude Execution
# Run Claude with artifacts awareness
#######################
def run_claude(prompt, role, output_file, allowed_tools, session_dir):
    """Run Claude with a given prompt and save output to a file."""
    log(f"Running {role}...")

    try:
        # Build the list of artifacts to inform Claude about
        artifacts_info = ""
        if session_dir.exists():
            artifacts_info = "Available artifacts from previous steps:\n"
            for file in sorted(session_dir.glob("*.md")):
                artifacts_info += f"- {file.name}: {file}\n"

        full_prompt = f"""
{artifacts_info}

{prompt}
"""

        result = subprocess.run(
            [
                "claude",
                "--output-format",
                "text",
                "-p",
                full_prompt,
                "--allowedTools",
                allowed_tools,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=1200,  # 20 minute timeout
        )

        # Save output to file
        with open(output_file, "w") as f:
            f.write(result.stdout)

        log(f"{role.capitalize()} completed and saved to {output_file}")
        return result.stdout
    except Exception as e:
        log(f"Error running {role}: {e}")
        # Save error to file
        with open(output_file, "w") as f:
            f.write(f"Error running {role}: {e}")
        return f"Error: {e}"


#######################
# Step 3: Main Orchestration
# Main workflow orchestration function
#######################
def main():
    #######################
    # Step 3.1: Argument Parsing
    # Parse command-line arguments
    #######################
    parser = argparse.ArgumentParser(description="Claude-Driven Review Loop")

    # Source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--latest", action="store_true", help="Review latest commit")
    source_group.add_argument("--branch", help="Review specific branch against base branch")

    # Options
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison (default: main)")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum review/dev iterations (default: 3)")
    parser.add_argument("--output-dir", help="Directory for output files (default: tmp/claude_review_SESSION_ID)")
    parser.add_argument("--skip-pr", action="store_true", help="Skip PR creation even if validation passes")

    args = parser.parse_args()

    #######################
    # Step 3.2: Session Setup
    # Create output directory and session context
    #######################
    # Create unique session ID and output directory
    session_id = str(uuid.uuid4())[:8]

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = int(time.time())
        output_dir = Path("tmp") / f"claude_review_{timestamp}_{session_id}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Log basic info
    if args.latest:
        log("Starting review of latest commit")
        compare_desc = "latest commit against its parent"
    else:
        log(f"Starting review of branch '{args.branch}' against '{args.base_branch}'")
        compare_desc = f"branch '{args.branch}' against '{args.base_branch}'"

    log(f"Session ID: {session_id}")
    log(f"Output directory: {output_dir}")
    log(f"Maximum iterations: {args.max_iterations}")

    #######################
    # Step 3.3: State Machine
    # Implement workflow as a state machine
    #######################
    # Initialize state
    iteration = 0
    state = "review"  # Start with review
    dev_iterations = 0
    validation_passed = False
    final_success = False

    while iteration < args.max_iterations:
        iteration += 1
        log(f"\n=== Starting Iteration {iteration}/{args.max_iterations}, State: {state} ===")

        #######################
        # Step 3.3.1: Review State
        # Code reviewer examines changes and determines if they pass or need work
        #######################
        if state == "review":
            review_file = output_dir / f"review_iter_{iteration}.md"
            review_prompt = f"""
Think hard about this task. You are Iteration #{iteration}/{args.max_iterations}.

You are a senior code reviewer examining changes in {compare_desc}.
{"This is a re-review after development changes." if dev_iterations > 0 else ""}

Your task is to identify issues in the code changes with these priorities:
1. CRITICAL: Must be fixed (security vulnerabilities, broken functionality)
2. HIGH: Important to fix (bugs, serious code smells)
3. MEDIUM: Should be fixed (maintainability issues)
4. LOW: Nice to fix (style, minor improvements)

Steps:
1. Run the appropriate git diff command to see the changes
2. Thoroughly analyze these changes for issues
3. For each issue found, provide:
   - Priority (CRITICAL, HIGH, MEDIUM, LOW)
   - File path and line number
   - Clear explanation of the issue
   - Specific, actionable fix suggestion

Format your output as a markdown document with these sections:
## Summary
[Overview of changes and key issues]

## Issue List
### CRITICAL
[List critical issues with file:line, explanation, and fix]

### HIGH
[List high priority issues]

### MEDIUM
[List medium priority issues]

### LOW
[List low priority issues]

## Recommendations
[Strategic suggestions beyond specific fixes]

## Review Decision
[Your assessment of whether the code is ready to proceed]

Your review decision MUST end with one of these lines exactly:
REVIEW: PASSED (if no CRITICAL or HIGH issues remain and code meets quality standards)
REVIEW: REJECTED (if CRITICAL or HIGH issues were found that need to be fixed)

Start with ## Summary without any introductory text.
"""
            review_output = run_claude(
                review_prompt,
                f"reviewer_{iteration}",
                review_file,
                "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch",
                output_dir,
            )

            # Check if review passed or failed
            if "REVIEW: PASSED" in review_output:
                log("Review PASSED! Moving to validator state.")
                state = "validator"
            else:
                log("Review REJECTED. Moving to developer state.")
                state = "developer"

        #######################
        # Step 3.3.2: Developer State
        # Developer implements fixes for issues identified in review
        #######################
        elif state == "developer":
            dev_iterations += 1
            dev_file = output_dir / f"dev_iter_{iteration}.md"

            # Find the most recent review file
            review_files = sorted(output_dir.glob("review_iter_*.md"))
            latest_review_file = review_files[-1] if review_files else None

            # Find the most recent validation file (if exists)
            validation_files = sorted(output_dir.glob("validation_iter_*.md"))
            latest_validation_file = validation_files[-1] if validation_files else None

            validation_info = ""
            if latest_validation_file:
                validation_info = f"""
You should also review the validator's feedback at {latest_validation_file}
and address any issues they identified.
"""

            dev_prompt = f"""
Think hard about this task. You are Iteration #{iteration}/{args.max_iterations}.

You are a senior developer implementing fixes based on code review feedback.
You're working on changes in {compare_desc}.

Your task is to address all CRITICAL and HIGH priority issues from the latest review.

Steps:
1. Read the latest review report at {latest_review_file}{validation_info}
2. Run an appropriate git diff to understand the current code state
3. Implement fixes for each CRITICAL and HIGH issue using Edit, MultiEdit, or Write tools
4. Run tests if available to verify your fixes
5. Commit your changes with clear messages

Format your output as a markdown document with these sections:
## Summary
[Overview of your changes for iteration {iteration}]

## Issues Fixed
[Details of each CRITICAL/HIGH issue you addressed, with file:line and how you fixed it]

## Implementation Notes
[Technical challenges, decisions made, alternatives considered]

## Test Results
[Results of any tests you ran to verify your fixes]

## Commits
[List of commit IDs for changes made in this iteration]

Start with ## Summary without any introductory text.
"""
            run_claude(
                dev_prompt,
                f"developer_{iteration}",
                dev_file,
                "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write,TodoRead,TodoWrite",
                output_dir,
            )

            # After development, always go back to review
            log("Development completed. Moving back to review state.")
            state = "review"

        #######################
        # Step 3.3.3: Validator State
        # Validator ensures code meets all quality standards
        #######################
        elif state == "validator":
            validation_file = output_dir / f"validation_iter_{iteration}.md"

            # Find the most recent review file
            review_files = sorted(output_dir.glob("review_iter_*.md"))
            latest_review_file = review_files[-1] if review_files else None

            # Find the most recent dev file
            dev_files = sorted(output_dir.glob("dev_iter_*.md"))
            latest_dev_file = dev_files[-1] if dev_files else None

            validation_prompt = f"""
Think hard about this task. You are Iteration #{iteration}/{args.max_iterations}.

You are a validator determining if the code changes meet all quality and functional requirements.
You're validating changes for {compare_desc}.

Steps:
1. Read the latest review report at {latest_review_file}
2. Read the developer's report at {latest_dev_file}
3. Run git diff commands to examine current state of the code
4. Verify all code meets quality standards
5. Run tests if available to verify functionality
6. Look for any issues that might have been missed in the review

Format your validation report as follows:
## Summary
[Overall assessment of the code quality]

## Quality Assessment
[Detailed assessment of code quality, maintainability, test coverage]

## Functional Verification
[Verification that the code works as expected]

## Conclusion
[Final determination with clear reasoning]

Your conclusion MUST end with one of these lines exactly:
VALIDATION: PASSED (if code meets all quality and functional requirements)
VALIDATION: REJECTED (if issues were found that need to be fixed)

Start with ## Summary without any introductory text.
"""
            validation_output = run_claude(
                validation_prompt,
                f"validator_{iteration}",
                validation_file,
                "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch",
                output_dir,
            )

            # Check validation result
            if "VALIDATION: PASSED" in validation_output:
                log(f"Validation PASSED in iteration {iteration}!")
                validation_passed = True
                final_success = True
                break
            else:
                log(f"Validation REJECTED in iteration {iteration}.")
                if iteration < args.max_iterations:
                    log("Moving back to developer state...")
                    state = "developer"
                else:
                    log("Maximum iterations reached without passing validation.")
                    break

    #######################
    # Step 3.4: PR Creation
    # Create PR if validation passed
    #######################
    if validation_passed and not args.skip_pr:
        pr_file = output_dir / "pr_report.md"
        pr_prompt = f"""
Think hard about this task.

You are responsible for creating a pull request for the changes made to {compare_desc}.
Validation has passed, and your task is to create a comprehensive PR.

Steps:
1. Review all the artifacts in the {output_dir} directory
2. Examine the final code changes using appropriate git diff commands
3. Create a pull request with a descriptive title and detailed body
4. Use the GitHub CLI (gh) to create the PR

Format your output as follows:
## PR Title
[A clear, concise title for the PR]

## PR Body
[The complete PR description, formatted in markdown]

## PR Creation Command
[The exact gh pr create command you used]

## PR Creation Result
[The output from the gh pr create command, including URL]

Start with ## PR Title without any introductory text.
"""
        run_claude(pr_prompt, "pr_manager", pr_file, "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch", output_dir)

        log("PR creation completed. Check the PR report for details.")

    #######################
    # Step 3.5: Final Summary
    # Generate summary of the entire process
    #######################
    log("\n=== Review Loop Summary ===")
    log(f"Session ID: {session_id}")
    log(f"Iterations completed: {iteration} of {args.max_iterations}")
    log(f"Total development iterations: {dev_iterations}")
    log(f"Final result: {'SUCCESS' if final_success else 'FAILED'}")
    log(f"All artifacts saved to: {output_dir}")

    # List all artifacts
    log("Artifacts:")
    for file in sorted(output_dir.glob("*.md")):
        log(f"  - {file.name}")

    return 0 if final_success else 1


#######################
# Step 4: Script Entry Point
# Entry point when script is run directly
#######################
if __name__ == "__main__":
    main()
