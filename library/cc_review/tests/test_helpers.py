"""Tests for the main module."""

import sys
from io import StringIO
from unittest.mock import patch

from library.cc_review.main import main


def test_main_output():
    """Test that the main function prints the expected output."""
    # Capture stdout to test the printed output
    captured_output = StringIO()
    sys.stdout = captured_output

    # Call the main function
    main()

    # Reset stdout
    sys.stdout = sys.__stdout__

    # Check the output
    output = captured_output.getvalue().strip()
    assert "Hello from CC Library!" in output
    assert "simple utility library" in output
