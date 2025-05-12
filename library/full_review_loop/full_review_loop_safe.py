#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.8"
# dependencies = [] # No external Python deps needed if using Claude CLI
# ///

"""
Agentic Review Loop v2

A collaborative workflow that orchestrates multiple Claude instances to review,
develop, validate and create PRs within a safe, temporary environment.

Key Features:
- **Automatic Branching:** Creates a temporary branch by default (e.g., feature-branch-agentic-TIMESTAMP)
  to avoid modifying the original branch directly.
- **Optional Worktree Isolation:** Use `--worktree` to run the entire process within a
  dedicated git worktree directory for better isolation.
- **Iterative Improvement:** Runs Reviewer -> Developer -> Re-Reviewer -> Validator loop.
- **Feedback Loop:** If validation fails, the Developer agent receives the validation feedback
  to attempt fixes in the next iteration.
- **PR Creation:** Creates a pull request via `gh` CLI upon successful validation (can be skipped).

Usage:
    # Review latest commit in a new temp branch (default behavior)
    uv run python library/full_review_loop/full_review_loop_safe.py --latest

    # Review a specific branch in a new temp branch, using a worktree
    uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --worktree

    # Specify base branch and keep temporary branch after run
    uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --base-branch develop --keep-branch

Options:
    --latest              Compare latest commit to previous commit (HEAD vs HEAD~1)
    --branch BRANCH       Source branch to create the temporary work branch from
    --base-branch BRANCH  Base branch for comparison in diffs and PR (default: main)
    --worktree            Run the entire process within a dedicated git worktree
    --keep-branch         Do not delete the temporary work branch after completion
    --max-iterations N    Maximum number of improvement cycles (default: 3)
    --output-dir DIR      Directory for output files (default: tmp/agentic_loop_TIMESTAMP)
    --verbose, -v         Show verbose output
    --no-pr               Skip PR creation even if validation passes
    --pr-title TITLE      Custom title for PR (default: auto-generated)
    --timeout N           Timeout in seconds for each agent (default: 600 - 10 mins)

Examples:
    # Review latest commit in temp branch, verbose output
    uv run python library/full_review_loop/full_review_loop_safe.py --latest --verbose

    # Review feature-branch vs main in temp branch + worktree, keep branch
    uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --worktree --keep-branch --verbose

    # Review latest commit, 5 iterations, custom output dir
    uv run python library/full_review_loop/full_review_loop_safe.py --latest --max-iterations 5 --output-dir my_review
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


def validate_git_branch_name(branch_name):
    """
    Validate that a branch name follows Git's branch naming rules.
    Git branch names cannot:
    - Contain control characters or spaces
    - Begin or end with a slash
    - Contain two consecutive dots (..)
    - Contain the sequence @{
    - Begin with a dash or contain multiple consecutive dashes
    - End with .lock
    - Contain a backslash or control characters

    Args:
        branch_name (str): The branch name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not branch_name or not isinstance(branch_name, str):
        return False

    # Check for common Git branch name restrictions
    invalid_patterns = [
        r"^\s",  # Leading whitespace
        r"\s$",  # Trailing whitespace
        r"\s",  # Spaces
        r"\.{2,}",  # Two or more consecutive dots
        r"@\{",  # The sequence @{
        r"^-",  # Beginning with a dash
        r"--+",  # Two or more consecutive dashes
        r"\.lock$",  # Ending with .lock
        r"[\x00-\x1F]",  # Control characters
        r"[~^:?*[\]]",  # Special Git chars
        r"\\",  # Backslash
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, branch_name):
            return False

    # Final check: branch name cannot begin or end with slash or contain consecutive slashes
    if branch_name.startswith("/") or branch_name.endswith("/") or "//" in branch_name:
        return False

    return True


def validate_directory_path(path):
    """
    Validate that a directory path is safe to use.
    Path should:
    - Be a string or Path object
    - Not contain null bytes
    - Not contain path traversal attempts
    - Exist and be a directory if already on the filesystem

    Args:
        path: The path to validate (string or Path object)

    Returns:
        bool: True if valid, False otherwise
    """
    if path is None:
        return False

    # Convert to string if it's a Path object
    path_str = str(path) if isinstance(path, Path) else path

    # Check that it's a string
    if not isinstance(path_str, str):
        return False

    # Check for null bytes
    if "\0" in path_str:
        return False

    # Check for path traversal attempts
    normalized = os.path.normpath(path_str)
    if "../" in normalized or normalized.startswith(".."):
        return False

    # If the path exists, make sure it's a directory
    if os.path.exists(path_str) and not os.path.isdir(path_str):
        return False

    return True


class AgentRole(Enum):
    """Roles for the different agents in the loop"""

    REVIEWER = "reviewer"
    DEVELOPER = "developer"
    VALIDATOR = "validator"
    PR_MANAGER = "pr_manager"


class AgenticReviewLoop:
    """
    Coordinates the review, development, validation, and PR creation workflow
    using multiple Claude instances within a temporary branch and optional worktree.
    """

    def __init__(
        self,
        latest_commit=False,
        branch=None,
        base_branch="main",
        use_worktree=False,
        keep_branch=False,
        max_iterations=3,
        output_dir=None,
        verbose=False,
        skip_pr=False,
        pr_title=None,
        timeout=600,
    ):
        """Initialize the agentic review loop."""
        # --- Basic Config ---
        self.latest_commit = latest_commit

        # Validate branch names before assigning
        if branch and not validate_git_branch_name(branch):
            sys.exit(
                f"Error: Invalid source branch name '{branch}'. Branch names must follow Git naming rules."
            )
        if not validate_git_branch_name(base_branch):
            sys.exit(
                f"Error: Invalid base branch name '{base_branch}'. Branch names must follow Git naming rules."
            )

        self.source_branch = branch  # The branch to start FROM
        self.base_branch = base_branch  # The branch to compare AGAINST and PR INTO
        self.use_worktree = use_worktree
        self.keep_branch = keep_branch
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.skip_pr = skip_pr
        self.pr_title = pr_title
        self.timeout = timeout
        self.iteration = 0
        self.session_id = str(uuid.uuid4())[:8]  # Short UUID for names

        # --- Output Directory ---
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = int(time.time())
            self.output_dir = Path("tmp") / f"agentic_loop_{timestamp}_{self.session_id}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # --- Git Setup ---
        self.repo_root = self._get_repo_root()
        self.original_branch = self._get_current_branch()
        self.work_branch = None  # Will be set during setup
        self.worktree_path = None  # Will be set if use_worktree is True
        self.cwd_for_tasks = self.repo_root  # Default CWD

        self._setup_environment()  # Creates branch, checks out, sets up worktree if needed

        # --- Determine Comparison ---
        # We always compare the work_branch against the base_branch
        self.compare_cmd = f"{self.base_branch}...{self.work_branch}"
        self.compare_desc = f"temp branch '{self.work_branch}' vs base '{self.base_branch}'"

        # --- Output Files (will be iteration-specific later) ---
        self.review_file = None       # For initial reviews
        self.rereview_file = None     # For re-reviews (after development)
        self.dev_report_file = None
        self.validation_file = None
        self.pr_file = self.output_dir / "pr_report.md"  # PR report is final

        self.log(f"Initialized Agentic Review Loop [session: {self.session_id}]")
        self.log(
            f"Source Reference: {'Latest commit' if latest_commit else f'Branch {self.source_branch}'}"
        )
        self.log(f"Base Branch: {self.base_branch}")
        self.log(f"Temporary Work Branch: {self.work_branch}")
        self.log(f"Using Worktree: {self.use_worktree} ({self.worktree_path})")
        self.log(f"Comparing: {self.compare_desc}")
        self.log(f"Max iterations: {self.max_iterations}")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Task CWD: {self.cwd_for_tasks}")

    def _run_git_command(self, command, check=True, capture=False, cwd=None, **kwargs):
        """Helper to run git commands."""
        effective_cwd = cwd or getattr(self, "cwd_for_tasks", None)
        if effective_cwd is None:
            # If cwd_for_tasks is not set yet (during initialization)
            effective_cwd = os.getcwd()

        # Validate the directory path before using it
        if not validate_directory_path(effective_cwd):
            sys.exit(f"Error: Invalid directory path '{effective_cwd}' for git command execution.")

        # Ensure effective_cwd actually exists
        effective_cwd_path = Path(effective_cwd)
        if not effective_cwd_path.exists():
            sys.exit(
                f"Error: Directory '{effective_cwd}' does not exist for git command execution."
            )
        if not effective_cwd_path.is_dir():
            sys.exit(f"Error: Path '{effective_cwd}' is not a directory for git command execution.")

        if hasattr(self, "debug"):
            self.debug(f"Running git command in '{effective_cwd}': {' '.join(command)}")
        try:
            process = subprocess.run(
                ["git"] + command,
                check=check,
                capture_output=capture,
                text=True,
                cwd=effective_cwd,
                **kwargs,
            )
            if capture:
                return process.stdout.strip()
            return True
        except subprocess.CalledProcessError as e:
            if hasattr(self, "log"):
                self.log(f"Error running git command: {' '.join(command)}")
                self.log(f"Stderr: {e.stderr}")
            if check:  # Only exit if check=True caused the error
                sys.exit(f"Git command failed: {e}")
            return None  # Return None on failure if check=False
        except FileNotFoundError:
            sys.exit("Error: 'git' command not found. Is git installed and in PATH?")

    def _get_current_branch(self):
        """Get the name of the current git branch."""
        return self._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], capture=True, cwd=self.repo_root
        )

    def _get_repo_root(self):
        """Get the root directory of the git repository."""
        try:
            return Path(
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
                ).strip()
            )
        except subprocess.CalledProcessError:
            sys.exit("Error: Not inside a git repository.")

    def _setup_environment(self):
        """Creates the temporary branch and optional worktree."""
        # 1. Determine Starting Point for the new branch
        if self.latest_commit:
            starting_point = "HEAD"
            source_desc = "latest commit"
        else:
            # Use specified branch or default to current branch if none specified
            if not self.source_branch:
                self.source_branch = self.original_branch
                # Validate the original branch name too when using it
                if not validate_git_branch_name(self.source_branch):
                    sys.exit(
                        f"Error: Invalid original branch name '{self.source_branch}'. Branch names must follow Git naming rules."
                    )

            # Verify source branch exists
            if not self._run_git_command(
                ["show-ref", "--verify", "--quiet", f"refs/heads/{self.source_branch}"], check=False
            ):
                sys.exit(f"Error: Source branch '{self.source_branch}' not found.")
            starting_point = self.source_branch
            source_desc = f"branch '{self.source_branch}'"

        # 2. Define Work Branch Name
        clean_start_point_name = re.sub(r"[^a-zA-Z0-9_-]", "_", starting_point)
        self.work_branch = f"{clean_start_point_name}-agentic-{self.session_id}"
        self.log(f"Creating temporary work branch '{self.work_branch}' from {source_desc}")

        # 3. Create the Branch
        # Check if branch already exists
        if self._run_git_command(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{self.work_branch}"], check=False
        ):
            self.log(f"Warning: Work branch '{self.work_branch}' already exists")
            # Delete the existing branch forcefully if it's not checked out
            current_branch = self._get_current_branch()
            if current_branch != self.work_branch:
                self.log(f"Deleting existing work branch '{self.work_branch}'")
                self._run_git_command(["branch", "-D", self.work_branch], check=False)
                # Now create the branch
                self._run_git_command(["branch", self.work_branch, starting_point])
            else:
                sys.exit(
                    f"Error: Cannot delete work branch '{self.work_branch}' because it is currently checked out."
                )
        else:
            # Branch doesn't exist, create it
            self._run_git_command(["branch", self.work_branch, starting_point])

        # 4. Setup Worktree OR Checkout
        if self.use_worktree:
            self.worktree_path = self.output_dir / "worktree"
            self.log(f"Setting up worktree at: {self.worktree_path}")

            # First check if the worktree path is already registered
            worktree_list = self._run_git_command(
                ["worktree", "list", "--porcelain"], capture=True, cwd=self.repo_root
            )
            if str(self.worktree_path) in worktree_list:
                self.log(
                    f"Worktree already exists at {self.worktree_path}, attempting to remove..."
                )

            # Remove existing worktree if present (e.g., from failed previous run)
            remove_result = self._run_git_command(
                ["worktree", "remove", "--force", str(self.worktree_path)],
                check=False,
                cwd=self.repo_root,
            )

            # If worktree removal fails, try pruning first, then removing again
            if remove_result is None:
                self.log("Pruning defunct worktrees and trying removal again...")
                self._run_git_command(["worktree", "prune"], check=False, cwd=self.repo_root)
                time.sleep(0.5)  # Short pause sometimes helps git release locks
                remove_result = self._run_git_command(
                    ["worktree", "remove", "--force", str(self.worktree_path)],
                    check=False,
                    cwd=self.repo_root,
                )

                # If still fails, try manual directory removal if the directory exists
                if remove_result is None and self.worktree_path.exists():
                    self.log(
                        f"Git worktree remove failed, trying manual directory removal of {self.worktree_path}"
                    )
                    try:
                        shutil.rmtree(self.worktree_path)
                    except OSError as e:
                        self.log(f"Warning: Manual directory removal failed: {e}")
                        # Continue anyway - git worktree add might still work

            # Make sure the parent directory exists
            self.worktree_path.parent.mkdir(parents=True, exist_ok=True)

            # Add the new worktree
            try:
                self._run_git_command(
                    ["worktree", "add", str(self.worktree_path), self.work_branch],
                    cwd=self.repo_root,
                )
                self.cwd_for_tasks = self.worktree_path  # Set CWD for subsequent tasks
            except subprocess.CalledProcessError as e:
                self.log(f"Error creating worktree: {e}")
                # Fallback to using the main repo checkout if worktree fails
                self.log("Falling back to using main repository checkout")
                self._run_git_command(["checkout", self.work_branch], cwd=self.repo_root)
                self.cwd_for_tasks = self.repo_root
                self.use_worktree = False  # Update flag to reflect actual state
        else:
            self.log(f"Checking out temporary branch '{self.work_branch}' in main directory")
            self._run_git_command(["checkout", self.work_branch], cwd=self.repo_root)
            self.cwd_for_tasks = self.repo_root  # Tasks run in main repo checkout

    def _cleanup_environment(self):
        """Cleans up the temporary branch and optional worktree."""
        self.log("Cleaning up environment...")

        # 1. Switch back to the original branch (only if not using worktree)
        if not self.use_worktree:
            self.log(f"Switching back to original branch '{self.original_branch}'")
            self._run_git_command(["checkout", self.original_branch], cwd=self.repo_root)

        # 2. Remove Worktree (if used)
        if self.use_worktree and self.worktree_path and self.worktree_path.exists():
            self.log(f"Removing worktree at {self.worktree_path}")
            # Prune first to handle potential state issues
            self._run_git_command(["worktree", "prune"], check=False, cwd=self.repo_root)
            time.sleep(0.5)  # Short pause sometimes helps git release locks
            self._run_git_command(
                ["worktree", "remove", "--force", str(self.worktree_path)],
                check=False,
                cwd=self.repo_root,
            )
            # Attempt to remove the directory if git didn't fully clean it
            if self.worktree_path.exists():
                try:
                    shutil.rmtree(self.worktree_path)
                except OSError as e:
                    self.log(
                        f"Warning: Could not remove worktree directory {self.worktree_path}: {e}"
                    )

        # 3. Delete Temporary Branch (if not keeping)
        if not self.keep_branch:
            self.log(f"Deleting temporary branch '{self.work_branch}'")
            self._run_git_command(
                ["branch", "-D", self.work_branch], check=False, cwd=self.repo_root
            )
        else:
            self.log(f"Keeping temporary branch '{self.work_branch}' as requested.")

    def log(self, message):
        """Log a message, always shown."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp} AgenticLoop] {message}")

    def debug(self, message):
        """Log a debug message, only shown in verbose mode."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp} AgenticLoop:DEBUG] {message}")

    def run_claude(self, prompt, role, allowed_tools=None, timeout=None):
        """Run a Claude instance with the given prompt and tools."""
        start_time = time.time()
        self.log(f"Running {role.value.capitalize()} agent (Iteration {self.iteration})...")
        self.debug(f"Prompt length: {len(prompt)} characters")

        # Default tools per role
        if allowed_tools is None:
            if role == AgentRole.REVIEWER:
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch"  # Read-only focus + web access + agent delegation
            elif role == AgentRole.DEVELOPER:
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task,Edit,MultiEdit,Write,TodoRead,TodoWrite,WebSearch,WebFetch"  # Edit + web access + agent delegation
            elif role == AgentRole.VALIDATOR:
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch"  # Read-only focus + web access + agent delegation
            elif role == AgentRole.PR_MANAGER:
                allowed_tools = "Bash,Grep,Read,LS,Glob,Task,WebSearch,WebFetch"  # Bash for gh + web access + agent delegation

        prompt_file_path = None  # Keep track of path for cleanup
        prompt_content = ""  # To store the prompt read from file
        try:
            # Validate the output directory path before using it
            if not validate_directory_path(self.output_dir):
                raise ValueError(f"Invalid output directory path: {self.output_dir}")

            # Make sure the directory exists
            output_dir_path = Path(self.output_dir)
            if not output_dir_path.exists():
                raise ValueError(f"Output directory does not exist: {self.output_dir}")
            if not output_dir_path.is_dir():
                raise ValueError(f"Output path is not a directory: {self.output_dir}")

            # Use mkstemp for more secure temporary file creation
            fd, prompt_file_path = tempfile.mkstemp(suffix=".txt", dir=self.output_dir)
            try:
                # Close the file descriptor returned by mkstemp
                os.close(fd)
                # Write the prompt to the temporary file
                with open(prompt_file_path, "w") as f:
                    f.write(prompt)
                self.debug(f"Wrote prompt to temporary file: {prompt_file_path}")

                # Read the content back from the file
                with open(prompt_file_path, "r") as f:
                    prompt_content = f.read()
                self.debug(f"Read {len(prompt_content)} chars from prompt file for -p argument.")
            except Exception:
                # Clean up the file if any error occurs during writing/reading
                if prompt_file_path and os.path.exists(prompt_file_path):
                    os.unlink(prompt_file_path)
                raise

            # Check if 'claude' command exists before trying to run it
            try:
                # Test if claude is available by running 'claude --version'
                version_check = subprocess.run(
                    ["claude", "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,  # Short timeout for version check
                )
                if version_check.returncode != 0:
                    raise ValueError(f"Claude command check failed: {version_check.stderr.strip()}")
                self.debug(f"Claude command is available: {version_check.stdout.strip()}")
            except FileNotFoundError:
                raise ValueError(
                    "Error: 'claude' command not found. Please ensure Claude CLI is installed and in your PATH."
                )
            except subprocess.TimeoutExpired:
                raise ValueError(
                    "Error: 'claude --version' command timed out. Check if Claude CLI is functioning properly."
                )

            # --- Build Claude command using -p and the content read from the file ---
            cmd = [
                "claude",
                "--output-format",
                "text",
                "-p",
                prompt_content,  # Use -p with the content string
            ]
            # --- End Modification ---

            if allowed_tools:
                cmd.extend(["--allowedTools", allowed_tools])

            _timeout = timeout or self.timeout
            # Truncate the command log in debug to avoid printing huge prompts
            self.debug(f"Running command in '{self.cwd_for_tasks}': {' '.join(cmd[:4])}...")

            # Make sure the working directory exists
            if not os.path.exists(self.cwd_for_tasks) or not os.path.isdir(self.cwd_for_tasks):
                raise ValueError(
                    f"Invalid working directory for Claude command: {self.cwd_for_tasks}"
                )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=_timeout,
                cwd=self.cwd_for_tasks,  # IMPORTANT: Run in the correct directory
            )
            output = result.stdout

            # Validate the output
            if not output:
                raise ValueError("Claude returned empty output")

            # Check for common error patterns in the output
            error_indicators = ["API Error:", "Failed to run: claude", "Error: Unable to connect"]
            for indicator in error_indicators:
                if indicator in output[:200]:  # Check just the beginning of the output
                    raise ValueError(f"Claude command might have failed: {output[:200]}")

            if not output.strip():
                self.log(f"Warning: Empty output from {role.value} agent")
                output = f"# {role.value.capitalize()} Report (Iteration {self.iteration})\n\nNo content returned."

            duration = time.time() - start_time
            self.log(f"{role.value.capitalize()} agent completed in {duration:.1f} seconds")
            self.debug(f"Output length: {len(output)} characters")
            return output

        except subprocess.TimeoutExpired:
            self.log(f"Error: {role.value.capitalize()} agent timed out after {_timeout} seconds")
            return f"# {role.value.capitalize()} Report (Iteration {self.iteration})\n\nAgent timed out after {_timeout} seconds."
        except subprocess.CalledProcessError as e:
            self.log(f"Error running {role.value.capitalize()} agent: {e}")
            self.debug(f"stderr: {e.stderr}")
            # Include stderr in the report for debugging
            stderr_excerpt = e.stderr[:500] + "..." if len(e.stderr) > 500 else e.stderr
            return f"# {role.value.capitalize()} Report (Iteration {self.iteration})\n\nError: {e}\nStderr:\n```\n{stderr_excerpt}\n```"
        except Exception as e:
            self.log(f"Unexpected error: {e}")
            import traceback  # Import here for debugging unexpected errors

            self.debug(traceback.format_exc())
            return f"# {role.value.capitalize()} Report (Iteration {self.iteration})\n\nUnexpected error: {e}"
        finally:
            # Clean up the temporary prompt file using the stored path
            if prompt_file_path and os.path.exists(prompt_file_path):
                try:
                    os.unlink(prompt_file_path)
                    self.debug(f"Cleaned up temporary prompt file: {prompt_file_path}")
                except Exception as e:
                    self.debug(f"Error cleaning up temporary file {prompt_file_path}: {e}")

    def run_reviewer(self, is_rereview=False):
        """Run the Reviewer agent."""
        phase = "Re-Review" if is_rereview else "Review"
        self.log(f"Starting {phase} phase (Iteration {self.iteration})...")

        # Validate the output directory before creating file paths
        if not validate_directory_path(self.output_dir):
            sys.exit(f"Error: Invalid output directory path: {self.output_dir}")

        # Create different filenames for initial review vs re-review
        if is_rereview:
            file_prefix = "rereview"
            target_file_attr = "rereview_file"
        else:
            file_prefix = "review"
            target_file_attr = "review_file"

        # Create a safe file path for the review file
        filename = f"{file_prefix}_iter_{self.iteration}.md"
        # Ensure the filename does not contain path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            sys.exit(f"Error: Invalid review filename: {filename}")

        # Store in the appropriate attribute based on type
        setattr(self, target_file_attr, self.output_dir / filename)
        target_file = getattr(self, target_file_attr)  # Get the file path we'll write to

        prompt = f"""
Think hard about this task. You are Iteration #{self.iteration}.

You are a senior code reviewer examining the changes in the temporary branch '{self.work_branch}' compared to the base branch '{self.base_branch}'.
{"This is a re-review after a developer attempted fixes." if is_rereview else ""}
Your task is to provide a thorough, critical review focused on:

1. Code quality and best practices
2. Architectural consistency
3. Error handling completeness
4. Input/output validation
5. Security issues
6. Performance concerns
7. Test coverage and quality
8. Library usage and dependency handling

For each issue found:
1. Mark as CRITICAL, HIGH, MEDIUM, or LOW priority
2. Provide the file path and line number where the issue occurs
3. Explain the issue clearly with technical reasoning
4. Suggest a specific, actionable fix

First, run the following command IN THE CURRENT DIRECTORY ({self.cwd_for_tasks}) to see the current state of changes:
```bash
git diff {self.compare_cmd}
```

Your Process:
1. Analyze the diff thoroughly to understand all changes.
2. Identify issues with the code, classifying each by priority.
3. Document each issue with precise location and reasoning.
4. Provide actionable recommendations for each issue.
5. For any library usage or API you're not 100% familiar with, FIRST look at the ai_docs/ directory, the user might have pasted documentation there. If not, use WebSearch to verify the functionality exists and how it's properly used before flagging issues.
{"6. Pay special attention to whether previous CRITICAL/HIGH issues were properly addressed and if any new issues were introduced." if is_rereview else ""}

IMPORTANT: When reviewing library usage, do not make assumptions about available functions or APIs. Use WebSearch to verify documentation for any external libraries before raising issues about their usage. NEVER invent or hallucinate library functionality that you can't confirm exists.

Format your entire output as a markdown document containing ONLY the review report.
The report MUST include these sections exactly:
## Summary
[Overall assessment, key themes {"mentioning progress from previous iteration if applicable" if is_rereview else ""}]

## Issue List
[List all issues found, categorized by priority (CRITICAL, HIGH, MEDIUM, LOW). For each issue, include:
- Priority label
- File path and line number(s)
- Clear explanation of the issue
- Specific suggestion for fixing]

## Recommendations
[Strategic suggestions beyond specific fixes. Include architectural or process improvements if applicable.]

IMPORTANT:
*Do not preface your answer with anything else.*
- Your entire response must be the markdown review report.
- Do NOT include any introductory phrases like "I have completed the review..." or "Here is the review...".
- Do NOT describe the process or mention where the file will be saved.
- Start your response DIRECTLY with the ## Summary heading.
- Be thorough yet constructive. Your output will guide the next step (Developer or Validator).
- If this is a re-review (Iteration > 1), pay close attention to whether previous CRITICAL/HIGH issues were properly addressed and if any new issues were introduced.
"""
        output = self.run_claude(prompt, AgentRole.REVIEWER)

        # Use a try-except block to catch any file errors
        try:
            with open(target_file, "w") as f:
                f.write(output)
            self.log(f"{phase} report saved to {target_file}")
        except IOError as e:
            self.log(f"Error writing to {phase.lower()} file {target_file}: {e}")
            return False

        return len(output.strip()) > 0 and "Error:" not in output[:100]  # Basic success check

    def run_developer(self):
        """Run the Developer agent."""
        self.log(f"Starting Development phase (Iteration {self.iteration})...")

        # Validate the output directory before creating file paths
        if not validate_directory_path(self.output_dir):
            sys.exit(f"Error: Invalid output directory path: {self.output_dir}")

        # Create a safe file path for the dev report file
        dev_report_filename = f"dev_report_iter_{self.iteration}.md"
        # Ensure the filename does not contain path traversal attempts
        if ".." in dev_report_filename or "/" in dev_report_filename or "\\" in dev_report_filename:
            sys.exit(f"Error: Invalid dev report filename: {dev_report_filename}")

        self.dev_report_file = self.output_dir / dev_report_filename  # Iteration specific

        # Check required input files - we need the most recent review
        # Use either the initial review or the re-review from a previous iteration
        if self.iteration > 1 and hasattr(self, 'rereview_file') and self.rereview_file and self.rereview_file.exists():
            # For iteration > 1, we should have a re-review from previous iteration
            prev_rereview_file = self.output_dir / f"rereview_iter_{self.iteration-1}.md"
            review_to_use = prev_rereview_file if prev_rereview_file.exists() else self.review_file
        else:
            # For iteration 1, use the initial review
            review_to_use = self.review_file

        if not review_to_use or not review_to_use.exists():
            self.log(f"Error: Review file ({review_to_use}) not found for Developer.")
            return False

        # Store the review file we're actually using
        self.current_review_for_dev = review_to_use

        # Check for previous failed validation report (for iterations > 1)
        previous_validation_file = self.output_dir / f"validation_iter_{self.iteration - 1}.md"
        has_validation_feedback = self.iteration > 1 and previous_validation_file.exists()

        prompt = f"""
Think hard about this task. You are Iteration #{self.iteration}.

You are a senior developer implementing fixes based on code review feedback.
You are working in the directory: {self.cwd_for_tasks} on branch '{self.work_branch}'.
Your task is to address all CRITICAL and HIGH priority issues identified in the latest code review.

Input Sources:
1. Latest Code Review: {self.current_review_for_dev}
{"2. Previous Failed Validation Report: " + str(previous_validation_file) if has_validation_feedback else ""}

Your Process:
1. Carefully analyze the latest review ({self.current_review_for_dev}).
{"2. Study the previous failed validation report (" + str(previous_validation_file) + ") and prioritize fixing the issues IT identified." if has_validation_feedback else ""}
3. Assess the current code state by running: git diff {self.compare_cmd}
4. Create a systematic plan to address all CRITICAL and HIGH priority issues from the review {"paying special attention to the feedback in the validation report" if has_validation_feedback else ""}.
5. For every library call or API you're not 100% sure about:
   • Use WebSearch to access the latest official documentation
   • Summarize key findings in Implementation Notes
   • If uncertainty remains, create a minimal smoke-test script in tests/test_smoke_<lib>.py that imports the symbol and exercises the call (catching exceptions). Commit this as part of the fix.
6. Implement the fixes using appropriate tools (Edit, MultiEdit, Write, Bash). WORK ONLY WITHIN THE CURRENT DIRECTORY.
7. After making changes, commit them with clear messages (e.g., git commit -am 'Fix critical issue X based on review iter {self.iteration}').
8. Run tests if available (e.g., using uv run pytest or similar command appropriate for this project).

IMPORTANT: NEVER assume library functionality exists without verifying it. Use WebSearch to confirm the correct usage of any external APIs or libraries before implementing fixes that depend on them.

Format your entire output as a markdown document containing ONLY the development report.
The report MUST include these sections exactly:
## Summary 
[Concise overview of fixes implemented for Iteration {self.iteration}]

## Issues Addressed
[Detail how each CRITICAL/HIGH issue from the review {"and validation report" if has_validation_feedback else ""} was fixed - include precise file paths and line numbers]

## Implementation Notes
[Technical challenges encountered and how they were resolved, alternative approaches considered]

## Test Results
[Results of any tests run, showing before/after if possible]

## Commit IDs
[List the git commit IDs for all changes made in this iteration]

IMPORTANT:
*Do not preface your answer with anything else.*
- Your entire response must be the markdown development report.
- Do NOT include any introductory phrases like "I have completed the development..." or "Here is the report...".
- Do NOT describe the process or mention where the file will be saved.
- Start your response DIRECTLY with the ## Summary heading.
- The content you generate will be used directly as the development report for the next agent.
- Focus on high-quality fixes that will pass validation. Your work will be re-reviewed and validated.
"""
        output = self.run_claude(prompt, AgentRole.DEVELOPER)

        # Use a try-except block to catch any file errors
        try:
            with open(self.dev_report_file, "w") as f:
                f.write(output)
            self.log(f"Development report saved to {self.dev_report_file}")
        except IOError as e:
            self.log(f"Error writing to development report file {self.dev_report_file}: {e}")
            return False

        return len(output.strip()) > 0 and "Error:" not in output[:100]

    def run_validator(self):
        """Run the Validator agent."""
        self.log(f"Starting Validation phase (Iteration {self.iteration})...")

        # Validate the output directory before creating file paths
        if not validate_directory_path(self.output_dir):
            sys.exit(f"Error: Invalid output directory path: {self.output_dir}")

        # Create a safe file path for the validation file
        validation_filename = f"validation_iter_{self.iteration}.md"
        # Ensure the filename does not contain path traversal attempts
        if ".." in validation_filename or "/" in validation_filename or "\\" in validation_filename:
            sys.exit(f"Error: Invalid validation filename: {validation_filename}")

        self.validation_file = self.output_dir / validation_filename  # Iteration specific

        # Check required input files - validator needs the rereview (post-development review)
        if not self.rereview_file or not self.rereview_file.exists():
            self.log(f"Error: Latest re-review file ({self.rereview_file}) not found for Validator.")
            return False, False
        if not self.dev_report_file or not self.dev_report_file.exists():
            self.log(
                f"Error: Latest dev report file ({self.dev_report_file}) not found for Validator."
            )
            return False, False

        # Also check if we have the initial review for reference
        initial_review_exists = self.review_file and self.review_file.exists()

        prompt = f"""
Think hard about this task. You are Iteration #{self.iteration}.

You are a quality validator ensuring code standards after development changes on branch '{self.work_branch}'.
Your task is to verify that all critical issues have been properly addressed, and no new issues were introduced.

Input Sources:
1. Latest Re-Review: {self.rereview_file} (This review was done AFTER the development attempt)
2. Latest Development Report: {self.dev_report_file}
{f"3. Initial Review: {self.review_file} (For reference to see original issues)" if initial_review_exists else ""}

Your Process:
1. Carefully study both the re-review ({self.rereview_file}) and dev report ({self.dev_report_file}).
2. Examine the current code changes: git diff {self.compare_cmd}
3. Verify if EVERY CRITICAL and HIGH priority issue mentioned in the latest review has been properly addressed by the developer.
4. Check if any NEW issues (especially CRITICAL/HIGH) were introduced during the fix process.
5. For any library usage or API you're not 100% familiar with, FIRST look at the ai_docs/ directory, the user might have pasted documentation there. If not, use WebSearch to verify functionality and proper usage before determining if an issue is addressed correctly.
6. Run tests if available and assess results.
7. Evaluate overall code quality against project standards.

IMPORTANT: Do not rely on your built-in knowledge when evaluating library usage fixes. Use WebSearch to verify documentation for external libraries when validating implementations. NEVER declare a library-related fix inadequate without first confirming the correct API usage through documentation.

Format your entire output as a markdown document containing ONLY the validation report.
The report MUST include these sections exactly:
## Summary
[Overall assessment of the iteration {self.iteration} changes]

## Issue Verification
[For each CRITICAL/HIGH issue from the review, clearly state whether it is: Fully Addressed, Partially Addressed, Not Addressed, or Inadequately Addressed. Provide specific evidence.]

## Test Results
[Results of any tests run, with clear pass/fail indicators]

## Code Quality Evaluation
[Assessment of code quality, maintainability, and adherence to best practices]

## Conclusion
[Final determination with clear reasoning]

YOUR REPORT MUST END WITH ONE OF THESE LINES EXACTLY:
VALIDATION: PASSED
VALIDATION: FAILED

IMPORTANT:
*Do not preface your answer with anything else.*
- Your entire response must be the markdown validation report.
- Do NOT include any introductory phrases like "I have completed the validation..." or "Here is the report...".
- Do NOT describe the process or mention where the file will be saved.
- Start your response DIRECTLY with the ## Summary heading.
- Be extremely rigorous in your validation - a PASS means ALL CRITICAL and HIGH issues are fully fixed.
- If FAILED, clearly state which specific CRITICAL/HIGH issues remain or were newly introduced. This feedback is crucial for the next development iteration.
- Provide specific evidence (file paths, line numbers, reasoning) for your conclusions.
"""
        output = self.run_claude(prompt, AgentRole.VALIDATOR)

        # Use a try-except block to catch any file errors
        try:
            with open(self.validation_file, "w") as f:
                f.write(output)
            self.log(f"Validation report saved to {self.validation_file}")
        except IOError as e:
            self.log(f"Error writing to validation file {self.validation_file}: {e}")
            return False, False

        validation_passed = "VALIDATION: PASSED" in output.splitlines()[-1]  # Check last line
        self.log(f"Validation Result: {'PASSED' if validation_passed else 'FAILED'}")
        success = len(output.strip()) > 0 and "Error:" not in output[:100]
        return success, validation_passed

    def run_pr_manager(self):
        """Run the PR Manager agent."""
        self.log(f"Starting PR creation phase...")

        # Validate the output directory before creating file paths
        if not validate_directory_path(self.output_dir):
            sys.exit(f"Error: Invalid output directory path: {self.output_dir}")

        # Make sure self.pr_file has a safe path
        if not hasattr(self, "pr_file") or self.pr_file is None:
            pr_filename = "pr_report.md"
            # Ensure the filename does not contain path traversal attempts
            if ".." in pr_filename or "/" in pr_filename or "\\" in pr_filename:
                sys.exit(f"Error: Invalid PR filename: {pr_filename}")
            self.pr_file = self.output_dir / pr_filename

        if self.skip_pr:
            self.log("PR creation skipped due to --no-pr flag.")
            # Create a dummy PR report indicating skip
            try:
                with open(self.pr_file, "w") as f:
                    f.write("# PR Report\n\nPR creation was skipped via the --no-pr flag.")
                self.log(f"PR skip note saved to {self.pr_file}")
            except IOError as e:
                self.log(f"Error writing PR skip note to {self.pr_file}: {e}")
            return False  # Indicate PR wasn't created

        # Check required input files from the final successful iteration
        if not self.validation_file or not self.validation_file.exists():
            self.log(
                f"Error: Final validation file ({self.validation_file}) not found for PR Manager."
            )
            return False

        # Find the reports from the last iteration
        final_review_file = self.output_dir / f"review_iter_{self.iteration}.md"
        final_rereview_file = self.output_dir / f"rereview_iter_{self.iteration}.md"
        final_dev_report_file = self.output_dir / f"dev_report_iter_{self.iteration}.md"

        # We need at least the re-review (which contains the post-fix assessment) and the dev report
        if not final_rereview_file.exists() or not final_dev_report_file.exists():
            self.log("Error: Could not find final re-review/dev reports for PR description.")
            return False

        # Generate PR title if needed
        title = self.pr_title
        if not title:
            # Use the temporary branch name for a reasonable default
            clean_branch = (
                self.work_branch.replace("-agentic-" + self.session_id, "")
                .replace("-", " ")
                .title()
            )
            title = f"Agentic Loop Changes for {clean_branch} (Iter {self.iteration})"

        prompt = f"""
Think hard about this task. You are creating a Pull Request.

You are a PR manager preparing a high-quality pull request for branch '{self.work_branch}' into '{self.base_branch}'.
Validation has passed according to the final validation report, and your task is to create a comprehensive PR.

Input Sources:
1. Initial Review: {final_review_file if final_review_file.exists() else "Not available"}
2. Final Re-Review: {final_rereview_file}
3. Final Development Report: {final_dev_report_file}
4. Final Validation Report: {self.validation_file} (Should confirm PASSED)

Your Process:
1. Read all final reports to gather complete context.
2. Analyze the final code changes: git diff {self.compare_cmd}
3. For any library or API discussions in the reports, use WebSearch to verify that the implemented solutions follow best practices and documentation.
4. Generate a comprehensive PR description in markdown format that accurately describes the changes, especially noting any API or library updates.
5. Prepare and execute the commands to create the PR using the GitHub CLI (gh).

IMPORTANT: When describing library or API changes in the PR, make sure to verify the correct usage through official documentation using WebSearch. This ensures the PR accurately represents the technical changes made.

For the PR description, include:
- A clear summary of changes and their purpose
- Key issues addressed (from final review/dev reports)
- Overview of the iterative process (mention # iterations)
- Confirmation of validation passing
- Testing performed (if any mentioned in reports)

Execution Steps:
1. Generate the PR description markdown text.
2. Write the PR description to a temporary file (e.g., pr_body.md).
3. Execute these commands IN THE CURRENT DIRECTORY ({self.cwd_for_tasks}):
   ```bash
   # Ensure branch is pushed
   git push -u origin {self.work_branch}

   # Create the PR (replace $PR_BODY_TEXT with the actual description)
   echo "$PR_BODY_TEXT" > pr_body.md
   gh pr create --base {self.base_branch} --head {self.work_branch} --title "{title}" --body-file pr_body.md
   ```
4. Capture the output, especially the PR URL.

Format your entire output as a markdown document containing ONLY the PR manager report.
The report MUST include these sections exactly:
## PR Title
{title}

## PR Body
[The complete markdown PR description that was used]

## PR Creation Command
[The exact gh pr create command used]

## PR Creation Result
[The output from the gh pr create command, including the URL if successful]

IMPORTANT:
*Do not preface your answer with anything else.*
- Your entire response must be the markdown PR manager report.
- Do NOT include any introductory phrases like "I have created the PR..." or "Here is the report...".
- Do NOT describe the process or mention where the file will be saved.
- Start your response DIRECTLY with the ## PR Title heading.
- Ensure you actually execute the commands to create the PR, don't just describe them.
- If the gh command fails, include the complete error message in the report.
- The content you generate will be saved as the final PR report.
"""
        output = self.run_claude(prompt, AgentRole.PR_MANAGER)

        # Use a try-except block to catch any file errors
        try:
            with open(self.pr_file, "w") as f:
                f.write(output)
            self.log(f"PR report saved to {self.pr_file}")
        except IOError as e:
            self.log(f"Error writing to PR file {self.pr_file}: {e}")
            return False

        # Check if PR URL exists in the output
        pr_url_match = re.search(r"https://github\.com/[^/]+/[^/]+/pull/\d+", output)
        if pr_url_match:
            pr_url = pr_url_match.group(0)
            self.log(f"PR creation reported successfully: {pr_url}")
            return True
        else:
            self.log(
                "PR URL not found in the report. PR creation might have failed. Check the PR report."
            )
            return False

    def run(self):
        """Run the full agentic review loop workflow."""
        self.log(f"Starting agentic review loop for branch '{self.work_branch}'...")
        validation_passed = False
        final_success = False

        try:
            while self.iteration < self.max_iterations:
                self.iteration += 1
                self.log(f"\n=== Starting Iteration {self.iteration}/{self.max_iterations} ===")

                # --- Step 1: Review ---
                review_success = self.run_reviewer(is_rereview=(self.iteration > 1))
                if not review_success:
                    self.log(f"Review phase failed on iteration {self.iteration}. Stopping loop.")
                    break

                # --- Step 2: Develop ---
                # Developer uses the latest review and potentially previous validation feedback
                dev_success = self.run_developer()
                if not dev_success:
                    self.log(
                        f"Development phase failed on iteration {self.iteration}. Stopping loop."
                    )
                    break

                # --- Step 3: Re-Review (Review the developer's changes) ---
                # This creates a separate rereview_file, distinct from the initial review_file
                rereview_success = self.run_reviewer(is_rereview=True)
                if not rereview_success:
                    self.log(
                        f"Re-Review phase failed on iteration {self.iteration}. Stopping loop."
                    )
                    break
                # Note: The validation step will use the report from this re-review (stored in rereview_file)

                # --- Step 4: Validate ---
                # Validator uses the latest (re-review) report and the latest dev report
                validation_success, validation_passed = self.run_validator()
                if not validation_success:
                    self.log(
                        f"Validation phase failed on iteration {self.iteration}. Stopping loop."
                    )
                    break

                # --- Check Validation Result ---
                if validation_passed:
                    self.log(f"Validation PASSED on iteration {self.iteration}!")
                    # Proceed to PR creation outside the loop
                    final_success = True
                    break
                else:
                    self.log(f"Validation FAILED on iteration {self.iteration}.")
                    if self.iteration >= self.max_iterations:
                        self.log("Maximum iterations reached without passing validation.")
                        break
                    else:
                        self.log("Continuing to next iteration with validation feedback...")
                        # Loop continues, developer will use the failed validation report

            # --- Step 5: PR Creation (if validation passed) ---
            if final_success:
                pr_creation_reported = self.run_pr_manager()
                # The overall success depends on validation passing, PR is best-effort
            else:
                self.log("Workflow finished without passing validation.")

        except KeyboardInterrupt:
            self.log("\nProcess interrupted by user.")
            final_success = False
        except Exception as e:
            self.log(f"An unexpected error occurred during the loop: {e}")
            import traceback

            self.debug(traceback.format_exc())
            final_success = False
        finally:
            # --- Cleanup ---
            self._cleanup_environment()

        self.log(f"Agentic review loop completed.")
        self.log(f"Final Validation Status: {'PASSED' if final_success else 'FAILED'}")
        self.log(f"Output artifacts are in: {self.output_dir}")
        self.log("Artifacts Summary:")
        for i in range(1, self.iteration + 1):
            self.log(f"  Iter {i}: Initial Review: review_iter_{i}.md")
            self.log(f"  Iter {i}: Development: dev_report_iter_{i}.md")
            self.log(f"  Iter {i}: Re-Review: rereview_iter_{i}.md")
            self.log(f"  Iter {i}: Validation: validation_iter_{i}.md")
        if self.pr_file.exists():
            self.log(f"  PR Report: {self.pr_file.name}")

        return final_success


def main():
    parser = argparse.ArgumentParser(
        description="Run Agentic Review Loop v2 with Claude instances.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Review latest commit in a new temp branch (default behavior)
  uv run python scripts/agentic_review_loop_v2.py --latest
  Review a specific branch in a new temp branch, using a worktree
  uv run python scripts/agentic_review_loop_v2.py --branch feature-branch --worktree
  Specify base branch and keep temporary branch after run
  uv run python scripts/agentic_review_loop_v2.py --branch feature-branch --base-branch develop --keep-branch
""",
    )
    # Source selection (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--latest", action="store_true", help="Source from the latest commit (HEAD)"
    )
    source_group.add_argument(
        "--branch", metavar="BRANCH", help="Source branch to create the temporary work branch from"
    )

    # Configuration options
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for comparison and PR target (default: main)",
    )
    parser.add_argument(
        "--worktree",
        action="store_true",
        help="Run the entire process within a dedicated git worktree",
    )
    parser.add_argument(
        "--keep-branch",
        action="store_true",
        help="Do not delete the temporary work branch after completion",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of improvement cycles (default: 3)",
    )
    parser.add_argument(
        "--output-dir", help="Directory for output files (default: tmp/agentic_loop_TIMESTAMP_UUID)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose debug output")
    parser.add_argument(
        "--no-pr", action="store_true", help="Skip PR creation even if validation passes"
    )
    parser.add_argument("--pr-title", help="Custom title for PR (default: auto-generated)")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds for each Claude agent call (default: 600)",
    )

    args = parser.parse_args()

    # --- Initialize and Run ---
    loop = None
    try:
        loop = AgenticReviewLoop(
            latest_commit=args.latest,
            branch=args.branch,
            base_branch=args.base_branch,
            use_worktree=args.worktree,
            keep_branch=args.keep_branch,
            max_iterations=args.max_iterations,
            output_dir=args.output_dir,
            verbose=args.verbose,
            skip_pr=args.no_pr,
            pr_title=args.pr_title,
            timeout=args.timeout,
        )
        success = loop.run()
        sys.exit(0 if success else 1)

    except SystemExit as e:
        # Catch sys.exit calls for cleaner exit codes
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if loop:  # Ensure cleanup if loop was initialized
            loop._cleanup_environment()
        sys.exit(130)
    except Exception as e:
        print(f"\nCritical Error during agentic loop execution: {e}")
        import traceback

        print(traceback.format_exc())  # Print stack trace for unexpected errors
        if loop:  # Ensure cleanup if loop was initialized
            loop._cleanup_environment()
        sys.exit(1)


if __name__ == "__main__":
    main()
