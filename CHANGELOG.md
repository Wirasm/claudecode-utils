# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.8] - 2025-05-20

### Added
- Branch management command scripts for git operations

### Fixed
- Improved message clarity in review CLI display
- Enhanced mode display in release CLI

### Changed
- Updated commit message template to favor bullet lists
- Simplified command options and standardized interfaces

## [0.6.7] - 2025-05-20

### Changed
- Enhanced release process with improved changelog generation
- Improved prompt consistency and file handling

## [0.6.6] - 2025-05-20

### Changed
- Bump patch version for new release

## [0.6.5] - 2025-05-20

### Changed
- Bump patch version for new release

## [0.6.4] - 2025-05-20

### Changed
- Project renamed to "dylan" throughout the codebase
- Updated branching strategy documentation
- Improved documentation and README files

### Added
- Added PRP-001 for prompt consistency
- Updated CLI README and component READMEs

### Updated
- Updated Ruff dependency from 0.11.9 to 0.11.10

## [0.6.3] - 2025-05-20

### Added
- Enhanced CLI interfaces with improved UI components
  - Added welcome message and command table to main CLI
  - Improved help text and visual elements across all CLIs
  - Added progress bars and rich console output to all runners
- New shared UI components in utility_library/shared
  - Added UI theme configuration
  - Added progress bar utilities
  - Added error handling improvements
## [0.6.1] - 2025-05-19

### Changed
- Improved report file handling and changelog integration for dylan utility library
  - Branch-aware report naming with sanitized branch names (replace / with -)
  - Enhanced changelog support in PR generation
  - Added PR report extraction capabilities to release process
  
### Added
- Updated CLI and utility documentation with branching strategy details
  - Comprehensive documentation for `dylan pr` and `dylan release` commands
  - Documentation for branching strategy support and merge strategies
  - Enhanced README files across all dylan modules

## [0.6.0] - 2025-05-19

### Added
- New `dylan release` command for automated project releases (`10bed2a`)
  - Introduces autonomous release management functionality
  - Detects project configuration and manages version bumps
  - Updates changelogs and optionally creates git commits/tags
  - Follows dylan philosophy of minimal wrappers and maximum Claude autonomy
  - Supports project-agnostic operations with configurable version bump types
  - Includes dry-run mode for safe operation previews

## [0.5.1] - 2025-05-19

### Changed
- Remove temporary workflow report files (`4ac095e`)
  - Clean up pr_report.md and review_report.md files from repository
  - Keep repository tidy by removing temporary files generated during workflows

## [0.5.0] - 2025-05-19

### Added
- New `dylan pr` command for autonomous pull request creation
  - Complete PR creation module integrated into the main CLI
  - Analyzes commits and creates PRs automatically
  - Works with GitHub CLI for seamless integration
  - Supports custom target branches and dry-run mode

### Changed
- Refactored pre-push hook to add branch-specific versioning rules (`5ee18c5`)
  - Apply different versioning rules based on target branch
  - Main branch: Bump version and create new changelog section  
  - Feature branches: Append to [Unreleased] section without version bump
  - Add clearer branch detection and file management instructions
- Refactored dylan to improve pr and review file handling with tmp directory (`5ee18c5`)
  - Move report outputs to tmp/ directory to avoid clutter
  - Add timestamp-based filename generation for existing files
  - Enhance file handling instructions in prompts
  - Ensure proper directory creation before writing reports

### Fixed
- Updated README files for dylan pr and review commands (`05c9716`)

### Breaking Changes
- Report files are now saved to tmp/ directory by default (`5ee18c5`)

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