## [0.3.1] - 2025-05-18
- refactor(commit_hooks): reorganize prepare_commit_msg hook into subdirectory for better structure\n- chore: remove unused workflows and commit hook infrastructure\n- chore: remove experimental commit hooks and temporary artifacts\n- chore: bump dependencies and update versions

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added commit hooks concept library with Claude Code integration
  - prepare-commit-msg hook for automatic conventional commit messages
  - pre-push hook for semantic version bumping and changelog updates
- Added automated bug triage concept
- Added full review loop orchestration
- Added PRP (Product Requirement Prompt) flow

### Changed
- Reorganized prepare_commit_msg hook into subdirectory structure
- Updated project to use 0.x.x versioning during development phase

## [0.3.0] - 2025-05-18

### Added
- Commit hooks library for git workflow automation
- Enhanced code review functionality with JSON output
- Standup report generator integration
- CLI commands consolidation under main `claudecode` command

### Changed
- Migrated from 1.x.x to 0.x.x versioning (development phase)
- Improved project structure with concept_library and src separation

## [0.2.0] - 2025-05-13

### Added
- Initial concept library implementation
- Simple review, dev, validator, and PR tools
- Full review loop proof of concept
- Basic CLI structure with Typer

### Changed
- Refactored project structure for better modularity
- Improved documentation and README

## [0.1.0] - 2025-05-10

### Added
- Initial project setup
- Basic utility functions for Claude Code
- Project configuration and dependencies