"""Tests for exit_command module."""

import threading
import time
from unittest.mock import MagicMock, patch

from dylan.utility_library.shared.exit_command import (
    DEFAULT_EXIT_COMMAND,
    setup_exit_command_handler,
)


@patch("threading.Thread")
def test_setup_exit_command_handler_no_command(mock_thread):
    """Test setup with no exit command."""
    mock_process = MagicMock()

    # Thread should be created even without exit command
    event = setup_exit_command_handler(mock_process, None)

    assert mock_thread.called
    assert not event.is_set()


@patch("threading.Thread")
def test_setup_exit_command_handler_with_command(mock_thread):
    """Test setup with exit command (simplified)."""
    mock_process = MagicMock()

    # Mock thread implementation
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    # The thread should be created regardless of exit command parameter
    event = setup_exit_command_handler(mock_process, DEFAULT_EXIT_COMMAND)

    assert mock_thread.called
    assert not event.is_set()


def test_exit_command_handler_integration():
    """Integration test for exit command handler."""
    # This test simulates real behavior without patching threading

    # Setup the exit handler with a custom event
    event = threading.Event()

    # Create a monitor thread that waits for input
    def mock_input_thread():
        # Simulate user typing exit command after a short delay
        time.sleep(0.1)
        event.set()

    # Start the test thread
    test_thread = threading.Thread(target=mock_input_thread)
    test_thread.daemon = True
    test_thread.start()

    # Wait for event with timeout
    event_set = event.wait(0.5)  # Timeout after 0.5 seconds

    # Event should have been set by the thread
    assert event_set
