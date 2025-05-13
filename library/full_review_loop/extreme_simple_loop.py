#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.8"
# dependencies = [] # No external Python deps needed if using Claude CLI
# ///

"""
Super Simple Claude Review Loop

A dead-simple implementation that lets Claude directly read and generate reports
with each Claude instance having full access to all previous artifacts.

Key features:
- Direct Claude-to-Claude communication through shared files
- No complex regex or validation logic in Python
- Each step has full context of previous steps
- KISS principle: minimal Python orchestration code

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


def run_claude(prompt, step_name, output_file, allowed_tools, timeout=1200):
    """Run Claude and save output to file.

    Args:
        prompt: Prompt to send to Claude
        step_name: Name of the step (for logging)
        output_file: Path where to save Claude's response
        allowed_tools: Tools Claude is allowed to use
        timeout: Timeout in seconds
    """
    log(f"Running {step_name}...")

    try:
        result = subprocess.run(
            ["claude", "--output-format", "text", "-p", prompt, "--allowedTools", allowed_tools],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            shell=False,
        )

        # Save output to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(result.stdout)

        log(f"{step_name} completed and saved to {output_file}")
        return result.stdout

    except Exception as e:
        log(f"Error running {step_name}: {e}")
        # Try to save error to file
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(f"Error: {e}")
        except Exception:
            pass
        return f"Error: {e}"


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Super Simple Claude Review Loop")

    # Source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--latest", action="store_true", help="Review latest commit")
    source_group.add_argument("--branch", help="Review branch against base branch")

    # Other options
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison (default: main)")
    parser.add_argument("--output-dir", help="Directory for output files (default: tmp/simple_loop_TIMESTAMP)")
    parser.add_argument("--timeout", type=int, default=1200, help="Timeout in seconds for Claude calls (default: 1200)")
    parser.add_argument("--max-loops", type=int, default=2, help="Maximum review-develop cycles (default: 2)")
    parser.add_argument("--skip-pr", action="store_true", help="Skip PR creation at the end")

    args = parser.parse_args()

    # Set up output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = int(time.time())
        output_dir = Path("tmp") / f"simple_loop_{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine comparison mode for prompt
    if args.latest:
        log("Starting review of latest commit")
        compare_desc = "latest commit against its parent"
    else:
        log(f"Starting review of branch '{args.branch}' against '{args.base_branch}'")
        compare_desc = f"branch '{args.branch}' against '{args.base_branch}'"

    log(f"Output directory: {output_dir}")

    #######################
    # Step 1: Initial Review
    #######################
    review_file = output_dir / "01_review.md"

    review_prompt = f"""
Think hard about this task.

You are a senior code reviewer. Your task is to identify issues in code changes.

First, determine what changes we're reviewing:
{compare_desc}

Steps:
1. First, run the appropriate git diff command to see the changes
2. Analyze the changes thoroughly for issues
3. For each issue, mark its priority (CRITICAL, HIGH, MEDIUM, LOW)
4. For each issue, provide the file path and line number
5. Suggest specific fixes for each issue

Format your review as follows:

## Summary
[Overview of the changes and key issues]

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
[Any strategic or architectural recommendations]

## Review Decision
[Your assessment of whether the code needs fixes]

End your review with ONE of these lines:
- REVIEW: PASSED (if no CRITICAL or HIGH issues found)
- REVIEW: NEEDS_FIXES (if CRITICAL or HIGH issues found)

Start with ## Summary without any introductory text.
"""

    review_output = run_claude(
        review_prompt, "Initial review", review_file, "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch", args.timeout
    )

    # Ask Claude explicitly if fixes are needed
    decision_prompt = f"""
I need your help parsing the review you just created. Please read the review at {review_file} 
and tell me if any fixes are needed. Answer with ONLY ONE of these lines:
DECISION: NEEDS_FIXES
DECISION: PASSED
"""
    
    decision_file = output_dir / "01_decision.md"
    decision_output = run_claude(
        decision_prompt,
        "Review decision parser",
        decision_file,
        "Read", # Only need Read permission
        60  # Short timeout since this is simple
    )
    
    # Check decision
    needs_fixes = "DECISION: NEEDS_FIXES" in decision_output
    
    if needs_fixes:
        log("Review indicates fixes are needed")
    else:
        log("Review passed - no critical/high issues found")

    #######################
    # Loop through development and re-review if needed
    #######################
    loop_count = 0
    final_success = not needs_fixes  # Already successful if first review passed

    while needs_fixes and loop_count < args.max_loops:
        loop_count += 1
        log(f"Starting development-review loop {loop_count}/{args.max_loops}")

        # Development phase
        dev_file = output_dir / f"{(loop_count * 2):02d}_development.md"

        # List all previous reports for context
        previous_reports = "\n".join([f"- {f.relative_to(output_dir)}: {f}" for f in sorted(output_dir.glob("*.md"))])

        dev_prompt = f"""
Think hard about this task.

You are a senior developer implementing fixes based on code review feedback.

Context:
- We're reviewing {compare_desc}
- You have the following reports available:
{previous_reports}

Steps:
1. Read ALL previous reports, especially the most recent review
2. Implement fixes for CRITICAL and HIGH priority issues using Edit, MultiEdit, or Write tools
3. Stage and commit your changes with descriptive messages
4. Run any relevant tests to verify your fixes

Your development report must have these sections:

## Summary
[Overview of the changes you've made]

## Issues Fixed
[Details of each issue you addressed]

## Implementation Notes
[Technical challenges or decisions]

## Test Results
[Results of any tests you ran]

## Commits
[List of commits you made]

Start with ## Summary without any introductory text.
"""

        run_claude(
            dev_prompt,
            f"Developer loop {loop_count}",
            dev_file,
            "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch,Edit,MultiEdit,Write,TodoRead,TodoWrite",
            args.timeout,
        )

        # Re-review phase
        rereview_file = output_dir / f"{(loop_count * 2 + 1):02d}_rereview.md"

        # Updated list of reports including development report
        previous_reports = "\n".join([f"- {f.relative_to(output_dir)}: {f}" for f in sorted(output_dir.glob("*.md"))])

        rereview_prompt = f"""
Think hard about this task.

You are a senior code reviewer re-examining changes after development work.

Context:
- We're reviewing {compare_desc}
- You have the following reports available:
{previous_reports}

Steps:
1. Read ALL previous reports to understand the issues and fixes
2. Run git diff to see the current state of the code
3. Verify if CRITICAL and HIGH priority issues have been properly addressed
4. Check if any new issues were introduced

Format your re-review as follows:

## Summary
[Overview of the changes and current state]

## Addressed Issues
[Which issues were fixed and how well]

## Remaining Issues
[Any issues that still need attention]

## New Issues
[Any new issues introduced]

## Review Decision
[Your assessment of whether the code now meets standards]

End your review with ONE of these lines:
- REVIEW: PASSED (if all CRITICAL and HIGH issues are fixed and code is good)
- REVIEW: NEEDS_FIXES (if there are still CRITICAL or HIGH issues)

Start with ## Summary without any introductory text.
"""

        rereview_output = run_claude(
            rereview_prompt,
            f"Re-review loop {loop_count}",
            rereview_file,
            "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch",
            args.timeout,
        )

        # Ask Claude explicitly if re-review passes
        decision_prompt = f"""
I need your help parsing the re-review you just created. Please read the re-review at {rereview_file} 
and tell me if it passes or needs more fixes. Answer with ONLY ONE of these lines:
DECISION: NEEDS_FIXES
DECISION: PASSED
"""
        
        decision_file = output_dir / f"{(loop_count*2+1):02d}_redecision.md"
        decision_output = run_claude(
            decision_prompt,
            f"Re-review decision parser {loop_count}",
            decision_file,
            "Read", # Only need Read permission
            60  # Short timeout since this is simple
        )
        
        # Check decision
        review_passed = "DECISION: PASSED" in decision_output
        
        if review_passed:
            log(f"Re-review loop {loop_count} PASSED!")
            needs_fixes = False
            final_success = True
            break
        else:
            log(f"Re-review loop {loop_count} still needs fixes")
            if loop_count >= args.max_loops:
                log(f"Reached maximum loops ({args.max_loops}). Stopping.")

    #######################
    # Step 3: Validation (if review passed)
    #######################
    if final_success:
        validation_file = output_dir / f"{(len(list(output_dir.glob('*.md'))) + 1):02d}_validation.md"

        # Updated list of all reports
        previous_reports = "\n".join([f"- {f.relative_to(output_dir)}: {f}" for f in sorted(output_dir.glob("*.md"))])

        validation_prompt = f"""
Think hard about this task.

You are a validator ensuring all quality standards are met after development work.

Context:
- We're reviewing {compare_desc}
- You have the following reports available:
{previous_reports}

Steps:
1. Read ALL previous reports to understand the issues and fixes
2. Run git diff to see the current state of the code
3. Perform a thorough quality check of the codebase
4. Run any tests to verify functionality

Format your validation report as follows:

## Summary
[Overall assessment]

## Quality Assessment
[Detailed assessment of code quality, maintainability, test coverage]

## Functional Verification
[Verification that the code works as expected]

## Validation Decision
[Final determination with clear reasoning]

End your validation with ONE of these lines:
- VALIDATION: PASSED (if code meets all quality and functional requirements)
- VALIDATION: FAILED (if issues were found that need to be fixed)

Start with ## Summary without any introductory text.
"""

        validation_output = run_claude(
            validation_prompt,
            "Final validation",
            validation_file,
            "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch",
            args.timeout,
        )

        # Ask Claude explicitly about validation result
        decision_prompt = f"""
I need your help parsing the validation report you just created. Please read the validation at {validation_file} 
and tell me if it passes or fails. Answer with ONLY ONE of these lines:
DECISION: FAILED
DECISION: PASSED
"""
        
        decision_file = output_dir / f"{(len(list(output_dir.glob('*.md'))) + 1):02d}_valdecision.md"
        decision_output = run_claude(
            decision_prompt,
            "Validation decision parser",
            decision_file,
            "Read", # Only need Read permission
            60  # Short timeout since this is simple
        )
        
        # Check decision
        validation_passed = "DECISION: PASSED" in decision_output
        
        if validation_passed:
            log("Validation PASSED!")
        else:
            log("Validation FAILED - see report for details")
            final_success = False

        # Create PR if validation passed and PR not skipped
        if final_success and not args.skip_pr:
            pr_file = output_dir / f"{(len(list(output_dir.glob('*.md'))) + 1):02d}_pr.md"

            # Updated list of all reports
            previous_reports = "\n".join(
                [f"- {f.relative_to(output_dir)}: {f}" for f in sorted(output_dir.glob("*.md"))]
            )

            pr_prompt = f"""
Think hard about this task.

You are preparing a pull request now that all validation has passed.

Context:
- We're submitting changes for {compare_desc}
- You have the following reports available:
{previous_reports}

Steps:
1. Read ALL reports to understand the full journey of this code
2. Create a comprehensive PR description
3. Push the branch if needed
4. Create the PR using gh cli

Your PR report must include:

## PR Title
[A clear, concise title]

## PR Description
[The complete markdown PR description you used]

## PR Command
[The exact command you used to create the PR]

## PR Result
[The output from the PR creation, including URL]

Start with ## PR Title without any introductory text.
"""

            run_claude(
                pr_prompt, "PR creation", pr_file, "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch", args.timeout
            )

            log("PR creation completed - check PR report for details")

    # Final summary
    log("\n=== Review Loop Summary ===")
    log(f"Output directory: {output_dir}")
    log(f"Total loops completed: {loop_count} of {args.max_loops}")
    log(f"Final outcome: {'SUCCESS' if final_success else 'NEEDS IMPROVEMENT'}")

    # List all artifacts
    log("Artifacts:")
    for file in sorted(output_dir.glob("*.md")):
        log(f"  - {file.name}")

    return 0 if final_success else 1


if __name__ == "__main__":
    main()
