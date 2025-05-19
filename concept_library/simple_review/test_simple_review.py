#!/usr/bin/env python3
"""
Unit tests for the simple_review.py script.

These tests cover the key functionality of the script, including:
- Branch name validation
- Default branch detection
- Unique filename generation
- Command execution
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from simple_review import (
    DEFAULT_BRANCH_NAME,
    check_base_branch_exists,
    check_branch_exists,
    check_git_repo,
    get_default_branch,
    get_unique_filename,
    run_review,
    validate_branch_name,
    validate_output_path,
)


class TestBranchValidation:
    """Tests for branch name validation functionality."""

    def test_valid_branch_names(self):
        """Test that valid branch names are accepted."""
        valid_names = [
            "main",
            "master",
            "development",
            "feature/new-feature",
            "bugfix/issue-123",
            "release/v1.0.0",
            "user/john/feature",
            "v1.2.3",
            "hotfix_urgent",
        ]
        for name in valid_names:
            assert validate_branch_name(name), f"Branch name '{name}' should be valid"

    def test_invalid_branch_names(self):
        """Test that invalid branch names are rejected."""
        invalid_names = [
            "branch; rm -rf /",
            "branch && echo 'hacked'",
            "$(echo malicious)",
            "`rm important.txt`",
            "branch | grep secret",
            "branch > /etc/passwd",
            "branch\nrm file",
        ]
        for name in invalid_names:
            assert not validate_branch_name(name), f"Branch name '{name}' should be invalid"


class TestGitOperations:
    """Tests for git-related operations."""

    @patch("subprocess.run")
    def test_check_git_repo_success(self, mock_run):
        """Test successful git repository check."""
        # Mock successful subprocess execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        assert check_git_repo() is True

    @patch("subprocess.run")
    def test_check_git_repo_failure(self, mock_run):
        """Test failed git repository check."""
        # Mock failed subprocess execution
        mock_run.side_effect = Exception("Not a git repository")

        assert check_git_repo() is False

    @patch("subprocess.run")
    def test_check_branch_exists_success(self, mock_run):
        """Test successful branch existence check."""
        # Mock successful subprocess execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        assert check_branch_exists("main") is True

    @patch("subprocess.run")
    def test_check_branch_exists_failure(self, mock_run):
        """Test failed branch existence check."""
        # Mock failed subprocess execution
        mock_run.side_effect = Exception("Branch does not exist")

        assert check_branch_exists("nonexistent-branch") is False

    @patch("subprocess.run")
    def test_check_base_branch_exists_local(self, mock_run):
        """Test successful base branch existence check for local branch."""

        # Mock successful subprocess execution for local branch
        def side_effect(*args, **kwargs):
            if "refs/heads/main" in args[0]:
                # Local branch check succeeds
                return MagicMock(returncode=0)
            else:
                # Should not get to remote check
                raise AssertionError("Should not check remote if local exists")

        mock_run.side_effect = side_effect
        assert check_base_branch_exists("main") is True

    @patch("subprocess.run")
    def test_check_base_branch_exists_remote(self, mock_run):
        """Test successful base branch existence check for remote branch."""

        # Mock local branch check fails but remote succeeds
        def side_effect(*args, **kwargs):
            if "refs/heads/" in args[0][3]:
                # Local branch check fails
                raise subprocess.CalledProcessError(1, "git")
            elif "refs/remotes/origin/" in args[0][3]:
                # Remote branch check succeeds
                return MagicMock(returncode=0)

        mock_run.side_effect = side_effect
        assert check_base_branch_exists("main") is True

    @patch("subprocess.run")
    def test_check_base_branch_exists_failure(self, mock_run):
        """Test failed base branch existence check."""
        # Mock both local and remote checks fail
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert check_base_branch_exists("nonexistent-branch") is False

    @patch("subprocess.run")
    def test_get_default_branch_from_origin(self, mock_run):
        """Test getting default branch from origin HEAD."""
        # Mock successful subprocess execution for origin HEAD
        mock_process = MagicMock()
        mock_process.stdout = "refs/remotes/origin/main"
        mock_run.return_value = mock_process

        assert get_default_branch() == "main"

    @patch("subprocess.run")
    def test_get_default_branch_fallback(self, mock_run):
        """Test fallback to default branch name."""
        # Mock failed subprocess execution
        mock_run.side_effect = Exception("Cannot determine default branch")

        assert get_default_branch() == DEFAULT_BRANCH_NAME


class TestFileOperations:
    """Tests for file-related operations."""

    def test_get_unique_filename_nonexistent(self, tmp_path):
        """Test unique filename generation for non-existent file."""
        test_file = tmp_path / "test.md"
        assert get_unique_filename(str(test_file)) == str(test_file)

    def test_get_unique_filename_existing(self, tmp_path):
        """Test unique filename generation for existing file."""
        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")

        # Get unique filename
        unique_name = get_unique_filename(str(test_file))

        # Verify it's different and contains a timestamp
        assert unique_name != str(test_file)
        assert "_20" in unique_name  # Should contain timestamp like _20250511_
        assert unique_name.endswith(".md")

        # Verify it uses Path objects correctly to avoid path traversal
        unique_path = Path(unique_name)
        assert unique_path.parent == test_file.parent

    def test_validate_output_path_valid(self, tmp_path):
        """Test validation of a valid output path."""
        test_file = tmp_path / "test.md"
        is_valid, _ = validate_output_path(str(test_file))
        assert is_valid is True

    def test_validate_output_path_invalid_dir(self, tmp_path):
        """Test validation of an output path with invalid directory."""
        # Create a path that should not be writable
        invalid_dir = tmp_path / "nonexistent" / "deeply" / "nested"
        test_file = invalid_dir / "test.md"

        # Mock os.access to return False for this directory
        with patch("os.access", return_value=False):
            is_valid, error_msg = validate_output_path(str(test_file))
            assert is_valid is False
            assert "permission" in error_msg.lower()

    def test_validate_output_path_permission_error(self, tmp_path):
        """Test validation of an output path with permission error."""
        test_file = tmp_path / "test.md"

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            is_valid, error_msg = validate_output_path(str(test_file))
            assert is_valid is False
            assert "permission" in error_msg.lower()


class TestReviewFunction:
    """Tests for the main review function."""

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=MagicMock)
    def test_run_review_with_invalid_branch(self, mock_open, mock_run):
        """Test review with invalid branch name."""
        result = run_review("invalid; rm -rf /", "output.md", verbose=True)
        assert result is False
        mock_open.assert_not_called()

    @patch("simple_review.check_git_repo")
    def test_run_review_not_in_git_repo(self, mock_check_git_repo):
        """Test review when not in a git repository."""
        mock_check_git_repo.return_value = False
        result = run_review("main", "output.md")
        assert result is False

    @patch("simple_review.check_git_repo")
    @patch("simple_review.validate_branch_name")
    @patch("simple_review.check_branch_exists")
    def test_run_review_nonexistent_branch(
        self, mock_check_branch, mock_validate, mock_check_git_repo
    ):
        """Test review with non-existent branch."""
        mock_check_git_repo.return_value = True
        mock_validate.return_value = True
        mock_check_branch.return_value = False

        result = run_review("nonexistent", "output.md")
        assert result is False

    @patch("simple_review.check_git_repo")
    @patch("simple_review.validate_branch_name")
    @patch("simple_review.check_branch_exists")
    @patch("simple_review.validate_output_path")
    def test_run_review_invalid_output_path(
        self, mock_validate_path, mock_check_branch, mock_validate, mock_check_git_repo
    ):
        """Test review with invalid output path."""
        mock_check_git_repo.return_value = True
        mock_validate.return_value = True
        mock_check_branch.return_value = True
        mock_validate_path.return_value = (False, "Invalid path")

        result = run_review("main", "output.md")
        assert result is False

    @patch("simple_review.check_git_repo")
    @patch("simple_review.validate_branch_name")
    @patch("simple_review.check_branch_exists")
    @patch("simple_review.validate_output_path")
    @patch("simple_review.check_base_branch_exists")
    def test_run_review_nonexistent_base_branch(
        self,
        mock_check_base,
        mock_validate_path,
        mock_check_branch,
        mock_validate,
        mock_check_git_repo,
    ):
        """Test review with non-existent base branch."""
        mock_check_git_repo.return_value = True
        mock_validate.return_value = True
        mock_check_branch.return_value = True
        mock_validate_path.return_value = (True, "")
        mock_check_base.return_value = False

        result = run_review("main", "output.md", base_branch="nonexistent")
        assert result is False

    @patch("simple_review.check_git_repo")
    @patch("simple_review.validate_branch_name")
    @patch("simple_review.check_branch_exists")
    @patch("simple_review.validate_output_path")
    @patch("simple_review.get_default_branch")
    @patch("subprocess.run")
    @patch("simple_review.get_unique_filename")
    @patch("builtins.open", new_callable=MagicMock)
    def test_run_review_success(
        self,
        mock_open,
        mock_get_filename,
        mock_subprocess,
        mock_get_default,
        mock_validate_path,
        mock_check_branch,
        mock_validate,
        mock_check_git_repo,
    ):
        """Test successful review execution."""
        # Setup all the mocks for a successful run
        mock_check_git_repo.return_value = True
        mock_validate.return_value = True
        mock_check_branch.return_value = True
        mock_validate_path.return_value = (True, "")
        mock_get_default.return_value = "main"

        # Mock subprocess.run to return a successful result
        mock_process = MagicMock()
        mock_process.stdout = "Review content"
        mock_subprocess.return_value = mock_process

        # Mock get_unique_filename to return the same filename
        mock_get_filename.return_value = "output.md"

        # Run the review function
        result = run_review("feature", "output.md", timeout=60)

        # Verify the result and that subprocess was called with the right timeout
        assert result is True or result == (True, "")
        mock_subprocess.assert_called_once()
        # Check that timeout was passed correctly
        assert mock_subprocess.call_args[1]["timeout"] == 60

    @patch("simple_review.check_git_repo")
    @patch("simple_review.validate_branch_name")
    @patch("simple_review.check_branch_exists")
    @patch("simple_review.validate_output_path")
    @patch("subprocess.run")
    def test_run_review_file_write_error(
        self,
        mock_subprocess,
        mock_validate_path,
        mock_check_branch,
        mock_validate,
        mock_check_git_repo,
    ):
        """Test review with file write error."""
        # Setup mocks for a successful run until file writing
        mock_check_git_repo.return_value = True
        mock_validate.return_value = True
        mock_check_branch.return_value = True
        mock_validate_path.return_value = (True, "")

        # Mock subprocess.run to return a successful result
        mock_process = MagicMock()
        mock_process.stdout = "Review content"
        mock_subprocess.return_value = mock_process

        # Mock open to raise an exception
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = run_review("feature", "output.md")
            assert result is False


if __name__ == "__main__":
    pytest.main()
