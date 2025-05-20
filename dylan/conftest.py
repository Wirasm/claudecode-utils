"""Global pytest fixtures and configuration for Dylan package."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_claude_provider():
    """Mock Claude provider for testing.

    Returns a MagicMock with a configured generate method that returns a predictable response.
    This allows testing code that depends on the Claude provider without making actual API calls.
    """
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Mock response from Claude"
    with patch("dylan.utility_library.provider_clis.provider_claude_code.get_provider",
               return_value=mock_provider):
        yield mock_provider


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory):
    """Create a temporary directory for test outputs.

    This session-scoped fixture creates a temporary directory that persists
    for the duration of the test session, allowing tests to create and verify files.

    Args:
        tmp_path_factory: pytest's built-in tmp_path_factory fixture

    Returns:
        pathlib.Path: Path to the temporary directory
    """
    temp_dir = tmp_path_factory.mktemp("dylan_test_output")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


@pytest.fixture
def cli_runner():
    """Fixture for running CLI commands in tests.

    Creates a test CLI runner that can capture output and exceptions
    from Typer CLI commands, allowing testing of CLI interfaces.

    Returns:
        typer.testing.CliRunner: A CLI runner for testing commands
    """
    from typer.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a minimal mock git repository.

    This fixture creates a temporary directory with a minimal git repo structure
    for testing git-dependent features without actual git operations.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        pathlib.Path: Path to the mock git repository
    """
    repo_path = tmp_path / "mock_repo"
    os.makedirs(repo_path, exist_ok=True)

    # Create a mock .git directory
    git_dir = repo_path / ".git"
    os.makedirs(git_dir, exist_ok=True)

    return repo_path


@pytest.fixture
def mock_git_operations():
    """Mock wrapper for git operations.

    Provides mocks for common git operations used in the codebase,
    allowing tests to run without actual git commands.

    Returns:
        dict: Dictionary of mock functions for git operations
    """
    git_diff_mock = MagicMock(return_value="""
diff --git a/example.py b/example.py
index abc123..def456 100644
--- a/example.py
+++ b/example.py
@@ -10,7 +10,7 @@ def example_function():
     print("Hello World")
-    return None
+    return "Hello"
""")

    git_branch_mock = MagicMock(return_value="feature-branch")
    git_status_mock = MagicMock(return_value="On branch feature-branch\nChanges not staged for commit")

    with patch("subprocess.run") as subprocess_run_mock:
        # Configure the mock to return different values based on the command
        def side_effect(*args, **kwargs):
            command = args[0]
            mock_result = MagicMock()

            if isinstance(command, list):
                command_str = " ".join(command)
            else:
                command_str = command

            if "git diff" in command_str:
                mock_result.stdout = git_diff_mock()
                mock_result.returncode = 0
            elif "git branch" in command_str:
                mock_result.stdout = git_branch_mock()
                mock_result.returncode = 0
            elif "git status" in command_str:
                mock_result.stdout = git_status_mock()
                mock_result.returncode = 0
            else:
                mock_result.stdout = ""
                mock_result.returncode = 0

            return mock_result

        subprocess_run_mock.side_effect = side_effect

        yield {
            "diff": git_diff_mock,
            "branch": git_branch_mock,
            "status": git_status_mock,
            "subprocess_run": subprocess_run_mock
        }
