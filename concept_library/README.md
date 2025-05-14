# Claude Code Utility - Concept Library

The Claude Code Utility Concept Library houses several experimental approaches to enhance AI-driven software development with Claude Code. This library showcases multiple concepts for automated code review, development, and AI-driven software engineering workflows.

## Core Concepts

### 1. Automated Review Flow

A comprehensive solution for AI-driven code review and improvement that can be used either as a complete workflow or as individual components:

#### Full Review Loop

The `full_review_loop` is an advanced orchestration system that coordinates multiple Claude instances to review, develop, validate, and create PRs within safe, isolated environments.

**Key Features:**
- Automatic branching and worktree isolation
- Iterative improvement cycles
- Feedback loops between agents
- PR creation upon successful validation
- Safety features to prevent destructive changes

#### Simple Review Components

The modular components of the review flow can be used independently:

- **Simple Review (`simple_review`)**: Generates comprehensive code reviews for git branches or specific commits
- **Simple Developer (`simple_dev`)**: Implements code fixes based on review feedback, prioritizing critical and high-priority issues
- **Simple Validator (`simple_validator`)**: Validates that fixes properly address review issues and meet quality standards
- **Simple PR (`simple_pr`)**: Creates well-documented pull requests based on validated changes

### 2. Product Requirement Prompt (PRP) Flow

The `cc_PRP_flow` is a highly sophisticated agentic engineering workflow concept for implementing vertical slices of working software.

**Key Concept:**
"Over-specifying what to build while under-specifying the context is why so many AI-driven coding attempts stall at 80%. A Product Requirement Prompt (PRP) fixes that by fusing the disciplined scope of a traditional Product Requirements Document (PRD) with the 'context-is-king' mindset of modern prompt engineering."

**Key Features:**
- Structured prompt templates that provide complete context
- AI-critical layers for context, implementation details, and validation gates
- PRP runner script for executing PRPs with Claude Code
- Support for both interactive and headless modes

### 3. Standup Report Generator

The `cc_standup` utility (located in src/utility_library) automates the creation of daily standup reports by analyzing git commits and GitHub PR activity.

**Key Features:**
- Collects recent git commits and PR activity
- Uses Claude to generate structured Markdown reports
- Supports customizable date ranges
- Automatically formats reports with Yesterday/Today/Blockers sections
- Minimal dependencies with graceful fallbacks

## Usage

Each concept directory contains its own README with detailed usage instructions and examples.

## Directory Structure

```
concept_library/
├── cc_PRP_flow/            # Product Requirement Prompt workflow
│   ├── PRPs/               # PRP template and examples
│   ├── ai_docs/            # Documentation for Claude
│   └── scripts/            # PRP runner scripts
│
├── full_review_loop/       # Complete review-develop-validate-PR workflow
│   └── tests/              # Tests for the review loop
│
├── simple_review/          # Code review generation
├── simple_dev/             # Automated code fixes implementation
├── simple_validator/       # Fix validation and quality assurance
└── simple_pr/              # Automated PR creation
```

## Getting Started

1. Clone the repository
2. Set up your environment with the required dependencies
3. Choose a concept to explore
4. Follow the README instructions in the corresponding directory

## Requirements

- Python 3.8+
- Claude CLI installed and configured
- Git repository access
- GitHub CLI (gh) for GitHub-related operations