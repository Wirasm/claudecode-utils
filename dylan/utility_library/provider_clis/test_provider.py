#!/usr/bin/env python3
"""Test the enhanced provider functionality."""

from provider_claude_code import get_provider


def test_provider_basic():
    """Test basic provider functionality."""
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
    test_provider_basic()
