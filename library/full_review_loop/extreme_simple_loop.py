#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.8"
# dependencies = [] # No external Python deps needed if using Claude CLI
# ///

"""
Super Simple Claude Orchestration Script (Revised)

This script orchestrates Claude agents for a review loop, emphasizing
detailed prompting for Claude to manage file I/O directly. Python's role
is minimized to sequencing agents and simple decision checks.

Key principles:
- Claude agents are instructed to read and write their own files.
- Decision logic is simplified by Python checking for specific strings in Claude's output.
- Minimal Python code for orchestration, maximizing reliance on Claude's capabilities.
"""

import argparse
import datetime
import subprocess
import time
from pathlib import Path

# Globals to simplify access in main logic, set by args
OUTPUT_DIR = None
COMPARE_DESC = None
TIMEOUT_SECONDS = 1200
MAX_REVIEW_LOOPS = 2


def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def ensure_output_dir_exists():
    """Ensures the output directory exists, creating it if necessary."""
    global OUTPUT_DIR
    if OUTPUT_DIR is None:  # If --output-dir was not provided
        timestamp = int(time.time())
        OUTPUT_DIR = Path("tmp") / f"simple_loop_{timestamp}"
    else:
        OUTPUT_DIR = Path(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Output directory: {OUTPUT_DIR.resolve()}")


def get_all_artifacts_context():
    """
    Returns a string listing all .md artifacts in OUTPUT_DIR for prompt context.
    Instructs Claude that these files are available for reference.
    """
    if not OUTPUT_DIR or not OUTPUT_DIR.exists():
        return "No previous artifacts exist."

    artifact_files = sorted(OUTPUT_DIR.glob("*.md"))
    if not artifact_files:
        return f"No previous .md artifacts found in the output directory: {OUTPUT_DIR.resolve()}"

    return (
        f"The following artifact files are available in the output directory '{OUTPUT_DIR.resolve()}' for your reference:\n"
        + "\n".join([f"- {f.name}" for f in artifact_files])
        + "\nConsult them as needed by reading their content."
    )


def run_claude_agent(step_name, prompt_content, output_filename, allowed_tools_csv):
    """
    Runs a Claude agent with a given prompt, instructing it to save its output.
    The prompt_content *must* instruct Claude to use its 'Write' tool to save
    its full response to the specified output_filename within OUTPUT_DIR.

    Args:
        step_name: Name of the step (for logging).
        prompt_content: The full prompt for Claude. Should include file saving instructions.
        output_filename: The name of the file Claude should write to (within OUTPUT_DIR).
        allowed_tools_csv: Comma-separated string of tools Claude is allowed to use.

    Returns:
        The content of the output file if successfully created by Claude or fallback,
        otherwise an error message string.
    """
    log(f"Running agent: {step_name}...")
    output_file_path = OUTPUT_DIR / output_filename

    # The prompt_content should already contain the explicit instruction for Claude to save its output.
    # Example instruction to include in prompt_content:
    # f"IMPORTANT: After completing your tasks, save your ENTIRE response to the file:
    # {output_file_path.resolve()}
    # Use the 'Write' tool for this. Ensure the file contains your complete output."

    log(f"  Claude will be instructed to save output to: {output_file_path.resolve()}")

    try:
        command = ["claude", "-p", prompt_content, "--allowedTools", allowed_tools_csv]

        # For debugging long prompts, uncomment cautiously:
        # log(f"  Full prompt for {step_name}:\n{prompt_content[:500]}...")
        log(f"  Executing: claude -p ... --allowedTools {allowed_tools_csv}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,  # Raises CalledProcessError on non-zero exit
            timeout=TIMEOUT_SECONDS,
            shell=False,  # Crucial for security and proper arg handling
        )

        if not output_file_path.exists():
            log(
                f"  WARNING: Agent '{step_name}' did NOT create the output file '{output_file_path.resolve()}' as instructed."
            )
            log(f"  Saving Claude's stdout to '{output_file_path.resolve()}' as a fallback.")
            output_file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent exists
            with open(output_file_path, "w") as f:
                f.write(result.stdout)
            log(f"  Fallback save completed for {step_name}.")
        else:
            log(
                f"  Agent '{step_name}' successfully wrote to '{output_file_path.resolve()}' (as instructed or verified)."
            )

        return output_file_path.read_text()

    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Error running agent '{step_name}' (Exit Code {e.returncode}):\nStdout:\n{e.stdout}\nStderr:\n{e.stderr}"
        )
        log(error_msg)
        # Save error details to the intended output file if possible
        try:
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(error_msg)
        except Exception as save_err:
            log(f"  Additionally, failed to save error details to {output_file_path}: {save_err}")
        return error_msg  # Propagate error state
    except subprocess.TimeoutExpired as e:
        error_msg = (
            f"Error running agent '{step_name}' (Timeout after {TIMEOUT_SECONDS}s):\n"
            f"Stdout:\n{e.stdout}\nStderr:\n{e.stderr}"
        )
        log(error_msg)
        try:
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(error_msg)
        except Exception as save_err:
            log(f"  Additionally, failed to save timeout error details to {output_file_path}: {save_err}")
        return error_msg  # Propagate error state
    except Exception as e:
        error_msg = f"An unexpected error occurred while running agent '{step_name}': {e}"
        log(error_msg)
        try:
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(error_msg)
        except Exception as save_err:
            log(f"  Additionally, failed to save unexpected error details to {output_file_path}: {save_err}")
        return error_msg  # Propagate error state


def parse_decision_from_file_content(file_content, file_path_for_log, pass_string, fail_string):
    """
    Checks file content for decision strings.
    Returns True if pass_string is found, False if fail_string is found or neither.
    """
    if pass_string in file_content:
        return True
    if fail_string in file_content:
        return False

    log(
        f"WARNING: Could not parse decision from '{file_path_for_log.name}'. Neither '{pass_string}' nor '{fail_string}' found. Assuming failure/needs fixes."
    )
    log(f"Content snippet (up to 500 chars):\n{file_content[:500]}")
    return False  # Default to failure/needs_fixes if decision is unclear


def main():
    global OUTPUT_DIR, COMPARE_DESC, TIMEOUT_SECONDS, MAX_REVIEW_LOOPS

    parser = argparse.ArgumentParser(description="Super Simple Claude Orchestration Script")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--latest", action="store_true", help="Review latest commit")
    source_group.add_argument("--branch", help="Review branch against base branch")
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison (default: main)")
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Directory for output files (default: tmp/simple_loop_TIMESTAMP)"
    )
    parser.add_argument("--timeout", type=int, default=1200, help="Timeout in seconds for Claude calls (default: 1200)")
    parser.add_argument("--max-loops", type=int, default=2, help="Maximum review-develop cycles (default: 2)")
    parser.add_argument("--skip-pr", action="store_true", help="Skip PR creation at the end")
    args = parser.parse_args()

    TIMEOUT_SECONDS = args.timeout
    MAX_REVIEW_LOOPS = args.max_loops
    OUTPUT_DIR = args.output_dir  # Handled by ensure_output_dir_exists

    ensure_output_dir_exists()

    if args.latest:
        log("Starting review of latest commit")
        COMPARE_DESC = "the latest commit against its parent"
    else:
        log(f"Starting review of branch '{args.branch}' against '{args.base_branch}'")
        COMPARE_DESC = f"branch '{args.branch}' against base branch '{args.base_branch}'"

    # --- Initial Review Step ---
    initial_review_filename = "01_initial_review.md"
    initial_review_prompt = f"""
Think hard about this task. You are a Senior Code Reviewer.

Your primary goal is to review code changes and produce a detailed report.
The code changes to review are for: {COMPARE_DESC}.
All artifacts, including your report, should be relative to the output directory: {OUTPUT_DIR.resolve()}
{get_all_artifacts_context()}

Your tasks are:
1.  Use git diff commands (or other appropriate git commands) to identify the specific code changes.
2.  Thoroughly analyze these changes for issues: bugs, style violations, performance concerns, security vulnerabilities, unclear logic, etc.
3.  For each identified issue, clearly state its priority (CRITICAL, HIGH, MEDIUM, LOW), the relevant file path, and line number(s).
4.  Provide specific, actionable suggestions for how to fix each issue.
5.  Structure your review report in Markdown format. It MUST include:
    - A "## Summary" section: Brief overview of the changes and key findings.
    - An "## Issue List" section: Detailed list of issues, categorized by priority.
    - A "## Recommendations" section (optional): Broader advice if applicable.
6.  At the VERY END of your entire response, include one of the following lines as the final line:
    - REVIEW_CONCLUSION: NEEDS_FIXES (if any CRITICAL or HIGH priority issues are found)
    - REVIEW_CONCLUSION: PASSED (if no CRITICAL or HIGH priority issues are found)

IMPORTANT: After completing all tasks, you MUST save your ENTIRE response (including the summary, issue list, recommendations, and the final REVIEW_CONCLUSION line) to the file:
{OUTPUT_DIR.resolve() / initial_review_filename}
Use the 'Write' tool for this purpose. Start your report directly with "## Initial Code Review" and no other introductory text.
"""
    review_content = run_claude_agent(
        "Initial Reviewer",
        initial_review_prompt,
        initial_review_filename,
        "Bash,Grep,Read,LS,Glob,Write",  # Removed Task, WebSearch, WebFetch for simplicity unless essential
    )

    passed_initial_review = parse_decision_from_file_content(
        review_content,
        OUTPUT_DIR / initial_review_filename,
        "REVIEW_CONCLUSION: PASSED",
        "REVIEW_CONCLUSION: NEEDS_FIXES",
    )

    current_loop_passed = passed_initial_review
    if current_loop_passed:
        log("Initial review PASSED.")
    else:
        log("Initial review indicates fixes are needed.")

    # --- Development and Re-review Loop ---
    loop_count = 0
    final_success_achieved = current_loop_passed  # True if initial review passed

    while not final_success_achieved and loop_count < MAX_REVIEW_LOOPS:
        loop_count += 1
        log(f"--- Starting Development-Review Iteration {loop_count}/{MAX_REVIEW_LOOPS} ---")

        # Development Phase
        dev_phase_filename = f"{2 * loop_count:02d}_development_iteration_{loop_count}.md"
        # Determine the most recent review file for the developer to read
        last_review_file = (
            initial_review_filename
            if loop_count == 1
            else f"{(2 * (loop_count - 1)) + 1:02d}_rereview_iteration_{loop_count - 1}.md"
        )

        dev_prompt = f"""
Think hard about this task. You are a Senior Developer.

Your goal is to implement fixes based on the latest code review feedback.
The code changes relate to: {COMPARE_DESC}.
All artifacts are in the output directory: {OUTPUT_DIR.resolve()}
{get_all_artifacts_context()}

Your tasks are:
1.  Carefully read ALL previous reports in '{OUTPUT_DIR.resolve()}', paying close attention to the most recent review: '{last_review_file}'.
2.  Identify all CRITICAL and HIGH priority issues listed in that review.
3.  Implement the necessary code changes to address these identified issues. Use 'Edit', 'MultiEdit', or 'Write' tools as appropriate.
4.  After making changes, stage and commit them using git. Use clear, descriptive commit messages.
5.  (Optional) If applicable, run any relevant tests to verify your fixes.
6.  Produce a development report in Markdown. It MUST include:
    - "## Summary of Changes": What you did.
    - "## Issues Addressed": Which specific issues from the review you fixed.
    - "## Commits Made": List of git commits.

IMPORTANT: After completing all tasks, you MUST save your ENTIRE development report to the file:
{OUTPUT_DIR.resolve() / dev_phase_filename}
Use the 'Write' tool. Start your report with "## Development Fixes - Iteration {loop_count}" and no other introductory text.
"""
        run_claude_agent(
            f"Developer (Iteration {loop_count})",
            dev_prompt,
            dev_phase_filename,
            "Bash,Grep,Read,LS,Glob,Edit,MultiEdit,Write,TodoRead,TodoWrite",
        )

        # Re-review Phase
        rereview_filename = f"{(2 * loop_count) + 1:02d}_rereview_iteration_{loop_count}.md"
        rereview_prompt = f"""
Think hard about this task. You are a Senior Code Reviewer conducting a re-review.

The code changes relate to: {COMPARE_DESC}.
All artifacts are in the output directory: {OUTPUT_DIR.resolve()}
{get_all_artifacts_context()}

Your tasks are:
1.  Read ALL previous reports in '{OUTPUT_DIR.resolve()}', especially the initial review, and the latest development report ('{dev_phase_filename}').
2.  Use git diff (or similar git commands) to examine the latest code changes made by the developer.
3.  Verify if the CRITICAL and HIGH priority issues identified in the previous review cycle have been adequately addressed.
4.  Check if any new issues (CRITICAL or HIGH) were introduced by the fixes.
5.  Format your re-review report in Markdown. It MUST include:
    - "## Re-review Summary"
    - "## Addressed Issues": Confirmation of fixes.
    - "## Remaining Issues": Any old issues not fully fixed.
    - "## New Issues": Any new problems found.
6.  At the VERY END of your entire response, include one of the following lines as the final line:
    - REVIEW_CONCLUSION: PASSED (if all CRITICAL/HIGH issues are resolved and no new major ones)
    - REVIEW_CONCLUSION: NEEDS_FIXES (otherwise)

IMPORTANT: After completing all tasks, you MUST save your ENTIRE re-review report to the file:
{OUTPUT_DIR.resolve() / rereview_filename}
Use the 'Write' tool. Start your report with "## Re-review - Iteration {loop_count}" and no other introductory text.
"""
        rereview_content = run_claude_agent(
            f"Re-reviewer (Iteration {loop_count})", rereview_prompt, rereview_filename, "Bash,Grep,Read,LS,Glob,Write"
        )

        current_loop_passed = parse_decision_from_file_content(
            rereview_content,
            OUTPUT_DIR / rereview_filename,
            "REVIEW_CONCLUSION: PASSED",
            "REVIEW_CONCLUSION: NEEDS_FIXES",
        )

        if current_loop_passed:
            log(f"Re-review (Iteration {loop_count}) PASSED.")
            final_success_achieved = True  # This iteration was successful
            # break # Exit loop as fixes are satisfactory
        else:
            log(f"Re-review (Iteration {loop_count}) still needs fixes.")
            if loop_count >= MAX_REVIEW_LOOPS:
                log(f"Maximum review loops ({MAX_REVIEW_LOOPS}) reached. Process did not pass this stage.")
                final_success_achieved = False  # Ensure it's marked as not successful

    # --- Validation Step (if all reviews passed) ---
    validation_succeeded = False
    if final_success_achieved:
        log("--- Starting Final Validation Step ---")
        validation_filename = f"{len(list(OUTPUT_DIR.glob('*.md'))) + 1:02d}_validation.md"
        validation_prompt = f"""
Think hard about this task. You are a Quality Assurance Validator.

The code changes relate to: {COMPARE_DESC}.
All artifacts are in the output directory: {OUTPUT_DIR.resolve()}
{get_all_artifacts_context()}

Your tasks are:
1.  Thoroughly review ALL previous reports in '{OUTPUT_DIR.resolve()}' to understand the full history.
2.  Perform a final quality check on the current state of the code (use git diff if needed).
3.  Assess overall code quality, maintainability, and whether all initial requirements appear met.
4.  Describe any conceptual tests you would run or expect to see.
5.  Format your validation report in Markdown. Include:
    - "## Overall Assessment"
    - "## Quality Checklist Verification"
    - "## Functional Verification (Conceptual)"
6.  At the VERY END of your entire response, include one of the following lines as the final line:
    - VALIDATION_CONCLUSION: PASSED (if code meets all quality and functional requirements)
    - VALIDATION_CONCLUSION: FAILED (if significant issues are found)

IMPORTANT: After completing all tasks, you MUST save your ENTIRE validation report to the file:
{OUTPUT_DIR.resolve() / validation_filename}
Use the 'Write' tool. Start your report with "## Final Validation Report" and no other introductory text.
"""
        validation_content = run_claude_agent(
            "Final Validator", validation_prompt, validation_filename, "Bash,Grep,Read,LS,Glob,Write"
        )
        validation_succeeded = parse_decision_from_file_content(
            validation_content,
            OUTPUT_DIR / validation_filename,
            "VALIDATION_CONCLUSION: PASSED",
            "VALIDATION_CONCLUSION: FAILED",
        )
        if validation_succeeded:
            log("Validation PASSED.")
        else:
            log("Validation FAILED.")
            final_success_achieved = False  # Overall success is now false
    elif not final_success_achieved:
        log("Skipping Validation step because prior reviews did not pass.")

    # --- PR Creation Step (if all successful and not skipped) ---
    if final_success_achieved and validation_succeeded and not args.skip_pr:
        log("--- Starting PR Creation Details Step ---")
        pr_filename = f"{len(list(OUTPUT_DIR.glob('*.md'))) + 1:02d}_pr_details.md"
        pr_prompt = f"""
Think hard about this task. You are a Release Engineer preparing a Pull Request.

The code changes for submission relate to: {COMPARE_DESC}.
All artifacts are in the output directory: {OUTPUT_DIR.resolve()}
{get_all_artifacts_context()}

All reviews and validation have passed. Your task is to outline the Pull Request details.

Your tasks are:
1.  Review ALL reports in '{OUTPUT_DIR.resolve()}' to synthesize a comprehensive PR description.
2.  Formulate a clear and concise PR Title.
3.  Detail the exact `gh pr create ...` command you would use (or equivalent for other platforms).
4.  Describe the expected output or result of successfully creating the PR (e.g., PR URL).
5.  Format your response in Markdown. Include:
    - "## PR Title"
    - "## PR Description" (Full Markdown for the PR body)
    - "## PR Command"
    - "## Expected PR Result"

IMPORTANT: After completing all tasks, you MUST save your ENTIRE report on PR creation to the file:
{OUTPUT_DIR.resolve() / pr_filename}
Use the 'Write' tool. Start your report with "## Pull Request Details" and no other introductory text.
"""
        run_claude_agent(
            "PR Creator",
            pr_prompt,
            pr_filename,
            "Bash,Grep,Read,LS,Glob,Write",  # Bash for gh command formulation
        )
        log(f"PR creation details saved to '{pr_filename}'.")
    elif not args.skip_pr:
        log("Skipping PR creation step due to failures in review or validation.")

    if args.skip_pr:
        log("PR creation skipped as per --skip-pr flag.")

    # --- Final Summary ---
    log("\n=== Review Loop Summary ===")
    log(f"Output directory: {OUTPUT_DIR.resolve()}")
    log(f"Total review-develop iterations completed: {loop_count} (max allowed: {MAX_REVIEW_LOOPS})")

    overall_outcome_status = "UNKNOWN"
    if final_success_achieved and validation_succeeded:
        overall_outcome_status = "SUCCESS"
    elif final_success_achieved and not validation_succeeded:
        overall_outcome_status = "FAILED VALIDATION"
    else:  # Not final_success_achieved (implies review loops failed or initial review failed and no loops run)
        overall_outcome_status = "NEEDS IMPROVEMENT / FAILED REVIEW CYCLES"

    log(f"Final Outcome: {overall_outcome_status}")

    log("Artifacts generated:")
    for file_path in sorted(OUTPUT_DIR.glob("*.md")):
        log(f"  - {file_path.name}")

    return 0 if final_success_achieved and validation_succeeded else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
