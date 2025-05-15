# GitHub Actions

This directory contains GitHub Action workflows for automating various tasks in the Claude Code Utility repository.

## Available Workflows

### Changelog and Version Bumping

**File:** [changelog-version-bump.yml](./workflows/changelog-version-bump.yml)

This workflow automatically updates the project's CHANGELOG.md file and bumps the version number in pyproject.toml and src/__init__.py based on semantic versioning principles.

#### How it works

1. The workflow triggers on:
   - Pushes to the `main` branch
   - Manual triggers via the GitHub Actions interface

2. The workflow performs the following steps:
   - Analyzes commit history to determine the appropriate version bump (major, minor, or patch)
   - Uses Git tags to track releases and compare changes since the last version
   - Uses Claude Code in headless mode to:
     - Create a CHANGELOG.md file if it doesn't exist
     - Read the current version from pyproject.toml
     - Bump the version number according to the detected release type
     - Fetch commits since the last version tag
     - Categorize commits by type (Features, Bug Fixes, etc.)
     - Add a new changelog section with version, date, and categorized commits
     - Update the version in both pyproject.toml and src/__init__.py
   - Commits changes and creates a version tag

3. Cost and efficiency optimizations:
   - Pre-processes Git data to reduce token usage
   - Only executes when significant changes are detected since the last version tag
   - Restricts Claude's scope to just the necessary tasks and files
   - Uses a focused prompt to minimize token consumption

#### Requirements

- An `ANTHROPIC_API_KEY` secret must be configured in the repository settings.
  - Go to Repository Settings → Secrets and Variables → Actions
  - Add a new repository secret named `ANTHROPIC_API_KEY` with your Anthropic API key

#### Usage

The workflow runs automatically on pushes to main, but you can also trigger it manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select the "Update Changelog and Version" workflow
3. Click "Run workflow"
4. Choose the branch to run on
5. Click "Run workflow"

The workflow will create or update CHANGELOG.md, bump the version in pyproject.toml and src/__init__.py, then commit these changes and create a version tag.