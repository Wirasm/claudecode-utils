"""Tests for provider_claude_code module (unit tests only, no provider calls)."""

from unittest.mock import patch

import pytest

from dylan.utility_library.provider_clis.provider_claude_code import ClaudeProvider, get_provider


def test_get_provider():
    """Test the get_provider factory function without invoking Claude."""
    # Test with default (claude)
    provider = get_provider()
    assert isinstance(provider, ClaudeProvider)

    # Test with explicit claude provider
    provider = get_provider("claude")
    assert isinstance(provider, ClaudeProvider)

    # Test with unsupported provider
    with pytest.raises(ValueError):
        get_provider("unsupported")


@patch("subprocess.Popen")
@patch("shutil.which")
def test_claude_provider_prepare_prompt(mock_which, mock_popen):
    """Test the _prepare_prompt method of ClaudeProvider."""
    # Setup mock for shutil.which
    mock_which.return_value = "/usr/local/bin/claude"

    # Create provider
    provider = ClaudeProvider()

    # Test with basic prompt
    prompt = "Test prompt"
    prepared_prompt = provider._prepare_prompt(prompt)

    # Verify prompt contains directive
    assert "Test prompt" in prepared_prompt
    assert "tmp/" in prepared_prompt

    # Test with output path
    output_path = "./test_output.md"
    prepared_prompt = provider._prepare_prompt(prompt, output_path)

    # Verify prompt contains output path directive
    assert output_path in prepared_prompt
    assert "WITHOUT asking for confirmation" in prepared_prompt


@patch("subprocess.Popen")
def test_claude_provider_build_command(mock_popen):
    """Test the _build_command method of ClaudeProvider."""
    # The provider uses the actual claude path, which is set when the class is defined
    # Let's test the command structure instead of the exact path

    # Create provider
    provider = ClaudeProvider()

    # Test with basic prompt
    cmd = provider._build_command("Test prompt")

    # Verify command structure
    assert len(cmd) >= 3
    assert "claude" in cmd[0]  # Path should contain "claude"
    assert cmd[1] == "-p"
    assert cmd[2] == "Test prompt"

    # Test with additional parameters
    cmd = provider._build_command(
        "Test prompt with options",
        output_format="json",
        allowed_tools=["Read", "Write"]
    )

    # Verify command includes options
    assert "--output-format" in cmd
    assert "json" in cmd
    assert "Read" in cmd
    assert "Write" in cmd
