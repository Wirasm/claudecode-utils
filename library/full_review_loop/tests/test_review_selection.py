"""
Test review file selection logic in the agentic review loop module.

This module contains tests for the review file selection logic used in the AgenticReviewLoop class,
particularly in the run_developer method.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from full_review_loop.full_review_loop_safe import AgenticReviewLoop


class TestReviewFileSelection(unittest.TestCase):
    """Test the logic for selecting the appropriate review file for development."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a patched version of subprocess.run
        self.subprocess_run_patcher = patch("subprocess.run")
        self.mock_subprocess_run = self.subprocess_run_patcher.start()

        # Set up mock return value for subprocess.run
        self.mock_process = MagicMock()
        self.mock_process.stdout = "mocked_output"
        self.mock_process.returncode = 0
        self.mock_subprocess_run.return_value = self.mock_process

        # Create a loop instance with required parameters
        with patch.object(AgenticReviewLoop, "_get_repo_root"):
            with patch.object(AgenticReviewLoop, "_get_current_branch"):
                with patch.object(AgenticReviewLoop, "_setup_environment"):
                    self.loop = AgenticReviewLoop(latest_commit=True)
                    self.loop.output_dir = Path("/tmp/test_output")

    def tearDown(self):
        """Tear down test fixtures."""
        self.subprocess_run_patcher.stop()

    def test_review_selection_iteration_1(self):
        """Test review file selection for iteration 1."""
        self.loop.iteration = 1
        self.loop.review_file = self.loop.output_dir / "review_iter_1.md"

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            # Run a mocked version of run_developer that only tests the file selection
            with patch.object(self.loop, "run_claude", return_value="output"):
                # Mock writing to file
                with patch("builtins.open", unittest.mock.mock_open()):
                    self.loop.run_developer()

                    # For iteration 1, should use the initial review file
                    self.assertEqual(self.loop.current_review_for_dev, self.loop.review_file)

    def test_review_selection_iteration_gt_1_with_rereview(self):
        """Test review file selection for iteration > 1 with rereview file."""
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"
        self.loop.rereview_file = self.loop.output_dir / "rereview_iter_2.md"
        prev_rereview_file = self.loop.output_dir / "rereview_iter_1.md"

        # Set up a mock Path.exists method that returns specific values
        with patch.object(Path, "exists") as mock_exists:
            # Configure the mock to return True for all path checks
            mock_exists.return_value = True

            # Run a mocked version of run_developer that only tests the file selection
            with patch.object(self.loop, "run_claude", return_value="output"):
                # Mock writing to file
                with patch("builtins.open", unittest.mock.mock_open()):
                    self.loop.run_developer()

                    # For iteration > 1 with existing prev_rereview_file, should use that file
                    self.assertEqual(self.loop.current_review_for_dev, prev_rereview_file)

    def test_review_selection_iteration_gt_1_no_rereview(self):
        """Test review file selection for iteration > 1 without rereview file."""
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"
        # No rereview_file attribute set

        prev_review_file = self.loop.output_dir / "review_iter_1.md"

        # Mock path.exists to return different values for different paths
        original_exists = Path.exists
        
        def mock_exists(path_obj):
            if "rereview_iter_1.md" in str(path_obj):
                return False
            return True
            
        # Apply the patch to Path.exists
        with patch('pathlib.Path.exists', mock_exists):
            # Run a mocked version of run_developer that only tests the file selection
            with patch.object(self.loop, "run_claude", return_value="output"):
                # Mock writing to file
                with patch("builtins.open", unittest.mock.mock_open()):
                    self.loop.run_developer()

                    # For iteration > 1 but no prev_rereview_file, should use prev_review_file
                    self.assertEqual(self.loop.current_review_for_dev, prev_review_file)

    def test_review_selection_iteration_gt_1_fallback(self):
        """Test review file selection for iteration > 1 with fallback to current review."""
        self.loop.iteration = 2
        self.loop.review_file = self.loop.output_dir / "review_iter_2.md"
        # No rereview_file attribute set

        # Mock path.exists to return different values for different paths
        def mock_exists(path_obj):
            path_str = str(path_obj)
            if "rereview_iter_1.md" in path_str or "review_iter_1.md" in path_str:
                return False
            return True
            
        # Apply the patch
        with patch('pathlib.Path.exists', mock_exists):
            # Run a mocked version of run_developer that only tests the file selection
            with patch.object(self.loop, "run_claude", return_value="output"):
                # Mock writing to file
                with patch("builtins.open", unittest.mock.mock_open()):
                    self.loop.run_developer()

                    # When no previous review files exist, should fall back to current review
                    self.assertEqual(self.loop.current_review_for_dev, self.loop.review_file)


if __name__ == "__main__":
    unittest.main()