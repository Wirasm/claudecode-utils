"""Configuration constants for Dylan CLI."""

# Repository information
GITHUB_REPOSITORY_URL = "https://github.com/Wirasm/dylan"
GITHUB_ISSUES_URL = f"{GITHUB_REPOSITORY_URL}/issues"

# Claude Code installation and references
CLAUDE_CODE_NPM_PACKAGE = "@anthropic-ai/claude-code"
CLAUDE_CODE_REPO_URL = "https://github.com/anthropics/claude-code"
CLAUDE_CODE_ISSUES_URL = f"{CLAUDE_CODE_REPO_URL}/issues"

# Command and error messages
CLAUDE_CODE_INSTALL_CMD = f"npm install -g {CLAUDE_CODE_NPM_PACKAGE}"
CLAUDE_CODE_NOT_FOUND_MSG = (
    "🔴 Claude Code not found!\n"
    f"Please install Claude Code first:\n"
    f"  {CLAUDE_CODE_INSTALL_CMD}\n"
    f"  \n"
    f"For more info: {CLAUDE_CODE_REPO_URL}"
)
