#!/usr/bin/env -S uv run --script
"""
Tests for the Automated Bug Triage module.

These tests verify the core functionality of the bug triage tool.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from automated_bug_triage.bug_triage_poc import (
    analyze_issue_with_claude,
    fetch_issues_with_github_cli,
    fetch_repository_structure,
    generate_report,
)


class TestBugTriage(unittest.TestCase):
    """Test cases for the bug triage module."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample issue data
        self.sample_issue = {
            "number": 123,
            "title": "App crashes when uploading large files",
            "body": "When I try to upload a file larger than 100MB, the application crashes with an out of memory error.",
            "createdAt": "2023-01-01T00:00:00Z",
            "updatedAt": "2023-01-02T00:00:00Z",
            "labels": [{"name": "bug"}, {"name": "critical"}],
            "url": "https://github.com/test/repo/issues/123",
        }

        # Sample repository structure
        self.sample_repo_structure = {
            "src": ["src/upload.py", "src/main.py"],
            "docs": ["docs/README.md"],
            "tests": ["tests/test_upload.py"],
        }

        # Sample analysis result
        self.sample_analysis = {
            "severity": "high",
            "bug_type": "functional",
            "component": "src",
            "reproduction_steps": [
                "Open the application",
                "Go to the upload page",
                "Select a file larger than 100MB",
                "Click the upload button",
            ],
            "fix_suggestions": [
                "Implement chunked file uploads",
                "Add memory usage monitoring",
                "Set maximum upload size limit",
            ],
            "reasoning": "This is a critical issue affecting core functionality.",
        }

    @mock.patch("subprocess.run")
    def test_fetch_issues_with_github_cli(self, mock_run):
        """Test fetching issues using GitHub CLI."""
        # Mock subprocess.run to return sample issue data
        mock_process = mock.Mock()
        mock_process.stdout = json.dumps([self.sample_issue])
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Call the function
        issues = fetch_issues_with_github_cli("test/repo", verbose=True)

        # Verify results
        self.assertIsNotNone(issues)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["number"], 123)
        self.assertEqual(issues[0]["title"], "App crashes when uploading large files")

        # Verify GitHub CLI was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertTrue("gh" in args[0][0])
        self.assertTrue("issue" in args[0][1])

    @mock.patch("subprocess.run")
    def test_fetch_repository_structure(self, mock_run):
        """Test fetching repository structure."""
        # Mock subprocess.run to return sample repository structure
        mock_process = mock.Mock()
        mock_process.stdout = json.dumps(
            {
                "tree": [
                    {"path": "src/upload.py", "type": "blob"},
                    {"path": "src/main.py", "type": "blob"},
                    {"path": "docs/README.md", "type": "blob"},
                    {"path": "tests/test_upload.py", "type": "blob"},
                ]
            }
        )
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Call the function
        structure = fetch_repository_structure("test/repo", verbose=True)

        # Verify results
        self.assertIsNotNone(structure)
        self.assertIn("src", structure)
        self.assertIn("docs", structure)
        self.assertIn("tests", structure)
        self.assertEqual(len(structure["src"]), 2)

        # Verify GitHub API was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertTrue("gh" in args[0][0])
        self.assertTrue("api" in args[0][1])

    @mock.patch("subprocess.run")
    @mock.patch("tempfile.NamedTemporaryFile")
    def test_analyze_issue_with_claude(self, mock_tempfile, mock_run):
        """Test analyzing an issue with Claude."""
        # Mock tempfile
        mock_file = mock.MagicMock()
        mock_file.name = "temp_prompt.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        # Mock subprocess.run to return sample analysis
        mock_process = mock.Mock()
        mock_process.stdout = f"""
        Here's my analysis:
        
        ```json
        {json.dumps(self.sample_analysis)}
        ```
        """
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Call the function
        analysis = analyze_issue_with_claude(
            self.sample_issue, self.sample_repo_structure, verbose=True
        )

        # Verify results
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis["severity"], "high")
        self.assertEqual(analysis["bug_type"], "functional")
        self.assertEqual(len(analysis["reproduction_steps"]), 4)

        # Verify Claude was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertTrue("claude" in args[0][0])

    def test_generate_report(self):
        """Test report generation."""
        # Create a temporary output file
        output_file = "test_report.md"

        # Call the function
        issues = [self.sample_issue]
        analyses = {123: self.sample_analysis}
        report_path = generate_report(issues, analyses, output_file, verbose=True)

        # Verify results
        self.assertEqual(report_path, output_file)
        self.assertTrue(os.path.exists(output_file))

        # Read the report content
        with open(output_file, "r") as f:
            content = f.read()

        # Verify report content
        self.assertIn("Automated Bug Triage Report", content)
        self.assertIn("Issue #123", content)
        self.assertIn("App crashes when uploading large files", content)
        self.assertIn("high", content.lower())
        self.assertIn("functional", content.lower())

        # Clean up
        os.remove(output_file)


if __name__ == "__main__":
    unittest.main()
