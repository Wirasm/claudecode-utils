name: "Dylan PRP Command"
description: |
  A simple, interactive wrapper around the Product Requirement Prompt (PRP) concept for the Dylan CLI, focusing on guided creation with human-in-the-loop feedback.

## Goal

Create a `dylan prp` command that provides a streamlined interface for creating and running Product Requirement Prompts, emphasizing human-AI collaboration throughout the process.

## Why

- **Accessibility**: Makes the powerful PRP concept accessible via the main Dylan CLI
- **Guidance**: Offers structured guidance for creating effective PRPs through interactive dialogue
- **Context Enhancement**: Improves PRP quality by ensuring proper context gathering with human input
- **Simplicity**: Keeps the implementation minimal while focusing on the core value of human-AI collaboration
- **Workflow Integration**: Integrates PRPs into the existing Dylan CLI ecosystem

## What

The `dylan prp` command will:

- Provide a simple interface for creating and running PRPs
- Focus on interactive dialogue for PRP creation
- Include clear checkpoints for human feedback
- Support both interactive and headless modes
- Guide users through the structured PRP creation process
- Execute PRPs with appropriate guidance

## Endpoints/APIs to Implement

N/A - This feature implements a CLI command, not an API endpoint.

## Current Directory Structure

```
dylan/
├── cli.py                                # Main CLI entry point
├── utility_library/
│   ├── dylan_review/                     # Review functionality
│   │   ├── __init__.py
│   │   ├── dylan_review_cli.py           # Review CLI interface
│   │   └── dylan_review_runner.py        # Review core functionality
│   ├── dylan_pr/                         # PR functionality
│   │   ├── __init__.py
│   │   ├── dylan_pr_cli.py               # PR CLI interface
│   │   └── dylan_pr_runner.py            # PR core functionality
│   ├── dylan_release/                    # Release functionality
│   │   ├── __init__.py
│   │   ├── dylan_release_cli.py          # Release CLI interface
│   │   └── dylan_release_runner.py       # Release core functionality
│   ├── provider_clis/                    # Provider interfaces
│   │   ├── __init__.py
│   │   ├── provider_claude_code.py       # Claude Code provider
│   │   └── shared/
│   │       ├── __init__.py
│   │       └── subprocess_utils.py       # Subprocess utilities
│   └── shared/                           # Shared utilities and UI components
│       ├── __init__.py
│       ├── config.py                     # Configuration
│       ├── error_handling.py             # Error handling
│       ├── exit_command.py               # Exit command handling
│       ├── progress.py                   # Progress reporting
│       └── ui_theme.py                   # UI theme components
```

## Proposed Directory Structure

```
dylan/
├── cli.py                                # Updated to add prp command
├── utility_library/
│   ├── dylan_prp/                        # New PRP functionality
│   │   ├── __init__.py
│   │   ├── dylan_prp_cli.py              # PRP CLI interface
│   │   ├── dylan_prp_runner.py           # PRP core functionality
│   │   └── templates/                    # PRP templates
│   │       └── meta_header.py            # META_HEADER for PRP execution
│   └── ... (other existing directories)
```

## Files to Reference

- `/Users/rasmus/Projects/claudecode-utility/concept_library/cc_PRP_flow/scripts/cc_runner_simple.py` (read_only) Reference implementation of the PRP runner
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/dylan_review/dylan_review_cli.py` (read_only) Pattern for CLI interface implementation
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/dylan_release/dylan_release_cli.py` (read_only) Example of a Typer.Typer implementation
- `/Users/rasmus/Projects/claudecode-utility/dylan/utility_library/provider_clis/provider_claude_code.py` (read_only) Provider interface for Claude Code
- `/Users/rasmus/Projects/claudecode-utility/dylan/cli.py` (read_only) Main CLI entry point to be updated
- `/Users/rasmus/Projects/claudecode-utility/.claude/commands/create-prp.md` (read_only) Current implementation of PRP creation via slash command
- `https://typer.tiangolo.com/tutorial/commands/callback/` (read_only) Documentation for Typer callback functions

## Files to Implement (concept)

### Core CLI Module

1. `dylan/utility_library/dylan_prp/__init__.py` - Empty init file for the package

```python
"""Dylan PRP module for creating and running Product Requirement Prompts."""
```

2. `dylan/utility_library/dylan_prp/dylan_prp_cli.py` - CLI interface for the PRP command

```python
#!/usr/bin/env python3
"""CLI interface for the Product Requirement Prompt (PRP) tool using Typer."""

import os
import typer
from pathlib import Path
from rich.console import Console

from ..shared.ui_theme import (
    create_box_header,
    create_header,
    format_boolean_option,
)
from .dylan_prp_runner import (
    create_prp,
    run_prp,
)

console = Console()
prp_app = typer.Typer()


@prp_app.callback(invoke_without_command=True)
def prp(
    ctx: typer.Context,
    name: str = typer.Argument(
        None,
        help="Name for the new PRP or existing PRP to run",
    ),
    create: bool = typer.Option(
        False,
        "--create",
        "-c", 
        help="Create a new PRP",
    ),
    run: bool = typer.Option(
        False,
        "--run",
        "-r",
        help="Run an existing PRP",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--headless",
        help="Run in interactive mode with user feedback",
        show_default=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Print debug information (including prompts)",
        show_default=True,
    ),
):
    """Work with Product Requirement Prompts (PRPs).
    
    Creates or runs PRPs with human-in-the-loop feedback.
    
    Examples:
        # Create a new PRP
        dylan prp --create authentication-system
        
        # Run an existing PRP
        dylan prp --run authentication-system
        
        # Run an existing PRP in headless mode
        dylan prp --run authentication-system --no-interactive
    """
    # Skip if subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return
        
    # Show header with flair
    console.print()
    console.print(create_header("Dylan", "PRP"))
    console.print()
    
    # Validate that a name was provided
    if not name:
        console.print("Error: PRP name is required", style="bold red")
        console.print("Usage: dylan prp --create <name> or dylan prp --run <name>")
        raise typer.Exit(1)
    
    # Show configuration
    action = "Create" if create else "Run" if run else "Unknown"
    
    console.print(create_box_header("PRP Configuration", {
        "Action": action,
        "Name": name,
        "Mode": "Interactive" if interactive else "Headless",
        "Debug": format_boolean_option(debug, "✓ Enabled", "✗ Disabled"),
        "Exit": "Ctrl+C to interrupt or /done to exit interactive mode"
    }))
    console.print()
    
    # Dispatch to the appropriate action
    if create:
        # Get description
        description = typer.prompt("Enter a brief description of the feature")
        create_prp(name, description, interactive=interactive, debug=debug)
    elif run:
        run_prp(name, interactive=interactive, debug=debug)
    else:
        # Show help if no action specified
        console.print("Please specify an action: --create or --run", style="yellow")
        raise typer.Exit(1)


# For backwards compatibility and standalone usage
def main():
    """Entry point for standalone CLI usage."""
    prp_app()
```

3. `dylan/utility_library/dylan_prp/dylan_prp_runner.py` - Core implementation of the PRP command

```python
#!/usr/bin/env python3
"""Core functionality for the Product Requirement Prompt (PRP) tool.

This module provides the functionality to create and run PRPs with human-in-the-loop
feedback.

Python API usage:
    from dylan.utility_library.dylan_prp.dylan_prp_runner import create_prp, run_prp

    # Create a new PRP
    create_prp("authentication-system", "JWT authentication system")
    
    # Run an existing PRP
    run_prp("authentication-system")
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from ..provider_clis.provider_claude_code import get_provider
from ..shared.config import (
    CLAUDE_CODE_NPM_PACKAGE,
    CLAUDE_CODE_REPO_URL,
    GITHUB_ISSUES_URL,
)
from ..shared.progress import create_dylan_progress, create_task_with_dylan
from ..shared.ui_theme import ARROW, COLORS, SPARK, create_status
from .templates.meta_header import META_HEADER

console = Console()


def create_prp(
    name: str,
    description: str,
    interactive: bool = True,
    debug: bool = False,
) -> None:
    """Create a new PRP with guided user input.
    
    Args:
        name: The name for the PRP
        description: A brief description of the feature
        interactive: Whether to run in interactive mode
        debug: Whether to print debug information
    """
    # Ensure PRPs directory exists
    os.makedirs("PRPs", exist_ok=True)
    
    # Check if PRP already exists
    prp_path = Path(f"PRPs/{name}.md")
    if prp_path.exists():
        if not typer.confirm(f"PRP '{name}' already exists. Overwrite?", default=False):
            console.print("Operation cancelled.")
            return
    
    # Build the initial prompt
    prompt = f"""
You will help the user create a comprehensive Product Requirement Prompt (PRP) for: {name}

Description: {description}

Please guide me through creating this PRP by following these steps:

1. Ask me questions about the feature to understand the scope and requirements
2. Suggest relevant files and directories to look at for context
3. Identify key patterns and implementation approaches
4. Propose validation criteria for the implementation
5. Draft the PRP structure based on our discussion

After each step, ask for my feedback and adjust based on my responses.

When the PRP is complete and approved by the user, save it to PRPs/{name}.md.
The PRP should follow the structure from concept_library/cc_PRP_flow/PRPs/base_template_v1.md.

Remember: A PRP is PRD + curated codebase intelligence + agent/runbook—the minimum viable packet an AI needs to ship production-ready code on the first pass.
"""

    # Print prompt for debugging
    if debug:
        console.print("\n===== DEBUG: PROMPT =====\n")
        console.print(prompt)
        console.print("\n========================\n")

    # Get provider
    provider = get_provider()
    
    with create_dylan_progress(console=console) as progress:
        # Start the task
        task = create_task_with_dylan(progress, "Starting PRP creation dialogue...")
        
        try:
            # Run Claude in interactive mode
            result = provider.generate(
                prompt,
                stream=interactive,
                exit_command="/done" if interactive else None,
            )
            
            # Update task to complete
            progress.update(task, completed=True)
            
            # Success message with flair
            console.print()
            console.print(create_status("PRP creation completed!", "success"))
            console.print(f"[{COLORS['muted']}]PRP saved to {prp_path}[/]")
            console.print()
            
            # Show next steps
            console.print(f"[{COLORS['primary']}]{ARROW}[/] [bold]Next Steps[/bold] [{COLORS['accent']}]{SPARK}[/]")
            console.print(f"[{COLORS['muted']}]To run this PRP, use:[/]")
            console.print(f"[{COLORS['primary']}]dylan prp --run {name}[/]")
            console.print()
            
        except Exception as e:
            # Handle errors
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(f"Error during PRP creation: {e}", "error"))
            sys.exit(1)


def run_prp(
    name: str,
    interactive: bool = True,
    debug: bool = False,
) -> None:
    """Run an existing PRP.
    
    Args:
        name: The name of the PRP to run
        interactive: Whether to run in interactive mode
        debug: Whether to print debug information
    """
    # Check if PRP exists
    prp_path = Path(f"PRPs/{name}.md")
    if not prp_path.exists():
        console.print(f"Error: PRP not found: {prp_path}", style="bold red")
        sys.exit(1)
    
    # Read the PRP content
    prp_content = prp_path.read_text()
    
    # Add meta header for guidance
    prompt = META_HEADER + prp_content
    
    # Print prompt for debugging
    if debug:
        console.print("\n===== DEBUG: PROMPT =====\n")
        console.print(prompt)
        console.print("\n========================\n")
    
    # Set allowed tools
    allowed_tools = [
        "Edit", "Bash", "Write", "MultiEdit", "NotebookEdit", "WebFetch",
        "Agent", "LS", "Grep", "Read", "NotebookRead", "TodoRead", 
        "TodoWrite", "WebSearch"
    ]
    
    # Get provider
    provider = get_provider()
    
    with create_dylan_progress(console=console) as progress:
        # Start the task
        task = create_task_with_dylan(progress, "Running PRP implementation...")
        
        try:
            # Run Claude with the PRP
            result = provider.generate(
                prompt,
                allowed_tools=allowed_tools,
                stream=interactive,
                exit_command="/done" if interactive else None,
            )
            
            # Update task to complete
            progress.update(task, completed=True)
            
            # Success message with flair
            console.print()
            console.print(create_status("PRP execution completed!", "success"))
            console.print()
            
        except Exception as e:
            # Handle errors
            progress.update(task, completed=True)
            console.print()
            console.print(create_status(f"Error during PRP execution: {e}", "error"))
            sys.exit(1)
```

4. `dylan/utility_library/dylan_prp/templates/meta_header.py` - META_HEADER for PRP execution

```python
"""META_HEADER for PRP execution."""

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

## Human-in-the-Loop Checkpoints
- After completing your plan, ask for feedback before implementation
- After implementing core functionality, check with the user
- Present difficult design decisions to the user for guidance
- When encountering ambiguity, ask for clarification rather than guessing

## Testing Phase
- Test each component thoroughly as you build it.
- Use the provided validation gates to verify your implementation.
- Verify that all requirements have been satisfied.
- Run the project tests when finished.

Now proceed with the PRP:

"""
```

### CLI Entry Point Update

5. `dylan/cli.py` - Updated to add the prp command

```python
"""Root Typer application that dispatches to vertical slices.

Includes 'standup', 'review', 'dev', 'pr', 'prp', and 'release' commands.
"""

import typer
from rich.console import Console
from rich.table import Table

from .utility_library.dylan_pr.dylan_pr_cli import pr
from .utility_library.dylan_prp.dylan_prp_cli import prp_app
from .utility_library.dylan_release.dylan_release_cli import release_app
from .utility_library.dylan_review.dylan_review_cli import review
from .utility_library.dylan_standup.standup_typer import standup_app
from .utility_library.shared.ui_theme import ARROW, COLORS, SPARK

console = Console()

app = typer.Typer(
    help=f"[{COLORS['primary']}]Dylan[/] [{COLORS['accent']}]{SPARK}[/] AI-powered development utilities",
    add_completion=False,
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)
app.add_typer(standup_app, name="standup", help="Generate daily standup reports from git activity")
app.add_typer(release_app, name="release", help="Create and manage project releases")
app.add_typer(prp_app, name="prp", help="Create and run Product Requirement Prompts")
app.command(name="review", help="Run AI-powered code reviews on git branches")(review)
app.command(name="pr", help="Create pull requests with AI-generated descriptions")(pr)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    """Show welcome message when no command is provided."""
    if ctx.invoked_subcommand is None:
        # Welcome header with flair
        console.print(f"\n[{COLORS['primary']}]{ARROW}[/] [bold]Dylan[/bold] [{COLORS['accent']}]{SPARK}[/]")
        console.print("[dim]AI-powered development utilities using Claude Code[/dim]\n")

        # Commands table with custom styling
        table = Table(
            show_header=True,
            header_style=f"bold {COLORS['primary']}",
            border_style=COLORS['muted'],
            title_style=f"bold {COLORS['accent']}",
            box=None,
        )

        table.add_column("Command", style=COLORS['secondary'], width=12)
        table.add_column("Description", style=COLORS['primary'])
        table.add_column("Example", style="dim")

        table.add_row(
            "standup",
            "Generate daily standup reports",
            "dylan standup --since yesterday"
        )
        table.add_row(
            "review",
            "Run code reviews on branches",
            "dylan review feature-branch"
        )
        table.add_row(
            "prp",
            "Work with Product Requirement Prompts",
            "dylan prp --create feature-name"
        )
        table.add_row(
            "pr",
            "Create pull requests",
            "dylan pr --target develop"
        )
        table.add_row(
            "release",
            "Manage project releases",
            "dylan release --minor --tag"
        )

        console.print(table)
        help_text = f"\n[{COLORS['muted']}]Use[/] [{COLORS['primary']}]dylan <command> --help[/]"
        console.print(f"{help_text} [{COLORS['muted']}]for detailed options[/]")
        console.print("[dim]Example: dylan review --help[/dim]\n")
```

## Implementation Notes

### Human-in-the-Loop Interaction Design

- **Structured Dialogue**: The PRP creation process is structured as a dialogue between the user and Claude, with clear phases:
  1. **Initial Scoping**: Understanding feature requirements and goals
  2. **Context Gathering**: Identifying relevant codebase components
  3. **Implementation Planning**: Proposing and refining approach
  4. **Validation Definition**: Setting criteria for successful implementation
  5. **PRP Drafting**: Creating and refining the PRP document
  6. **Final Review**: Confirming and saving the completed PRP

- **Feedback Integration**: The implementation explicitly builds in checkpoints for user feedback:
  - After each major step in the PRP creation process
  - When proposing implementation approaches
  - When facing design decisions or ambiguities
  - Before finalizing the PRP

- **Interactive Mode**: The command prioritizes interactive mode by default to maximize human-in-the-loop feedback, but supports headless operation when needed.

### CLI Integration

- **Simplicity First**: The implementation keeps the CLI interface minimal and focused on the core functionality
- **Consistent Patterns**: Follows existing Dylan CLI patterns for UI and command structure
- **Typer App**: Uses Typer.Typer for command structuring, similar to other Dylan commands
- **Provider Interface**: Leverages the existing provider interface for Claude Code interaction

### PRP Structure

- **Template Following**: Ensures generated PRPs follow the established template structure
- **Context Gathering**: Emphasizes comprehensive context gathering with user validation
- **Validation Gates**: Includes clear validation criteria for implementation
- **META_HEADER**: Uses a guidance header to set expectations for PRP execution

### Error Handling & User Experience

- **Progress Feedback**: Uses progress indicators for long-running operations
- **Error Messages**: Provides clear error messages with appropriate styling
- **Next Steps**: Guides users on what to do after PRP creation
- **Exit Controls**: Supports standard interruption patterns and `/done` exit command

## Validation Gates

1. **Functionality Requirements**
   - The command must be accessible via `dylan prp --create <name>` and `dylan prp --run <name>`
   - The command must support interactive PRP creation with guided user input
   - The command must execute PRPs with appropriate guidance
   - The command must handle errors gracefully and provide clear feedback

2. **Integration Requirements**
   - The command must integrate with the existing Dylan CLI
   - The command must follow the same UI patterns as other commands
   - The command must use the provider interface for Claude Code

3. **User Experience Requirements**
   - The command must provide clear guidance during PRP creation
   - The command must include explicit checkpoints for user feedback
   - The command must support both interactive and headless modes
   - The command must provide clear next steps after operations

4. **Output Requirements**
   - Created PRPs must follow the established template structure
   - PRPs must be saved to the appropriate location
   - Execution must respect the guidance in the META_HEADER

## Implementation Checkpoints/Testing

### 1. Basic Command Structure

- Implement the CLI interface in `dylan_prp_cli.py`
- Test the interface by running `python -m dylan.utility_library.dylan_prp.dylan_prp_cli --help`
- Ensure all options are correctly defined and help text is appropriate
- Verify the command shows up in the main CLI help

Command to verify:
```
dylan --help
```

### 2. PRP Creation Functionality

- Implement the PRP creation functionality in `dylan_prp_runner.py`
- Test creation of a simple PRP
- Verify the interactive dialogue flow works as expected
- Verify the PRP is saved to the correct location with the appropriate structure

Command to verify:
```
dylan prp --create test-prp
```

### 3. PRP Execution Functionality

- Implement the PRP execution functionality in `dylan_prp_runner.py`
- Test execution of a created PRP
- Verify the META_HEADER is properly applied
- Verify the human-in-the-loop checkpoints work as expected

Command to verify:
```
dylan prp --run test-prp
```

## Other Considerations

### Extensibility

- The implementation can be extended in the future to support advanced features like:
  - PRP templates for common features
  - PRP categorization and organization
  - Advanced PRP editing capabilities
  - PRP sharing and collaboration

### Dependencies

- Typer for CLI interface
- Rich for UI components
- Claude Code for PRP creation and execution

### Security Considerations

- PRP execution should respect the tool permissions of Claude Code
- PRP files should be treated as code and reviewed appropriately

### Performance

- Interactive mode naturally involves delay for human input
- In headless mode, execution time depends on the complexity of the PRP

---

## User Example Interaction

Here's a concrete example of how a user might interact with the `dylan prp` command:

```
$ dylan prp --create user-authentication

Dylan PRP Creation

Enter a brief description of the feature: JWT-based user authentication system with login, registration, and role-based access control

Claude: I'll help you create a PRP for a JWT-based user authentication system. Let me ask a few questions to better understand your requirements:

1. What user roles do you need to support? (e.g., admin, regular user)
2. Do you need to integrate with any existing user database?
3. What authentication flows are required? (login, registration, password reset, etc.)
4. Are there any specific security requirements you need to follow?

User: We need admin and regular user roles. This is a new system with its own database. We need login, registration, and password reset flows. We should follow OWASP security guidelines.

Claude: Thanks for that information. I'd like to look at some relevant parts of your codebase to understand the existing patterns. Would these be the right places to check?

1. Any existing user or role models
2. Your database connection setup
3. Current API endpoint structure
4. Frontend authentication components (if applicable)

Which of these should I examine? Are there specific files I should look at?

User: Yes, please look at models/user.py for our user model pattern, db/connection.py for database setup, and api/endpoints/ for our API structure.

Claude: [Examines the codebase]

Based on my exploration, I see you're using SQLAlchemy for database models, FastAPI for endpoints, and Pydantic for validation. I also see your API endpoints follow a specific pattern.

For implementing JWT authentication, I propose:
1. Extending the User model with password hashing using Argon2
2. Creating auth endpoints following your established pattern
3. Implementing JWT token generation and validation middleware
4. Adding role-based access control decorators

Does this approach align with your vision?

User: Yes, but please make sure we separate the authentication logic into its own module.

Claude: [Dialogue continues with more detailed discussions on implementation, security, and validation]

[Eventually presents a draft PRP and refines based on feedback]

Claude: Here's the final PRP for your JWT-based user authentication system. I've included all the relevant context, implementation details, and validation gates. The PRP has been saved to PRPs/user-authentication.md.

To implement this feature, you can now run:
dylan prp --run user-authentication
```

This example demonstrates the human-in-the-loop collaborative process that makes PRPs effective, with clear checkpoints for user feedback throughout the creation process.