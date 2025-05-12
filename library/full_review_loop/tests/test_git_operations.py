"""
Test git operations in the agentic review loop module.

This module contains tests for the Git operations used in the AgenticReviewLoop class.
It uses mock objects to avoid requiring a real git repository during testing.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from full_review_loop.full_review_loop_safe import (
    AgenticReviewLoop,
    validate_git_branch_name,
    validate_directory_path,
)


class TestGitValidation(unittest.TestCase):
    """Test validation functions for git branch names and directories."""

    def test_validate_git_branch_name(self):
        """Test git branch name validation."""
        # Valid branch names
        self.assertTrue(validate_git_branch_name("main"))
        self.assertTrue(validate_git_branch_name("feature/new-feature"))
        self.assertTrue(validate_git_branch_name("bugfix-123"))
        self.assertTrue(validate_git_branch_name("release_1.0"))

        # Invalid branch names
        self.assertFalse(validate_git_branch_name(""))  # Empty
        self.assertFalse(validate_git_branch_name(None))  # None
        self.assertFalse(validate_git_branch_name("branch with spaces"))  # Spaces
        self.assertFalse(validate_git_branch_name("/branch"))  # Starts with slash
        self.assertFalse(validate_git_branch_name("branch/"))  # Ends with slash
        self.assertFalse(validate_git_branch_name("branch//name"))  # Consecutive slashes
        self.assertFalse(validate_git_branch_name("branch..name"))  # Consecutive dots
        self.assertFalse(validate_git_branch_name("branch@{name}"))  # Contains @{
        self.assertFalse(validate_git_branch_name("-branch"))  # Starts with dash
        self.assertFalse(validate_git_branch_name("branch.lock"))  # Ends with .lock
        self.assertFalse(validate_git_branch_name("branch\\name"))  # Contains backslash
        self.assertFalse(validate_git_branch_name("branch\nname"))  # Contains control character

    def test_validate_directory_path(self):
        """Test directory path validation."""
        # Valid paths
        self.assertTrue(validate_directory_path("/path/to/directory"))
        self.assertTrue(validate_directory_path(Path("/path/to/directory")))

        # Invalid paths
        self.assertFalse(validate_directory_path(None))  # None
        self.assertFalse(validate_directory_path(123))  # Not a string or Path
        self.assertFalse(validate_directory_path("/path/with/null\0byte"))  # Contains null byte
        self.assertFalse(validate_directory_path("../path/traversal"))  # Path traversal attempt

        # Create a temporary file for testing
        temp_file = "temp_test_file.txt"
        try:
            with open(temp_file, "w") as f:
                f.write("test")
            # Path exists but is a file, not a directory
            self.assertFalse(validate_directory_path(temp_file))
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestGitOperations(unittest.TestCase):
    """Test Git operations in the AgenticReviewLoop class."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # Create a patched version of subprocess.run
        self.subprocess_run_patcher = patch("subprocess.run")
        self.mock_subprocess_run = self.subprocess_run_patcher.start()

        # Set up mock return value for subprocess.run
        self.mock_process = MagicMock()
        self.mock_process.stdout = "mocked_output"
        self.mock_process.returncode = 0
        self.mock_subprocess_run.return_value = self.mock_process

        # Create a temporary directory for testing
        self.temp_dir = Path("temp_test_dir")
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()

    def tearDown(self):
        """Tear down test fixtures, if any."""
        self.subprocess_run_patcher.stop()

        # Remove temporary directory
        if self.temp_dir.exists():
            self.temp_dir.rmdir()

    @patch("sys.exit")
    def test_run_git_command_validates_cwd(self, mock_exit):
        """Test that _run_git_command validates the cwd parameter."""
        # Create a loop instance with required parameters
        loop = AgenticReviewLoop(latest_commit=True)

        # Set a valid cwd_for_tasks
        loop.cwd_for_tasks = str(self.temp_dir)

        # Valid cwd should work
        loop._run_git_command(["status"])
        self.mock_subprocess_run.assert_called()

        # Invalid cwd should exit
        loop._run_git_command(["status"], cwd="nonexistent_directory")
        mock_exit.assert_called()

        # None as cwd should use cwd_for_tasks
        self.mock_subprocess_run.reset_mock()
        loop._run_git_command(["status"], cwd=None)
        self.mock_subprocess_run.assert_called()

        # Path traversal attempt should exit
        loop._run_git_command(["status"], cwd="../path/traversal")
        mock_exit.assert_called()

    @patch("sys.exit")
    def test_setup_environment_handles_existing_branch(self, mock_exit):
        """Test that _setup_environment handles the case where the branch already exists."""
        loop = AgenticReviewLoop(latest_commit=True)

        # Mock _run_git_command to simulate branch already exists
        original_run_git = loop._run_git_command

        def mock_run_git_command(command, check=True, capture=False, cwd=None, **kwargs):
            # Simulate branch existence check
            if command[0] == "show-ref" and "--verify" in command:
                if command[-1] == f"refs/heads/{loop.work_branch}":
                    return True  # Branch exists
            # Simulate current branch check
            if command[0] == "rev-parse" and "--abbrev-ref" in command:
                return "different_branch"  # Current branch is different
            # Pass through to original for other commands
            return original_run_git(command, check, capture, cwd, **kwargs)

        # Apply the mock
        with patch.object(loop, "_run_git_command", side_effect=mock_run_git_command):
            with patch.object(loop, "_get_current_branch", return_value="different_branch"):
                # This should not exit due to our mocking
                loop._setup_environment()

    @patch("sys.exit")
    def test_setup_environment_handles_existing_worktree(self, mock_exit):
        """Test that _setup_environment handles the case where the worktree already exists."""
        loop = AgenticReviewLoop(latest_commit=True, use_worktree=True)
        loop.output_dir = self.temp_dir  # Use our temp dir for output
        loop.worktree_path = self.temp_dir / "worktree"

        # Create a mock for _run_git_command that simulates an existing worktree
        original_run_git = loop._run_git_command

        def mock_run_git_command(command, check=True, capture=False, cwd=None, **kwargs):
            # Simulate worktree list
            if command[0] == "worktree" and command[1] == "list":
                return f"worktree {loop.worktree_path}"
            # Simulate worktree removal (return None to indicate failure)
            if command[0] == "worktree" and command[1] == "remove":
                return None
            # Pass through to original for other commands
            return original_run_git(command, check, capture, cwd, **kwargs)

        # Apply the mock
        with patch.object(loop, "_run_git_command", side_effect=mock_run_git_command):
            with patch.object(loop, "_get_current_branch", return_value="different_branch"):
                with patch("shutil.rmtree"):  # Mock rmtree to avoid actual deletion
                    with patch.object(Path, "exists", return_value=True):  # Simulate path exists
                        # This should not exit due to our mocking
                        loop._setup_environment()


if __name__ == "__main__":
    unittest.main()
