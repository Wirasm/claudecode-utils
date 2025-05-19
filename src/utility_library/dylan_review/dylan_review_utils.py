#!/usr/bin/env python3
"""Utility functions for the cc_review module."""

import json


def pretty_print_json_file(file_path: str, output_path: str | None = None) -> None:
    """Pretty print a JSON file, handling common escape issues.

    Args:
        file_path: Path to the JSON file to pretty print
        output_path: Optional path to save the pretty-printed JSON
    """
    try:
        with open(file_path) as f:
            content = f.read()

        # Fix common escape issues
        content = content.replace(r"\!", "!")

        # Parse JSON
        data = json.loads(content)

        # Pretty print
        pretty_json = json.dumps(data, indent=2)

        if output_path:
            with open(output_path, "w") as f:
                f.write(pretty_json)
            print(f"Pretty-printed JSON saved to: {output_path}")
        else:
            print(pretty_json)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error: {e}")
