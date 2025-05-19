# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-05-19

### Added
- New `dylan pr` command for autonomous pull request creation (`90233e4`)
  - Integrates with the main dylan CLI as a new subcommand
  - Complete PR creation module with CLI and runner components
  - Comprehensive prompt generation for autonomous PR workflow
  - Support for automatic branch detection and PR analysis
  - Follows dylan philosophy of minimal wrappers with complete Claude autonomy
- New minimal autonomous pre-push hook implementation that trusts Claude completely
  - Gives Claude complete control over versioning decisions
  - Trusts Claude to format changelog entries appropriately
  - Allows Claude to run optional checks based on changes
  - Zero validation approach with graceful error handling
- Updated commit hooks documentation to reflect new philosophy

### Changed
- Replaced complex pre-push hook with minimal Claude-driven implementation
  - Reduced from 160+ lines to ~120 lines of code
  - Removed hardcoded version bump rules
  - Eliminated complex authentication fallbacks
  - Simplified to trust Claude's analysis completely

## [0.3.2] - 2025-05-19

### Changed
- Converted standup command to Typer sub-app architecture
- Simplified standup command structure for better integration
- Removed unused pretty-print functionality from dylan_review module

### Updated
- Documentation to reflect simplified CLI entry points

## [0.3.1] - 2025-05-18

### Changed
- Renamed CLI from claudecode to dylan
- Renamed package directory from src to dylan
- Consolidated provider modules into shared provider_clis package
- Enhanced codebase linting with comprehensive ruff configuration
- Reorganized prepare_commit_msg hook into subdirectory structure

### Removed
- Unused workflows and commit hook infrastructure
- Experimental commit hooks and temporary artifacts

### Updated
- Documentation with tool requirements and commit hook guidance

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