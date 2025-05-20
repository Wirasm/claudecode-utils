"""Pytest fixtures for the dylan_review module."""

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_git_diff():
    """Mock git diff response for review tests."""
    return """
diff --git a/example.py b/example.py
index abc123..def456 100644
--- a/example.py
+++ b/example.py
@@ -10,7 +10,7 @@ def example_function():
     print("Hello World")
-    return None
+    return "Hello"
"""


@pytest.fixture
def sample_review_report():
    """Sample review report fixture for testing."""
    return {
        "metadata": {
            "branch": "feature-branch",
            "timestamp": "2023-05-01T12:00:00Z",
            "base_branch": "main",
        },
        "summary": "Found 3 issues in the code changes.",
        "issues": [
            {
                "severity": "HIGH",
                "type": "BUG",
                "description": "Function returns string instead of None, which breaks type contract",
                "file": "example.py",
                "line": 11,
                "suggested_fix": "Change `return \"Hello\"` to `return None`"
            },
            {
                "severity": "MEDIUM",
                "type": "STYLE",
                "description": "Inconsistent return style in function",
                "file": "example.py",
                "line": 11,
                "suggested_fix": "Ensure consistent return style across functions"
            },
            {
                "severity": "LOW",
                "type": "DOCUMENTATION",
                "description": "Missing docstring updates to reflect return type change",
                "file": "example.py",
                "line": 10,
                "suggested_fix": "Update function docstring to reflect new return type"
            }
        ],
        "recommendations": [
            "Consider adding type annotations to make return types explicit",
            "Add unit tests to verify function behavior"
        ]
    }


@pytest.fixture
def mock_review_runner():
    """Mock for the dylan_review_runner module."""
    with patch("dylan.utility_library.dylan_review.dylan_review_runner") as mock_runner:
        mock_runner.generate_review_prompt.return_value = "Mock review prompt"
        mock_runner.run_claude_review.return_value = "Review completed successfully"
        yield mock_runner
