"""Subprocess utilities for process management.

This module provides utilities for subprocess management, handling interruptions,
and graceful termination of processes.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator


def is_windows() -> bool:
    """Check if the current platform is Windows.

    Returns:
        bool: True if running on Windows, False otherwise
    """
    return os.name == 'nt'


def get_interrupt_signal():
    """Get the appropriate interrupt signal for the current platform.

    Returns:
        The appropriate interrupt signal for the current platform
    """
    if is_windows():
        return signal.CTRL_C_EVENT
    return signal.SIGINT


def terminate_process(
    proc: subprocess.Popen,
    interrupt_timeout: int = 5,
    terminate_timeout: int = 2,
) -> None:
    """Terminate a process gracefully with cascading signals.

    Args:
        proc: The subprocess.Popen process object
        interrupt_timeout: Timeout in seconds to wait after SIGINT
        terminate_timeout: Timeout in seconds to wait after SIGTERM

    This function follows a cascading approach to termination:
    1. Send SIGINT (or equivalent) and wait up to interrupt_timeout seconds
    2. If still running, send SIGTERM and wait up to terminate_timeout seconds
    3. If still running, send SIGKILL (no wait/guaranteed to terminate)
    """
    # First try SIGINT (like Ctrl+C)
    interrupt_signal = get_interrupt_signal()
    proc.send_signal(interrupt_signal)

    # Give it a few seconds to clean up
    try:
        proc.wait(timeout=interrupt_timeout)
        return  # Process exited after SIGINT
    except subprocess.TimeoutExpired:
        print("Graceful shutdown timed out, terminating process...", file=sys.stderr)
        proc.terminate()  # SIGTERM
        try:
            proc.wait(timeout=terminate_timeout)
            return  # Process exited after SIGTERM
        except subprocess.TimeoutExpired:
            print("Termination timed out, killing process...", file=sys.stderr)
            proc.kill()  # SIGKILL (force quit)


def setup_exit_command_listener(
    exit_command: str,
    on_exit: Callable,
    check_interval: float = 0.1,
) -> threading.Thread:
    """Set up a listener thread for an exit command.

    Args:
        exit_command: The command to listen for
        on_exit: Callback function to call when exit command is detected
        check_interval: How often to check for the exit command (in seconds)

    Returns:
        The created daemon thread (already started)
    """
    exit_triggered = threading.Event()

    def input_listener():
        """Listen for user input in a separate thread."""
        while not exit_triggered.is_set():
            try:
                user_input = input()
                if user_input.strip() == exit_command:
                    print(f"\nExit command '{exit_command}' detected. Shutting down...", file=sys.stderr)
                    exit_triggered.set()
                    on_exit()
            except (EOFError, KeyboardInterrupt):
                break
            except Exception:  # noqa: S110
                # Ignore other errors in the input thread - don't crash the daemon thread
                # This is intentionally suppressed as the input thread is non-critical
                pass
            time.sleep(check_interval)

    # Start input listener thread
    input_thread = threading.Thread(target=input_listener, daemon=True)
    input_thread.start()
    return input_thread


def stream_process_output(
    proc: subprocess.Popen,
    timeout: int | None = None,
    exit_command: str | None = None,
) -> Iterator[str]:
    """Stream output from a subprocess line by line with optional timeout.

    Args:
        proc: The subprocess.Popen process object
        timeout: Optional timeout in seconds for the entire process
        exit_command: Custom command to listen for to exit gracefully

    Yields:
        Lines of output from the process

    Raises:
        TimeoutError: If the process exceeds the timeout
        subprocess.CalledProcessError: If the process exits with a non-zero code
        KeyboardInterrupt: If the process is interrupted by user
    """
    start_time = time.time()
    exit_triggered = threading.Event()

    try:
        # Check for user input if exit_command is specified
        if exit_command:
            def on_exit_command():
                exit_triggered.set()
                proc.send_signal(get_interrupt_signal())

            setup_exit_command_listener(exit_command, on_exit_command)

        # Main output streaming loop
        for line in proc.stdout:
            if timeout and (time.time() - start_time > timeout):
                raise TimeoutError("Process exceeded timeout")

            # Check if exit was triggered
            if exit_triggered.is_set():
                break

            yield line.strip()

    except (KeyboardInterrupt, SystemExit) as e:
        print("\nProcess interrupted by user. Attempting graceful shutdown...", file=sys.stderr)
        terminate_process(proc)
        raise KeyboardInterrupt() from e


def run_with_timeout(cmd: list[str], timeout: int | None = None) -> tuple[int, str, str]:
    """Run a command with timeout, handling interruptions gracefully.

    Args:
        cmd: Command to run as a list of strings
        timeout: Timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)

    Raises:
        TimeoutError: If the process exceeds the timeout
        KeyboardInterrupt: If the process is interrupted by user
    """
    try:
        # Use Popen to get more control over the process
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as proc:
            stdout_data = []
            start_time = time.time()

            # Read stdout while process is running
            for line in proc.stdout:
                stdout_data.append(line)
                if timeout and (time.time() - start_time > timeout):
                    # Process exceeded timeout
                    terminate_process(proc)
                    raise TimeoutError(f"Process timed out after {timeout} seconds")

            # Wait for the process to complete and check return code
            return_code = proc.wait()
            stderr_data = proc.stderr.read()

            return return_code, "".join(stdout_data), stderr_data

    except (KeyboardInterrupt, SystemExit) as e:
        # Handle keyboard interruption
        print("\nProcess interrupted. Shutting down...", file=sys.stderr)
        if 'proc' in locals():
            terminate_process(proc)
        raise KeyboardInterrupt() from e
