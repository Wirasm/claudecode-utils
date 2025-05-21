## Using the Interactive Mode (`--interactive` / `-i`)

The `--interactive` (or `-i`) flag transforms the behavior of supported Dylan CLI commands (`pr`, `review`, `release`). Instead of executing a predefined task based on a prompt and then exiting, this flag launches an interactive chat session directly with the underlying AI model (Claude). The command's standard generated prompt (e.g., for PR generation, code review, or release management) is used to provide the initial context for this conversation.

This mode allows for a more dynamic and conversational exchange. You can ask follow-up questions, request clarifications, provide further instructions, guide the AI's focus, or work through complex tasks step-by-step. It's particularly useful when the standard one-shot command execution might not be sufficient or when you want to explore options with AI assistance.

### `dylan pr --interactive`

The interactive mode for `dylan pr` allows for a conversational approach to creating and refining pull request descriptions.

**Example:**
```bash
dylan pr --interactive
```
Or, for a specific branch:
```bash
dylan pr my-feature-branch --target main --interactive
```

**Use Cases:**
*   **Refine PR Description:** After Claude generates an initial PR description based on the commits, you can ask it to rephrase sections, elaborate on certain points, or change the tone.
*   **Discuss Changes:** Ask Claude about specific changes in the commit history and how they might be best presented.
*   **Iterative Content Generation:** Work with Claude to build the PR description section by section.
*   **Related Tasks:** Request Claude to perform related tasks, such as summarizing the technical debt addressed or suggesting areas for future improvement based on the current changes.

### `dylan review --interactive`

For `dylan review`, the interactive mode enables a dynamic code review session where you can delve deeper into the AI's feedback.

**Example:**
```bash
dylan review --interactive
```
Or, to review a specific branch:
```bash
dylan review feature/my-bug-fix --interactive
```

**Use Cases:**
*   **Clarify Review Comments:** If a suggestion from Claude is unclear, you can ask for more details or examples.
*   **Explore Alternatives:** Request alternative solutions or approaches to issues identified by the AI.
*   **Guide Focus:** Direct Claude to pay closer attention to specific files, functions, or aspects of the code (e.g., "Focus on potential security issues in `auth.py`").
*   **Discuss Trade-offs:** Engage in a conversation about the trade-offs of different implementation choices.
*   **Iterative Review:** Work through the review feedback item by item, discussing each point with Claude.

### `dylan release --interactive`

Interactive mode for `dylan release` provides a way to manage the release process conversationally, offering more control and oversight.

**Example:**
```bash
dylan release --bump minor --interactive
```
Or, for a dry run:
```bash
dylan release --bump patch --mode dry-run --interactive
```

**Use Cases:**
*   **Discuss Release Plan:** Before Claude executes steps like version bumping or changelog updates, you can discuss the plan and confirm details.
*   **Step-by-Step Execution:** Ask Claude to perform release tasks one by one, allowing you to verify each step.
*   **Troubleshoot Issues:** If an issue arises (e.g., a problem with version detection or changelog formatting), you can work with Claude interactively to diagnose and attempt to resolve it.
*   **Confirm Actions:** Have Claude confirm critical actions (like tagging or pushing changes) before they are performed, if not already part of its standard interactive flow.
*   **Custom Requests:** Ask for specific checks or information related to the release that might not be part of the standard prompt (e.g., "List all commits since the last tag before you proceed").
