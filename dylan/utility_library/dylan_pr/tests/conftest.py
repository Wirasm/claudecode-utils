"""Pytest fixtures for the dylan_pr module."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_git_branch_info():
    """Mock git branch information for PR tests."""
    return {
        "current_branch": "feature/test-branch",
        "target_branch": "develop",
        "remote_exists": True,
        "tracking_branch": "origin/feature/test-branch",
        "is_ahead": True,
        "is_behind": False,
        "ahead_count": 2,
        "behind_count": 0
    }


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    with patch("github.Github") as mock_github:
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Configure PR attributes
        mock_pr.number = 123
        mock_pr.html_url = "https://github.com/user/repo/pull/123"
        mock_pr.title = "Feature: Test Branch"

        # Configure repo methods
        mock_repo.create_pull.return_value = mock_pr
        mock_repo.get_pulls.return_value = [mock_pr]

        # Configure GitHub client
        mock_github.return_value.get_repo.return_value = mock_repo

        yield {
            "client": mock_github,
            "repo": mock_repo,
            "pr": mock_pr
        }


@pytest.fixture
def mock_gh_cli():
    """Mock GitHub CLI (gh) command responses."""
    with patch("subprocess.run") as mock_run:
        # Configure different responses based on command
        def side_effect(*args, **kwargs):
            command = args[0]
            mock_result = MagicMock()

            if isinstance(command, list):
                command_str = " ".join(command)
            else:
                command_str = command

            if "gh pr create" in command_str:
                mock_result.stdout = "https://github.com/user/repo/pull/123"
                mock_result.returncode = 0
            elif "gh pr list" in command_str:
                mock_result.stdout = "123\tFeature: Test Branch\tDRAFT\t2023-05-01"
                mock_result.returncode = 0
            else:
                mock_result.stdout = ""
                mock_result.returncode = 0

            return mock_result

        mock_run.side_effect = side_effect
        yield mock_run


@pytest.fixture
def mock_pr_runner():
    """Mock for the dylan_pr_runner module."""
    with patch("dylan.utility_library.dylan_pr.dylan_pr_runner") as mock_runner:
        mock_runner.generate_pr_description.return_value = "## Mock PR Description\n\nThis is a test PR."
        mock_runner.create_pull_request.return_value = {
            "url": "https://github.com/user/repo/pull/123",
            "number": 123,
            "title": "Feature: Test Branch"
        }
        yield mock_runner
