#!/usr/bin/env -S uv run --script
"""Run an AI coding agent against a PRP.

KISS version - no repo-specific assumptions.

Typical usage:
    uv run python concept_library/cc_PRP_flow/scripts/cc_runner_simple.py --prp test --interactive

Arguments:
    --prp-path       Path to a PRP markdown file (overrides --prp)
    --prp            Feature key; resolves to PRPs/{feature}.md
    --model          CLI executable for the LLM (default: "claude") Only Claude Code is supported for now
    --interactive    Pass through to run the model in chat mode; otherwise headless.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root

# Meta header to be included in the prompt
# The Meta header is a powerful meta prompt that you can use to guide the model
# Before and after the execution of the PRP
# you can add stuff like git commands to run, or other meta instructions
# examples:
# - git add .
# - git commit -m "Initial commit"
# - git push
# git commit hooks

META_HEADER = """Ingest and understand the Product Requirement Prompt (PRP) below in detail.

    # WORKFLOW GUIDANCE:

    ## Planning Phase
    - Think hard before you code. Create a comprehensive plan addressing all requirements.
    - Break down complex tasks into smaller, manageable steps.
    - Use the TodoWrite tool to create and track your implementation plan.
    - Identify implementation patterns from existing code to follow.

    ## Implementation Phase
    - Follow code conventions and patterns found in existing files.
    - Implement one component at a time and verify it works correctly.
    - Write clear, maintainable code with appropriate comments.
    - Consider error handling, edge cases, and potential security issues.
    - Use type hints to ensure type safety.

    ## Testing Phase
    - Test each component thoroughly as you build it.
    - Use the provided validation gates to verify your implementation.
    - Verify that all requirements have been satisfied.
    - Run the project tests when finished and output "DONE" when they pass.

    ## Example Implementation Approach:
    1. Analyze the PRP requirements in detail
    2. Search for and understand existing patterns in the codebase
    3. Create a step-by-step implementation plan with TodoWrite
    4. Implement core functionality first, then additional features
    5. Test and validate each component
    6. Ensure all validation gates pass

    ***When you are finished, move the completed PRP to the concept_library/cc_PRP_flow/PRPs/completed folder***
    """


def build_prompt(prp_path: Path) -> str:
    return META_HEADER + prp_path.read_text()


def run_model(prompt: str, model: str = "claude", interactive: bool = False) -> None:
    if interactive:
        # Chat mode: feed prompt via STDIN, no -p flag so the user can continue the session.
        cmd = [
            model,
            "--allowedTools",
            "Edit,Bash,Write,MultiEdit,NotebookEdit,WebFetch,Agent,LS,Grep,Read,NotebookRead,TodoRead,TodoWrite,WebSearch",
        ]
        subprocess.run(cmd, input=prompt.encode(), check=True)
    else:
        # Headless: pass prompt via -p and auto‑print a single response.
        cmd = [
            model,
            "-p",
            prompt,
            "--allowedTools",
            "Edit,Bash,Write,MultiEdit,NotebookEdit,WebFetch,Agent,LS,Grep,Read,NotebookRead,TodoRead,TodoWrite,WebSearch",
            "--print",
        ]
        subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a PRP with an LLM agent.")
    parser.add_argument("--prp-path", help="Relative path to PRP file eg: PRPs/feature.md")
    parser.add_argument("--prp", help="The file name of the PRP without the .md extension eg: feature")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive chat session")
    parser.add_argument(
        "--model", default="claude", help="Model CLI executable name"
    )  # can be replaced with other CLI based coders, you would just have to construct the command differently
    args = parser.parse_args()

    if not args.prp_path and not args.prp:
        sys.exit("Must supply --prp or --prp-path")

    prp_path = Path(args.prp_path) if args.prp_path else ROOT / f"PRPs/{args.prp}.md"
    if not prp_path.exists():
        sys.exit(f"PRP not found: {prp_path}")

    os.chdir(ROOT)  # ensure relative paths match PRP expectations
    prompt = build_prompt(prp_path)
    run_model(prompt, model=args.model, interactive=args.interactive)


if __name__ == "__main__":
    main()
