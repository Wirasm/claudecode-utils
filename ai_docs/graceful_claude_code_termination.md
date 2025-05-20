# Graceful Claude Code Termination

This document provides examples and guidance on how to gracefully terminate Claude Code processes using the improved provider implementation in Dylan.

## Overview

The `ClaudeProvider` class in Dylan has been updated to provide graceful termination for Claude Code processes, which solves the issue of interrupted processes continuing to run in the background. The implementation follows best practices for subprocess management:

1. Uses `subprocess.Popen` instead of `subprocess.run` for better process control
2. Implements proper signal handling (SIGINT → SIGTERM → SIGKILL)
3. Supports custom exit commands
4. Provides real-time output streaming
5. Handles timeouts and interruptions gracefully

## Example Usage

### Basic Usage

```python
from dylan.utility_library.provider_clis.provider_claude_code import get_provider

# Get the Claude Code provider
provider = get_provider()

# Generate content with graceful termination handling
try:
    result = provider.generate(
        "Write a short story about a robot learning to garden",
        timeout=60,  # 60 second timeout
    )
    print(result)
except KeyboardInterrupt:
    print("Process was interrupted by user")
```

### Streaming Output

```python
from dylan.utility_library.provider_clis.provider_claude_code import get_provider

provider = get_provider()

try:
    # Stream the output in real-time (printed to console)
    result = provider.generate(
        "Analyze the following code and suggest improvements...",
        stream=True,  # Enable streaming output
        timeout=300,  # 5 minute timeout
    )
except KeyboardInterrupt:
    print("Process was interrupted by user")
```

### Custom Exit Command

```python
from dylan.utility_library.provider_clis.provider_claude_code import get_provider

provider = get_provider()

try:
    # Use a custom exit command ("/exit") to gracefully terminate
    result = provider.generate(
        "Generate a comprehensive report on...",
        stream=True,
        exit_command="/exit",  # Type /exit to terminate gracefully
    )
except KeyboardInterrupt:
    print("Process was interrupted by user")
```

## How It Works

### Interruption Flow

When a process is interrupted (either via KeyboardInterrupt or exit command):

1. **SIGINT**: First, SIGINT is sent to the Claude Code process, which the Claude CLI interprets as a user cancellation
2. **Waiting Period**: The code waits for up to 5 seconds for the process to exit cleanly
3. **SIGTERM**: If the process hasn't exited, SIGTERM is sent for a more forceful termination
4. **Final Kill**: If the process still hasn't exited after 2 more seconds, SIGKILL is used as a last resort

### Signal Handling

Claude Code's CLI has special handling for SIGINT (Ctrl+C) that allows it to cleanly cancel the current operation. The implementation takes advantage of this behavior by sending SIGINT as the first termination signal, giving Claude a chance to clean up properly.

### Exit Command Mechanism

The exit command feature uses a separate thread to listen for user input. When the specified command is entered:

1. An event is triggered to notify the main thread
2. SIGINT is sent to the Claude process
3. Output streaming is stopped
4. Process termination follows the same flow as a KeyboardInterrupt

## Best Practices

1. **Always use a timeout**: Set a reasonable timeout to prevent runaway processes
2. **Use with context managers**: The implementation uses a `with` statement to ensure proper process cleanup
3. **Handle KeyboardInterrupt**: Wrap your code in try/except to handle interruptions gracefully
4. **Stream for interactive use**: Use `stream=True` for interactive applications
5. **Choose intuitive exit commands**: If using custom exit commands, choose intuitive ones like `/exit`, `/quit`, or `q`

## Cross-Platform Considerations

The implementation works on both Unix/Linux/macOS and Windows, with appropriate handling of signals.

On Windows systems, the code may use `CTRL_BREAK_EVENT` instead of SIGINT when available.

## Integration with CLI Tools

When integrating this provider with CLI tools, be sure to:

1. Properly propagate KeyboardInterrupt exceptions
2. Provide clear user feedback during termination
3. Configure stream and exit_command parameters based on the CLI's interactive nature