#!/usr/bin/env -S uv run --script

"""
Agentic Review Loop

A collaborative workflow that orchestrates multiple Claude instances to review, develop, validate and create PRs.

This script:
1. Runs a Reviewer to analyze code changes and identify issues
2. Runs a Developer to implement fixes for issues found
3. Runs a Validator to verify fixes and ensure quality
4. Runs a PR Manager to create a pull request when all issues are fixed

Usage:
    # Compare latest commit to its parent (most common use case)
    uv run python library/full_review_loop/full_review_loop_poc.py --latest

    # Compare a specific branch to main
    uv run python library/full_review_loop/full_review_loop_poc.py --branch feature-branch

    # Compare current branch to another branch
    uv run python library/full_review_loop/full_review_loop_poc.py --branch feature-branch --base-branch development

Options:
    --latest              Compare latest commit to previous commit (HEAD vs HEAD~1)
    --branch BRANCH       Branch to review (compared to base-branch)
    --base-branch BRANCH  Base branch for comparison (default: main)
    --max-iterations N    Maximum number of improvement cycles (default: 3)
    --output-dir DIR      Directory for output files (default: tmp/agentic_loop_TIMESTAMP)
    --verbose, -v         Show verbose output
    --no-pr               Skip PR creation even if validation passes
    --pr-title TITLE      Custom title for PR (default: auto-generated)
    --timeout N           Timeout in seconds for each agent (default: 600 - 10 mins)

Examples:
    # Review latest commit
    uv run python library/full_review_loop/full_review_loop_poc.py --latest --verbose

    # Review feature branch compared to main
    uv run python library/full_review_loop/full_review_loop_poc.py --branch feature-branch --verbose

    # Review with custom settings
    uv run python library/full_review_loop/full_review_loop_poc.py --latest --max-iterations 5 --output-dir my_review --pr-title "Add configuration API"
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path


class AgentRole(Enum):
    """Roles for the different agents in the loop"""

    REVIEWER = "reviewer"
    DEVELOPER = "developer"
    VALIDATOR = "validator"
    PR_MANAGER = "pr_manager"


class AgenticReviewLoop:
    """
    Coordinates the review, development, validation, and PR creation workflow
    using multiple Claude instances.

    The workflow uses multiple agents (reviewer, developer, validator, PR manager)
    with configurable timeouts. By default, each agent has a 10-minute (600 seconds) timeout
    which has been reduced from the previous 30-minute default for better efficiency.
    """

    def __init__(
        self,
        latest_commit=False,
        branch=None,
        base_branch="main",
        max_iterations=3,
        output_dir=None,
        verbose=False,
        skip_pr=False,
        pr_title=None,
        timeout=600,  # Reduced timeout to 10 minutes by default
    ):
        """
        Initialize the agentic review loop with the given configuration.

        Args:
            latest_commit: Whether to compare latest commit to previous
            branch: Branch to review (compared to base_branch)
            base_branch: Base branch for comparison
            max_iterations: Maximum number of improvement cycles
            output_dir: Directory for output files
            verbose: Show verbose output
            skip_pr: Skip PR creation even if validation passes
            pr_title: Custom title for PR
            timeout: Timeout in seconds for each agent (default: 600 seconds/10 minutes)
        """
        # Set up basic config
        self.latest_commit = latest_commit
        self.branch = branch or self._get_current_branch()
        self.base_branch = base_branch
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.skip_pr = skip_pr
        self.pr_title = pr_title
        self.timeout = timeout
        self.iteration = 0

        # Determine comparison command
        if self.latest_commit:
            self.compare_cmd = "HEAD~1...HEAD"
            self.compare_desc = "latest commit vs parent"
        else:
            self.compare_cmd = f"{self.base_branch}...{self.branch}"
            self.compare_desc = f"branch '{self.branch}' vs '{self.base_branch}'"

        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = int(time.time())
            self.output_dir = Path("tmp") / f"agentic_loop_{timestamp}"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up output files
        self.review_file = self.output_dir / "review.md"
        self.dev_report_file = self.output_dir / "dev_report.md"
        self.validation_file = self.output_dir / "validation.md"
        self.pr_file = self.output_dir / "pr.md"

        # Initialize sessions
        self.session_id = str(uuid.uuid4())
        self.log(f"Initialized Agentic Review Loop [session: {self.session_id}]")
        self.log(f"Comparing: {self.compare_desc}")
        self.log(f"Max iterations: {self.max_iterations}")
        self.log(f"Output directory: {self.output_dir}")

    def _get_current_branch(self):
        """Get the name of the current git branch"""
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            self.log("Error: Not in a git repository or git command failed")
            sys.exit(1)

    def log(self, message):
        """Log a message, always shown regardless of verbose setting"""
        print(f"[AgenticLoop] {message}")

    def debug(self, message):
        """Log a debug message, only shown in verbose mode"""
        if self.verbose:
            print(f"[AgenticLoop:DEBUG] {message}")

    def run_claude(self, prompt, role, allowed_tools=None, timeout=None):
        """
        Run a Claude instance with the given prompt and tools.

        Args:
            prompt: The prompt to send to Claude
            role: The role of the agent (for logging)
            allowed_tools: List of tools to allow Claude to use
            timeout: Timeout in seconds (defaults to self.timeout)

        Returns:
            The output from Claude
        """
        start_time = time.time()
        self.log(f"Running {role.value.capitalize()} agent...")
        self.debug(f"Prompt length: {len(prompt)} characters")

        # Configure default allowed tools if not specified
        if allowed_tools is None:
            if role == AgentRole.REVIEWER:
                # Reviewer only needs to read and analyze
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task"
            elif role == AgentRole.DEVELOPER:
                # Developer needs to read, analyze, and modify code
                allowed_tools = (
                    "Bash,Grep,Read,LS,Glob,Task,Edit,MultiEdit,Write,TodoRead,TodoWrite"
                )
            elif role == AgentRole.VALIDATOR:
                # Validator only needs to read and analyze
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task"
            elif role == AgentRole.PR_MANAGER:
                # PR Manager needs to create PRs via GitHub CLI
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task"

        # Always use file-based input for security
        # This prevents command line escaping issues with shlex.quote when handling untrusted data
        prompt_file = None

        try:
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
                prompt_file = f.name
                f.write(prompt)
            self.debug(f"Using file-based input for prompt: {prompt_file}")

            # Build Claude command
            cmd = ["claude", "--output-format", "text", "-f", prompt_file]

            # Add allowed tools if specified
            if allowed_tools:
                cmd.extend(["--allowedTools", allowed_tools])

            # Set timeout if specified
            _timeout = timeout or self.timeout

            # Run Claude
            self.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=_timeout
            )

            output = result.stdout

            # Check for empty output
            if not output.strip():
                self.log(f"Warning: Empty output from {role.value} agent")
                if result.stderr:
                    self.debug(f"stderr: {result.stderr[:500]}...")
                output = (
                    f"# {role.value.capitalize()} Report\n\nNo content was returned from Claude."
                )

            # Log execution time
            duration = time.time() - start_time
            self.log(f"{role.value.capitalize()} agent completed in {duration:.1f} seconds")
            self.debug(f"Output length: {len(output)} characters")

            return output

        except subprocess.TimeoutExpired:
            self.log(f"Error: {role.value.capitalize()} agent timed out after {_timeout} seconds")
            return f"# {role.value.capitalize()} Report\n\nThe agent timed out after {_timeout} seconds."
        except subprocess.CalledProcessError as e:
            self.log(f"Error running {role.value.capitalize()} agent: {e}")
            self.debug(f"stderr: {e.stderr}")
            return f"# {role.value.capitalize()} Report\n\nAn error occurred: {e}"
        except Exception as e:
            self.log(f"Unexpected error: {e}")
            return f"# {role.value.capitalize()} Report\n\nAn unexpected error occurred: {e}"
        finally:
            # Clean up the prompt file if we created one and it still exists
            if prompt_file and os.path.exists(prompt_file):
                try:
                    os.unlink(prompt_file)
                except Exception as e:
                    self.debug(f"Error cleaning up temporary file: {e}")

    def run_reviewer(self):
        """
        Run the Reviewer agent to analyze code and identify issues.

        Returns:
            bool: Whether the review was successful
        """
        self.log(f"Starting review phase (iteration {self.iteration}/{self.max_iterations})...")

        # Create reviewer prompt
        prompt = f"""
Think hard about this task.

You are a senior code reviewer examining the changes in {self.compare_desc}.
Your task is to provide a thorough, critical review focused on:

1. Code quality and best practices
2. Architectural consistency 
3. Error handling completeness
4. Input/output validation
5. Security issues
6. Performance concerns
7. Test coverage and quality

For each issue found:
1. Mark as CRITICAL, HIGH, MEDIUM, or LOW priority
2. Provide the file path and line number where the issue occurs
3. Explain the issue clearly with technical reasoning
4. Suggest a specific, actionable fix

First, run the following command to see what has changed:
```bash
git diff {self.compare_cmd}
```

Focus on understanding the changes and their context. Be thorough in your analysis.

Write your review in markdown format with the following sections:
1. Summary (overall assessment and key themes)
2. Issue List (all issues categorized by priority)
3. Recommendations (strategic suggestions beyond specific fixes)

Your review will be automatically saved and provided to a developer agent who will implement fixes.
Be thorough yet constructive in your feedback.
"""

        # Run reviewer agent
        output = self.run_claude(prompt, AgentRole.REVIEWER)

        # Save output to file
        with open(self.review_file, "w") as f:
            f.write(output)

        self.log(f"Review saved to {self.review_file}")

        # Review is considered successful if we got some output
        return len(output.strip()) > 0

    def run_developer(self):
        """
        Run the Developer agent to implement fixes based on the review.

        Returns:
            bool: Whether the development was successful
        """
        self.log(
            f"Starting development phase (iteration {self.iteration}/{self.max_iterations})..."
        )

        # Check that review file exists
        if not self.review_file.exists():
            self.log(f"Error: Review file not found at {self.review_file}")
            return False

        # Create developer prompt
        prompt = f"""
Think hard about this task.

You are a senior developer implementing fixes based on a code review.
Your task is to:

1. Read the review at {self.review_file}
2. Create a plan to address all CRITICAL and HIGH priority issues
3. Implement fixes for these issues one by one
4. Test your changes to ensure they work properly
5. Document your changes clearly

First, read the review file to understand the issues, then run this command to see the code:
```bash
git diff {self.compare_cmd}
```

Then implement fixes for all CRITICAL and HIGH priority issues:
1. Understand each issue thoroughly
2. Plan your approach to fixing it
3. Implement the solution using Edit, MultiEdit, or Write tools
4. Verify your fix addresses the issue
5. Run appropriate tests to ensure quality

Write your development report in markdown format with the following sections:
1. Summary (overview of what you fixed and general approach)
2. Issues Fixed (detail on each issue and how you fixed it)
   - 2.1 CRITICAL Issues
   - 2.2 HIGH Priority Issues
3. Implementation Notes (any challenges encountered or alternatives considered)
4. Test Results (results of running tests after your changes)
5. Next Steps (any issues that couldn't be fixed or require further work)

Your report will be automatically saved and provided to a validator agent who will verify your fixes.
Focus on implementing high-quality fixes that address the root causes of the issues.
"""

        # Run developer agent
        output = self.run_claude(prompt, AgentRole.DEVELOPER)

        # Save output to file
        with open(self.dev_report_file, "w") as f:
            f.write(output)

        self.log(f"Development report saved to {self.dev_report_file}")

        # Development is considered successful if we got some output
        return len(output.strip()) > 0

    def run_validator(self):
        """
        Run the Validator agent to verify fixes and ensure quality.

        Returns:
            tuple: (success, validation_passed)
        """
        self.log(f"Starting validation phase (iteration {self.iteration}/{self.max_iterations})...")

        # Check that review and development report files exist
        if not self.review_file.exists():
            self.log(f"Error: Review file not found at {self.review_file}")
            return False, False

        if not self.dev_report_file.exists():
            self.log(f"Error: Development report file not found at {self.dev_report_file}")
            return False, False

        # Create validator prompt
        prompt = f"""
Think hard about this task.

You are a validator responsible for ensuring code quality after development changes.
Your task is to:

1. Read the original review at {self.review_file}
2. Read the development report at {self.dev_report_file}
3. Run 'git diff {self.compare_cmd}' to see all current changes
4. Verify that ALL CRITICAL and HIGH issues from the review have been fixed
5. Run appropriate tests to ensure quality
6. Check code quality, focusing on:
   - Proper error handling
   - Input validation
   - Security concerns
   - Consistent patterns and utilities
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
Then thoroughly analyze the current state of the code to determine if ALL issues have been properly addressed.
"""

        # Run validator agent
        output = self.run_claude(prompt, AgentRole.VALIDATOR)

        # Save output to file
        with open(self.validation_file, "w") as f:
            f.write(output)

        self.log(f"Validation report saved to {self.validation_file}")

        # Check validation result
        validation_passed = "VALIDATION: PASSED" in output
        self.log(f"Validation {'PASSED' if validation_passed else 'FAILED'}")

        # Validation is considered successful if we got some output
        return len(output.strip()) > 0, validation_passed

    def run_pr_manager(self):
        """
        Run the PR Manager agent to create a pull request.

        Returns:
            bool: Whether the PR creation was successful
        """
        self.log(f"Starting PR creation phase...")

        # Check that validation file exists
        if not self.validation_file.exists():
            self.log(f"Error: Validation file not found at {self.validation_file}")
            return False

        # Check that PR hasn't been disabled
        if self.skip_pr:
            self.log("PR creation skipped due to --no-pr flag")
            return False

        # Create PR title if not provided
        title = self.pr_title
        if not title:
            # Try to generate a sensible title from branch or latest commit
            if self.latest_commit:
                try:
                    title = subprocess.check_output(
                        ["git", "log", "-1", "--pretty=%s"], text=True
                    ).strip()
                except subprocess.SubprocessError:
                    title = "Changes from latest commit"
            else:
                # Use branch name with formatting
                clean_branch = self.branch.replace("-", " ").title()
                title = f"Changes from {clean_branch} branch"

        # Create PR manager prompt
        prompt = f"""
Think hard about this task.

You are a PR manager responsible for preparing a high-quality pull request.
Your task is to:

1. Read ALL previous reports to gather comprehensive context:
   - Read the original review at {self.review_file}
   - Read the development report at {self.dev_report_file}
   - Read the validation report at {self.validation_file} to confirm validation has passed

2. Only proceed if validation shows "VALIDATION: PASSED"

3. Run these commands to understand the changes fully:
   - git diff {self.compare_cmd} --name-only  (to see which files changed)
   - git diff {self.compare_cmd}  (to see the actual changes)
   - git log -1 --pretty=format:"%s%n%n%b"  (to see the commit message)

4. Create a comprehensive PR description including:
   - Summary of changes
   - List of specific issues fixed (from the review)
   - Implementation details (from the dev report)
   - Validation results (from the validation report)
   - Testing performed
   - Any known limitations or future work

Follow these steps:
1. First, read all reports thoroughly to gather complete context

2. Next, check if validation has passed. Only proceed if it shows "VALIDATION: PASSED"

3. Run the git commands listed above to analyze what has changed

4. Generate a PR description with the following sections:
   ## Changes
   [Summary of what was changed and why]

   ## Issues Addressed
   [List of specific issues that were fixed, sourced from the review report]

   ## Implementation Details
   [Key implementation decisions and approaches from the dev report]

   ## Validation
   [Summary of validation results]

   ## Testing
   [Summary of tests performed]

   ## Notes
   [Any other information or future considerations]

5. Push the branch and create the PR using these commands:
   - git push -u origin {self.branch}
   - Create a PR description file: echo "$PR_DESCRIPTION" > pr_desc.md
   - Create PR: gh pr create --base {self.base_branch} --head {self.branch} --title "{title}" --body-file pr_desc.md

Make sure the PR description is thorough yet concise, focusing on what reviewers need to know.
Include the PR URL at the end of your report.
"""

        # Run PR manager agent
        output = self.run_claude(prompt, AgentRole.PR_MANAGER)

        # Save output to file
        with open(self.pr_file, "w") as f:
            f.write(output)

        self.log(f"PR report saved to {self.pr_file}")

        # Check if PR was created by looking for PR URL
        pr_url_match = re.search(r"https://github\.com/[^/]+/[^/]+/pull/\d+", output)
        if pr_url_match:
            pr_url = pr_url_match.group(0)
            self.log(f"PR created successfully: {pr_url}")
            return True
        else:
            self.log("PR may not have been created. Check the PR report for details.")
            return False

    def run(self):
        """
        Run the full agentic review loop workflow.

        Returns:
            bool: Whether the workflow completed successfully with validation passing
        """
        self.log(f"Starting agentic review loop...")
        validation_passed = False

        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.log(f"=== Starting iteration {self.iteration}/{self.max_iterations} ===")

            # Run review phase
            review_success = self.run_reviewer()
            if not review_success:
                self.log("Review phase failed. Stopping loop.")
                break

            # Run development phase
            dev_success = self.run_developer()
            if not dev_success:
                self.log("Development phase failed. Stopping loop.")
                break

            # Run validation phase
            validation_success, validation_passed = self.run_validator()
            if not validation_success:
                self.log("Validation phase failed. Stopping loop.")
                break

            # If validation passed, run PR phase and exit
            if validation_passed:
                self.log("Validation passed!")

                if not self.skip_pr:
                    self.log("Running PR creation phase...")
                    pr_success = self.run_pr_manager()
                    if pr_success:
                        self.log("PR phase completed successfully.")
                    else:
                        self.log("PR phase failed.")
                else:
                    self.log("PR creation skipped due to --no-pr flag.")

                break
            else:
                self.log("Validation failed. Starting next iteration.")

        # Check if we hit max iterations
        if self.iteration == self.max_iterations and not validation_passed:
            self.log(
                f"Reached maximum iterations ({self.max_iterations}) without passing validation."
            )

        self.log(f"Agentic review loop completed.")
        self.log(f"Output artifacts are in: {self.output_dir}")

        # Summarize artifacts
        self.log("Artifacts:")
        self.log(f"  Review: {self.review_file}")
        self.log(f"  Development Report: {self.dev_report_file}")
        self.log(f"  Validation Report: {self.validation_file}")
        if not self.skip_pr:
            self.log(f"  PR Report: {self.pr_file}")

        return validation_passed


def main():
    parser = argparse.ArgumentParser(
        description="Run an agentic review loop with multiple Claude instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review latest commit
  uv run python scripts/agentic_review_loop.py --latest --verbose
  
  # Review feature branch compared to main
  uv run python scripts/agentic_review_loop.py --branch feature-branch --verbose
  
  # Review with custom settings
  uv run python scripts/agentic_review_loop.py --latest --max-iterations 5 --output-dir my_review --pr-title "Add configuration API"
        """,
    )

    # Comparison mode (mutually exclusive)
    comparison_group = parser.add_mutually_exclusive_group(required=True)
    comparison_group.add_argument(
        "--latest",
        action="store_true",
        help="Compare latest commit to previous commit (HEAD vs HEAD~1)",
    )
    comparison_group.add_argument(
        "--branch", metavar="BRANCH", help="Branch to review (compared to base-branch)"
    )

    # Additional options
    parser.add_argument(
        "--base-branch", default="main", help="Base branch for comparison (default: main)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of improvement cycles (default: 3)",
    )
    parser.add_argument(
        "--output-dir", help="Directory for output files (default: tmp/agentic_loop_TIMESTAMP)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--no-pr", action="store_true", help="Skip PR creation even if validation passes"
    )
    parser.add_argument("--pr-title", help="Custom title for PR (default: auto-generated)")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds for each agent (default: 600 - 10 mins)",
    )

    args = parser.parse_args()

    # Create and run agentic loop
    loop = AgenticReviewLoop(
        latest_commit=args.latest,
        branch=args.branch,
        base_branch=args.base_branch,
        max_iterations=args.max_iterations,
        output_dir=args.output_dir,
        verbose=args.verbose,
        skip_pr=args.no_pr,
        pr_title=args.pr_title,
        timeout=args.timeout,
    )

    try:
        success = loop.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error during agentic loop execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
