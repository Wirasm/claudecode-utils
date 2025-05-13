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
            # Resolve the absolute path of the session directory to avoid directory traversal
            resolved_session_dir = session_dir.resolve()

            # Only include files that are within the resolved session directory
            for file in sorted(resolved_session_dir.glob("*.md")):
                # Ensure the file is actually within the session directory to prevent directory traversal
                try:
                    file_resolved = file.resolve()
                    # Check if this file is inside the session directory
                    if file_resolved.is_relative_to(resolved_session_dir):
                        artifacts_info += f"- {file.name}: {file}\n"
                    else:
                        log(f"Warning: Skipping file outside session directory: {file}")
                except (ValueError, RuntimeError) as e:
                    # Handle any path resolution errors
                    log(f"Error validating file path {file}: {e}")
                    continue

        full_prompt = f"""
{artifacts_info}

{prompt}
"""

        # Construct command arguments as a list to prevent command injection
        cmd = [
            "claude",
            "--output-format",
            "text",
            "-p",
            full_prompt,
            "--allowedTools",
            allowed_tools,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1200,  # 20 minute timeout
                shell=False,  # Explicitly disable shell to prevent command injection
            )

            # Save output to file
            with open(output_file, "w") as f:
                f.write(result.stdout)

            log(f"{role.capitalize()} completed and saved to {output_file}")
            return result.stdout

        except subprocess.TimeoutExpired as e:
            log(f"Timeout error running {role}: Process exceeded {e.timeout} seconds")
            error_msg = f"Timeout error: Process exceeded {e.timeout} seconds"
            with open(output_file, "w") as f:
                f.write(f"Error running {role}: {error_msg}")
            return f"Error: {error_msg}"

        except subprocess.CalledProcessError as e:
            log(f"Process error running {role}: Command failed with exit code {e.returncode}")
            error_msg = f"Command failed with exit code {e.returncode}\nStderr: {e.stderr}"
            with open(output_file, "w") as f:
                f.write(f"Error running {role}: {error_msg}")
            return f"Error: {error_msg}"

    except FileNotFoundError as e:
        log(f"File not found error: {e}")
        error_msg = f"File not found: {e}"
        with open(output_file, "w") as f:
            f.write(f"Error running {role}: {error_msg}")
        return f"Error: {error_msg}"

    except PermissionError as e:
        log(f"Permission error: {e}")
        error_msg = f"Permission denied: {e}"
        with open(output_file, "w") as f:
            f.write(f"Error running {role}: {error_msg}")
        return f"Error: {error_msg}"

    except IOError as e:
        log(f"I/O error when running {role}: {e}")
        error_msg = f"I/O error: {e}"
        with open(output_file, "w") as f:
            f.write(f"Error running {role}: {error_msg}")
        return f"Error: {error_msg}"

    except Exception as e:
        # Fallback for any unexpected errors
        log(f"Unexpected error running {role}: {e}")
        error_msg = f"Unexpected error: {e}"
        try:
            with open(output_file, "w") as f:
                f.write(f"Error running {role}: {error_msg}")
        except Exception as write_err:
            log(f"Failed to write error to file: {write_err}")
        return f"Error: {error_msg}"


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

    # Validate directory creation with proper error handling
    try:
        # First check if path exists and is a directory
        if output_dir.exists():
            if not output_dir.is_dir():
                log(f"Error: '{output_dir}' exists but is not a directory")
                return 1

            # Check if we have write permission to the directory
            if not os.access(output_dir, os.W_OK):
                log(f"Error: No write permission to directory '{output_dir}'")
                return 1

            log(f"Using existing directory: {output_dir}")
        else:
            # Create directory with explicit permission checks
            try:
                # First check if parent directory exists and we have write permission
                parent_dir = output_dir.parent
                if not parent_dir.exists():
                    parent_dir.mkdir(parents=True, exist_ok=True)

                if not os.access(parent_dir, os.W_OK):
                    log(f"Error: No write permission to parent directory '{parent_dir}'")
                    return 1

                # Now create the directory
                output_dir.mkdir(parents=True, exist_ok=True)
                log(f"Created directory: {output_dir}")

                # Double-check that the directory was created and we can write to it
                if not output_dir.exists() or not output_dir.is_dir():
                    log(f"Error: Failed to create directory '{output_dir}'")
                    return 1

                if not os.access(output_dir, os.W_OK):
                    log(f"Error: Created directory '{output_dir}' but cannot write to it")
                    return 1
            except PermissionError as e:
                log(f"Permission error creating directory '{output_dir}': {e}")
                return 1
            except OSError as e:
                log(f"OS error creating directory '{output_dir}': {e}")
                return 1

    except Exception as e:
        log(f"Unexpected error validating/creating directory '{output_dir}': {e}")
        return 1

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

    # Track best effort results in case we need to fall back
    best_effort = {
        "review_file": None,
        "review_score": 0,  # Lower is better (count of critical/high issues)
        "dev_file": None,
        "validation_file": None,
        "validation_score": 0,  # Higher is better
    }

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

            # Check if review passed or failed using robust regex pattern matching
            import re

            # Define regex patterns to match the exact review decision phrases
            # Using anchored patterns with line boundaries for exact matches
            passed_pattern = re.compile(r'^REVIEW:\s*PASSED\s*$', re.MULTILINE)
            rejected_pattern = re.compile(r'^REVIEW:\s*REJECTED\s*$', re.MULTILINE)

            # Count critical and high issues to track progress for potential fallback
            critical_pattern = re.compile(r'###\s*CRITICAL.*?(?=###|$)', re.DOTALL | re.MULTILINE)
            high_pattern = re.compile(r'###\s*HIGH.*?(?=###|$)', re.DOTALL | re.MULTILINE)

            critical_section = critical_pattern.search(review_output)
            high_section = high_pattern.search(review_output)

            critical_count = 0
            high_count = 0

            if critical_section:
                critical_count = len(re.findall(r'^\d+\.', critical_section.group(0), re.MULTILINE))

            if high_section:
                high_count = len(re.findall(r'^\d+\.', high_section.group(0), re.MULTILINE))

            issue_score = critical_count * 10 + high_count  # Weight critical issues higher

            # Update best effort tracking if this review has fewer issues
            if best_effort["review_file"] is None or issue_score < best_effort["review_score"]:
                best_effort["review_file"] = review_file
                best_effort["review_score"] = issue_score
                log(f"Saved as best review so far ({critical_count} critical, {high_count} high issues)")

            if passed_pattern.search(review_output):
                log("Review PASSED! Moving to validator state.")
                state = "validator"
            elif rejected_pattern.search(review_output):
                log("Review REJECTED. Moving to developer state.")
                state = "developer"
            else:
                log("Warning: No valid review decision found. Default to developer state.")
                log("Expected 'REVIEW: PASSED' or 'REVIEW: REJECTED' in the output.")
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
            dev_output = run_claude(
                dev_prompt,
                f"developer_{iteration}",
                dev_file,
                "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write,TodoRead,TodoWrite",
                output_dir,
            )

            # Update best effort tracking
            if dev_output and "Error:" not in dev_output:
                best_effort["dev_file"] = dev_file
                log("Saved as best developer output so far")


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

            # Check validation result using robust regex patterns
            import re

            # Define regex patterns to match the exact validation decision phrases
            # Using anchored patterns with line boundaries for exact matches
            passed_pattern = re.compile(r'^VALIDATION:\s*PASSED\s*$', re.MULTILINE)
            rejected_pattern = re.compile(r'^VALIDATION:\s*REJECTED\s*$', re.MULTILINE)

            # Calculate validation score based on quality assessment
            quality_score = 0
            if "high quality" in validation_output.lower():
                quality_score += 3
            if "good quality" in validation_output.lower():
                quality_score += 2
            if "acceptable" in validation_output.lower():
                quality_score += 1
            if "poor quality" in validation_output.lower():
                quality_score -= 2

            # Update best effort tracking
            if best_effort["validation_file"] is None or quality_score > best_effort["validation_score"]:
                best_effort["validation_file"] = validation_file
                best_effort["validation_score"] = quality_score
                log(f"Saved as best validation so far (quality score: {quality_score})")

            if passed_pattern.search(validation_output):
                log(f"Validation PASSED in iteration {iteration}!")
                validation_passed = True
                final_success = True
                break
            elif rejected_pattern.search(validation_output):
                log(f"Validation REJECTED in iteration {iteration}.")
                if iteration < args.max_iterations:
                    log("Moving back to developer state...")
                    state = "developer"
                else:
                    log("Maximum iterations reached without passing validation.")
                    break
            else:
                log(f"Warning: No valid validation decision found in iteration {iteration}.")
                log("Expected 'VALIDATION: PASSED' or 'VALIDATION: REJECTED' in the output.")
                if iteration < args.max_iterations:
                    log("Moving back to developer state by default...")
                    state = "developer"
                else:
                    log("Maximum iterations reached without clear validation result.")
                    break

    #######################
    # Step 3.3.4: Fallback Mechanism
    # If validation failed after all iterations, provide a fallback
    #######################
    if not validation_passed:
        log("\n=== Validation did not pass across all iterations ===")

        # Check if we have any best effort results to fall back to
        if best_effort["review_file"] and best_effort["dev_file"]:
            log("Implementing fallback mechanism: Saving best effort results")

            # Create a fallback summary file
            fallback_file = output_dir / "fallback_summary.md"
            with open(fallback_file, "w") as f:
                f.write(f"""## Fallback Summary
                
The review-develop-validate loop did not complete successfully within {args.max_iterations} iterations.
However, we've preserved the best interim results for manual intervention.

### Best Review
- File: {best_effort["review_file"]}
- Issue score: {best_effort["review_score"]} (lower is better)

### Best Development Attempt
- File: {best_effort["dev_file"]}

{f'''### Best Validation Attempt
- File: {best_effort["validation_file"]}
- Quality score: {best_effort["validation_score"]} (higher is better)''' if best_effort["validation_file"] else ''}

### Next Steps
1. Review the best files identified above
2. Consider manual fixes for remaining issues
3. Use `git diff` to see what changes were made in the best development attempt
4. You may need to selectively apply parts of the changes or modify them
5. Run tests manually to verify any additional changes

This fallback summary was generated automatically by the review loop to help you continue the work manually.
""")

            log(f"Fallback summary saved to {fallback_file}")
            log("Please review this file for next steps")
        else:
            log("No viable fallback information available. Please review the logs manually.")

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
