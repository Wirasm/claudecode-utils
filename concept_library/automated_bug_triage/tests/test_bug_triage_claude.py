#!/usr/bin/env -S uv run --script
"""
Tests for the Claude-driven Automated Bug Triage module.

These tests verify the core functionality of the Claude-driven bug triage tool.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from automated_bug_triage.bug_triage_claude_poc import run_claude_task


class TestBugTriageClaude(unittest.TestCase):
    """Test cases for the Claude-driven bug triage module."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample prompt for testing
        self.sample_prompt = """
        I need you to create a bug triage report for GitHub issues.
        Repository: test/repo
        Maximum issues to analyze: 1
        """

    @mock.patch("subprocess.run")
    @mock.patch("tempfile.NamedTemporaryFile")
    def test_run_claude_task(self, mock_tempfile, mock_run):
        """Test running a task with Claude Code."""
        # Mock tempfile
        mock_file = mock.MagicMock()
        mock_file.name = "temp_prompt.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        # Mock subprocess.run to return sample output
        mock_process = mock.Mock()
        mock_process.stdout = "Sample Claude output"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Call the function
        output = run_claude_task(self.sample_prompt, verbose=True)

        # Verify results
        self.assertEqual(output, "Sample Claude output")

        # Verify Claude was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args

        # Check that claude command was called
        self.assertTrue("claude" in args[0][0])

        # Check that prompt file was used
        self.assertTrue("@temp_prompt.txt" in args[0][2])

        # Check that bash tools were enabled
        self.assertTrue("Bash" in args[0][4])
        self.assertTrue("Write" in args[0][4])

        # Check that print flag was set
        self.assertTrue("--print" in args[0])

    @mock.patch("subprocess.run")
    @mock.patch("tempfile.NamedTemporaryFile")
    def test_run_claude_task_error(self, mock_tempfile, mock_run):
        """Test error handling when running Claude Code."""
        # Mock tempfile
        mock_file = mock.MagicMock()
        mock_file.name = "temp_prompt.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        # Mock subprocess.run to raise an error
        error = subprocess.CalledProcessError(1, "claude")
        error.stderr = "Command failed"
        mock_run.side_effect = error

        # Call the function
        output = run_claude_task(self.sample_prompt, verbose=True)

        # Verify results
        self.assertTrue(output.startswith("Error:"))

        # Verify Claude was called
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
