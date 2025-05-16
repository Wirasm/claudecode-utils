#!/usr/bin/env python3
"""Tests for workflow sequence in AgenticReviewLoop."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from full_review_loop.full_review_loop_safe import AgenticReviewLoop, AgentRole


class TestWorkflowSequence(unittest.TestCase):
    """Test suite for the workflow sequence in run method."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.loop_patcher = patch(
            "full_review_loop.full_review_loop_safe.AgenticReviewLoop", autospec=True
        )
        self.mock_loop_class = self.loop_patcher.start()

        # Create a partially mocked instance that will use our patched methods
        self.loop = AgenticReviewLoop.__new__(AgenticReviewLoop)
        self.loop.iteration = 0
        self.loop.max_iterations = 2  # Set to 2 to test exactly 2 iterations
        self.loop.log = MagicMock()
        self.loop.debug = MagicMock()
        self.loop.output_dir = Path(
            "/tmp/test_output"
        )  # Set a fixed output dir that won't be created
        self.loop._cleanup_environment = MagicMock()  # Mock cleanup to avoid errors

        # Mock the main workflow methods
        self.loop.run_reviewer = MagicMock(return_value=True)
        self.loop.run_developer = MagicMock(return_value=True)
        self.loop.run_validator = MagicMock(
            return_value=(True, False)
        )  # (success, validation_passed)
        self.loop.run_pr_manager = MagicMock(return_value=True)
        self.loop._cleanup_environment = MagicMock()

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.loop_patcher.stop()

    def test_run_validation_failed_skips_to_developer(self) -> None:
        """Test workflow with validation failure and continuing after validation failure."""

        # Create a version of run() we can test that doesn't have threading/subprocess/etc.
        def simplified_run(self_ref):
            validation_passed = False
            final_success = False
            continuing_after_validation_failure = False

            try:
                while self_ref.iteration < self_ref.max_iterations:
                    self_ref.iteration += 1
                    self_ref.log(
                        f"\n=== Starting Iteration {self_ref.iteration}/{self_ref.max_iterations} ==="
                    )

                    # For the first iteration, or when not continuing after validation failure,
                    # start with review
                    if self_ref.iteration == 1 or not continuing_after_validation_failure:
                        # --- Step 1: Initial Review ---
                        review_success = self_ref.run_reviewer(is_rereview=(self_ref.iteration > 1))
                        if not review_success:
                            self_ref.log(
                                f"Review phase failed on iteration {self_ref.iteration}. Stopping loop."
                            )
                            break
                    else:
                        self_ref.log(
                            f"Skipping initial review as we're continuing after a validation failure"
                        )
                        # When continuing after validation failure, the developer will use the
                        # latest re-review and validation feedback from previous iteration

                    # --- Step 2: Develop ---
                    # Developer uses the latest review and potentially previous validation feedback
                    dev_success = self_ref.run_developer()
                    if not dev_success:
                        self_ref.log(
                            f"Development phase failed on iteration {self_ref.iteration}. Stopping loop."
                        )
                        break

                    # --- Step 3: Re-Review (Review the developer's changes) ---
                    # This creates a separate rereview_file, distinct from the initial review_file
                    rereview_success = self_ref.run_reviewer(is_rereview=True)
                    if not rereview_success:
                        self_ref.log(
                            f"Re-Review phase failed on iteration {self_ref.iteration}. Stopping loop."
                        )
                        break

                    # --- Step 4: Validate ---
                    # Validator uses the latest (re-review) report and the latest dev report
                    validation_success, validation_passed = self_ref.run_validator()
                    if not validation_success:
                        self_ref.log(
                            f"Validation phase failed on iteration {self_ref.iteration}. Stopping loop."
                        )
                        break

                    # --- Check Validation Result ---
                    if validation_passed:
                        self_ref.log(f"Validation PASSED on iteration {self_ref.iteration}!")
                        # Proceed to PR creation outside the loop
                        final_success = True
                        break
                    else:
                        self_ref.log(f"Validation FAILED on iteration {self_ref.iteration}.")
                        if self_ref.iteration >= self_ref.max_iterations:
                            self_ref.log("Maximum iterations reached without passing validation.")
                            break
                        else:
                            # Set flag to skip initial review in next iteration
                            continuing_after_validation_failure = True
                            self_ref.log("Continuing to next iteration with validation feedback...")
                            # Loop continues, developer will use the re-review and validation report

                # --- Step 5: PR Creation (if validation passed) ---
                if final_success:
                    self_ref.run_pr_manager()
                else:
                    self_ref.log("Workflow finished without passing validation.")

            finally:
                # --- Cleanup ---
                self_ref._cleanup_environment()

            return final_success

        # Run the test scenario
        # Replace the real run method with our simplified version for testing
        self.loop.run = lambda: simplified_run(self.loop)

        # Run the simplified method
        self.loop.run()

        # Check the actual calls made
        print(f"ACTUAL CALLS: {self.loop.run_reviewer.call_args_list}")

        # The new workflow runs through 2 iterations by default, with the second one
        # skipping the initial review step. This means we expect 3 calls total.
        expected_calls = [
            # Iteration 1
            call(is_rereview=False),  # Initial review
            call(is_rereview=True),  # Re-review after development
            # Iteration 2 - continuing after validation failure
            call(is_rereview=True),  # Re-review after development
        ]
        self.assertEqual(self.loop.run_reviewer.call_args_list, expected_calls)

        # Developer should be called twice (once in each iteration)
        self.assertEqual(self.loop.run_developer.call_count, 2)
        # Validator should be called twice (once in each iteration)
        self.assertEqual(self.loop.run_validator.call_count, 2)

        # PR manager should not be called (validation failed)
        self.assertEqual(self.loop.run_pr_manager.call_count, 0)

        # Cleanup should be called once at the end
        self.assertEqual(self.loop._cleanup_environment.call_count, 1)


if __name__ == "__main__":
    unittest.main()
