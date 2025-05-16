# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-05-16

### Added
- Added JSON format for review reports

### Fixed
- Fixed review CLI to support natural argument order (branch before options)

## [1.1.1] - 2025-05-16

### Changed
- Updated version numbers in pyproject.toml and __init__.py
- Maintenance release with no functional changes

## [1.1.0] - 2025-05-16

### Added
- Added enhanced code review command-line interface with Typer framework
- Implemented multi-format support for review reports (JSON and Markdown)
- Added simple Claude Code review runner CLI tool
- Added functionality to save code review reports to repository root directory
- Added JSON output format option for code review reports

### Changed
- Improved CLI structure to use Typer for better command organization
- Enhanced documentation for the review runner module

## [1.0.0] - 2025-05-16

### Added
- Added code review command 
- Refactored CLI structure with Typer
- Added output format support for JSON and markdown review reports
- Added JSON output format option to code review runner
- Added ability to save code review report to repository root directory
- Added simple Claude Code review runner CLI tool

### Changed
- Formatted long lines using black code formatter
- Deleted code review report for cc-review-runner feature

## [0.4.1] - 2025-05-16

### Changed
- Removed GitHub Actions workflow documentation from README

## [0.4.0] - 2025-05-15

### Added
- Added documentation for automated bug triaging
- Added restriction for major version bumps to explicit breaking changes only

## [0.3.0] - 2025-05-15

### Added
- Implemented automated bug triage tool with Claude integration
- Added concept library with analysis, innovative ideas, and potential features for future development

## [0.2.3] - 2025-05-15

### Fixed
- Updated workflow to explicitly create PR using GitHub CLI

## [0.2.2] - 2025-05-15

### Added
- Added CODEOWNERS file to define code ownership and review responsibilities

## [0.2.1] - 2025-05-15

### Changed
- Streamlined changelog workflow with GitHub CLI integration and PR automation

## [0.2.0] - 2025-05-15

### Added
- Implemented multiple API key configuration methods
- Enhanced debug logging
- Added debug logging for better troubleshooting
- Enhanced changelog automation with structured JSON response handling

### Changed
- Simplified changelog update workflow with streamlined version extraction
- Simplified changelog update workflow with better error handling

### Fixed
- Removed invalid character from changelog workflow file

## [0.1.0] - Initial Release

### Added
- Initial project structure
- Basic functionality