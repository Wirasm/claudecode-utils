#!/usr/bin/env python3
"""Tests for file selection helper methods in AgenticReviewLoop."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from full_review_loop.full_review_loop_safe import AgenticReviewLoop


class TestFileSelectionHelper(unittest.TestCase):
    """Test suite for the get_appropriate_review_file helper method."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Create a mock review loop instance
        self.loop = MagicMock(spec=AgenticReviewLoop)
        self.loop.output_dir = Path("/tmp/test_output")
        self.loop.iteration = 1

        # Add the method we're testing to the mock instance
        # This is required because we can't create a real instance easily
        self.loop.get_appropriate_review_file = (
            AgenticReviewLoop.get_appropriate_review_file.__get__(self.loop, AgenticReviewLoop)
        )

    def test_initial_review_iteration_1(self) -> None:
        """Test getting initial review file for iteration 1."""
        # Setup
        self.loop.review_file = self.loop.output_dir / "review_iter_1.md"

        # Call method and verify
        result = self.loop.get_appropriate_review_file(is_rereview=False)
        self.assertEqual(result, self.loop.review_file)

    def test_rereview_iteration_1(self) -> None:
        """Test getting re-review file for iteration 1."""
        # Setup
        self.loop.rereview_file = self.loop.output_dir / "rereview_iter_1.md"

        # Call method and verify
        result = self.loop.get_appropriate_review_file(is_rereview=True)
        self.assertEqual(result, self.loop.rereview_file)

    def test_for_developer_with_prev_rereview(self) -> None:
        """Test getting appropriate review file for developer with previous re-review."""
        # Setup
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"
        prev_rereview = self.loop.output_dir / "rereview_iter_1.md"

        # Mock Path.exists to simulate file existence
        original_exists = Path.exists

        def mock_exists(path):
            if str(path).endswith("rereview_iter_1.md"):
                return True
            return False

        # Apply the mock
        Path.exists = mock_exists

        try:
            # Call method and verify
            result = self.loop.get_appropriate_review_file(for_developer=True)
            self.assertEqual(result, prev_rereview)
        finally:
            # Restore original method
            Path.exists = original_exists

    def test_for_developer_fallback_to_prev_review(self) -> None:
        """Test developer fallback to previous review when re-review doesn't exist."""
        # Setup
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"
        prev_review = self.loop.output_dir / "review_iter_1.md"

        # Mock Path.exists to simulate file existence
        original_exists = Path.exists

        def mock_exists(path):
            if str(path).endswith("rereview_iter_1.md"):
                return False
            if str(path).endswith("review_iter_1.md"):
                return True
            return False

        # Apply the mock
        Path.exists = mock_exists

        try:
            # Call method and verify
            result = self.loop.get_appropriate_review_file(for_developer=True)
            self.assertEqual(result, prev_review)
        finally:
            # Restore original method
            Path.exists = original_exists

    def test_for_developer_fallback_to_current_review(self) -> None:
        """Test developer fallback to current review when no previous files exist."""
        # Setup
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"

        # Mock Path.exists to simulate file existence
        original_exists = Path.exists

        def mock_exists(path):
            return False

        # Apply the mock
        Path.exists = mock_exists

        try:
            # Call method and verify
            result = self.loop.get_appropriate_review_file(for_developer=True)
            self.assertEqual(result, self.loop.review_file)
        finally:
            # Restore original method
            Path.exists = original_exists

    def test_for_validator_uses_current_rereview(self) -> None:
        """Test validator using current re-review."""
        # Setup
        self.loop.iteration = 1
        self.loop.rereview_file = self.loop.output_dir / "rereview_iter_1.md"

        # Call method and verify
        result = self.loop.get_appropriate_review_file(for_validator=True)
        self.assertEqual(result, self.loop.rereview_file)

    def test_missing_file_raises_error(self) -> None:
        """Test error raised when required file doesn't exist."""
        # Setup
        self.loop.iteration = 1
        self.loop.review_file = self.loop.output_dir / "review_iter_1.md"

        # Mock Path.exists to simulate file non-existence
        original_exists = Path.exists

        def mock_exists(path):
            return False

        # Apply the mock
        Path.exists = mock_exists

        try:
            # Call method and verify exception
            with self.assertRaises(FileNotFoundError):
                self.loop.get_appropriate_review_file(is_rereview=False, required=True)
        finally:
            # Restore original method
            Path.exists = original_exists


if __name__ == "__main__":
    unittest.main()
