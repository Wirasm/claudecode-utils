"""Tests for the main Dylan CLI."""

from unittest.mock import patch

from dylan.cli import app


def test_cli_main_command(cli_runner):
    """Test the main CLI command with no arguments."""
    result = cli_runner.invoke(app)
    assert result.exit_code == 0

    # Should show welcome message and commands table
    assert "Dylan" in result.stdout
    assert "AI-powered development utilities" in result.stdout
    assert "standup" in result.stdout
    assert "review" in result.stdout
    assert "pr" in result.stdout
    assert "release" in result.stdout


def test_cli_help_command(cli_runner):
    """Test the CLI help command."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    # Should show help information
    assert "Usage" in result.stdout
    assert "Options" in result.stdout
    assert "Commands" in result.stdout


@patch("dylan.utility_library.dylan_review.dylan_review_cli.review")
def test_cli_review_command_invocation(mock_review, cli_runner):
    """Test that the review command is properly registered."""
    # Set up mock review command to verify it's called
    mock_review.__name__ = "review"

    # Run the review command through the main CLI
    result = cli_runner.invoke(app, ["review", "--help"])

    # Command should be properly dispatched through the CLI
    assert result.exit_code == 0

    # Basic test to ensure the command is registered and docs are accessible
    assert "review" in result.stdout.lower()


@patch("dylan.utility_library.dylan_standup.standup_typer.standup_app")
def test_cli_standup_command_invocation(mock_standup_app, cli_runner):
    """Test that the standup command is properly registered."""
    # Set up mock standup app
    mock_standup_app.callback.__name__ = "standup"

    # Run the standup command through the main CLI
    result = cli_runner.invoke(app, ["standup", "--help"])

    # Command should be properly dispatched through the CLI
    assert result.exit_code == 0

    # Basic test to ensure the command is registered
    assert "standup" in result.stdout.lower()


@patch("dylan.utility_library.dylan_pr.dylan_pr_cli.pr")
def test_cli_pr_command_invocation(mock_pr, cli_runner):
    """Test that the PR command is properly registered."""
    # Set up mock PR command to verify it's called
    mock_pr.__name__ = "pr"

    # Run the PR command through the main CLI
    result = cli_runner.invoke(app, ["pr", "--help"])

    # Command should be properly dispatched through the CLI
    assert result.exit_code == 0

    # Basic test to ensure the command is registered
    assert "pr" in result.stdout.lower()


@patch("dylan.utility_library.dylan_release.dylan_release_cli.release_app")
def test_cli_release_command_invocation(mock_release_app, cli_runner):
    """Test that the release command is properly registered."""
    # Set up mock release app
    mock_release_app.callback.__name__ = "release"

    # Run the release command through the main CLI
    result = cli_runner.invoke(app, ["release", "--help"])

    # Command should be properly dispatched through the CLI
    assert result.exit_code == 0

    # Basic test to ensure the command is registered
    assert "release" in result.stdout.lower()
