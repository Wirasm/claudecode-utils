#!/usr/bin/env python3
"""Manual test script for the provider - NOT a pytest file.

This file is used for manual testing only and should NOT be run by pytest.
"""

from dylan.utility_library.provider_clis.provider_claude_code import get_provider


def run_provider_test():
    """Run a manual test of provider functionality."""
    provider = get_provider()

    # Test with minimal arguments
    prompt = "Say hello"
    result = provider.generate(prompt)
    print(f"Basic test: {result[:50]}...")

    # Test with output path and allowed tools
    test_prompt = "Create a simple test file"
    result = provider.generate(
        test_prompt, output_path="test_output.txt", allowed_tools=["Write"], output_format="text"
    )
    print(f"Output path test: {result[:50]}...")


if __name__ == "__main__":
    run_provider_test()
