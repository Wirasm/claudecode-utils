# PRP-001: Standardizing Prompt Patterns Across Dylan Runners

## Summary

This proposal aims to improve the consistency and maintainability of prompts across the dylan utility library runners (review, PR, and release). By standardizing common patterns and structures, we can reduce duplication, improve maintainability, and ensure consistent behavior across all runner components.

## Problem Statement

After reviewing the prompts in the dylan review runner, PR runner, and release runner, several inconsistencies and potential issues were identified:

1. **Inconsistent Branching Strategy Detection**: Each runner implements its own approach to detecting and handling branching strategies.
2. **Varying Error Handling Guidance**: No standardized approach to error handling across prompts.
3. **Inconsistent Step Numbering**: Some prompts have conditional numbering or numbering gaps.
4. **Varying Detail Levels**: Different levels of detail for similar operations across prompts.
5. **Complex Conditional Logic**: Some prompts contain complex conditional logic that could be simplified.
6. **Inconsistent File Format Handling**: Slight variations in how file extensions are determined.
7. **Varying Report Metadata Requirements**: Different metadata requirements across prompts.

## Proposed Solution

Create standardized prompt components that can be shared across all runners, ensuring consistency in structure, behavior, and output.

### 1. Create Shared Prompt Components

Extract common elements into reusable components:

```python
# Example implementation in a new file: dylan/utility_library/shared/prompt_components.py

def get_branching_strategy_detection():
    """Return standardized branching strategy detection instructions."""
    return """
BRANCH STRATEGY DETECTION:
1. Check for .branchingstrategy file in repository root
2. If found, parse release_branch (typically: develop) and production_branch (typically: main)
3. If not found, check for common development branches (develop, development, dev)
4. If none found, fall back to main/master
5. Report which branches were selected
"""

def get_file_handling_instructions(file_prefix, extension):
    """Return standardized file handling instructions."""
    return f"""
IMPORTANT FILE HANDLING INSTRUCTIONS:
- Save your report to the tmp/ directory
- CRITICAL: Get current branch name and include it in filename
- Base filename format: tmp/{file_prefix}_<branch_name>_YYYYMMDD_HHMMSS{extension}
- Replace slashes in branch name with dashes (e.g., feature/foo → feature-foo)
- Use the Bash tool to check if the file exists first
- Always create a new file with timestamp for each operation
- Ensure tmp/ directory exists: mkdir -p tmp
"""

def get_error_handling_instructions():
    """Return standardized error handling instructions."""
    return """
ERROR HANDLING:
1. If any command fails, capture the error message
2. Report the specific command that failed
3. Suggest possible solutions or workarounds
4. Continue with remaining steps if possible
5. Include all errors in the final report
"""

def get_report_metadata_template():
    """Return standardized report metadata template."""
    return """
REPORT METADATA:
- Report file name
- Report relative path
- Branch name
- Base branch used
- Date and time
- Operation type (review/PR/release)
- List of changed files
- Number of commits
- List of commits with IDs and messages
"""
```

### 2. Standardize Step Numbering

Ensure consistent step numbering across all prompts, even when steps are conditional:

```python
# Example of consistent conditional numbering in PR runner
def generate_pr_prompt(update_changelog=False):
    steps = [
        "1. FILE HANDLING: ...",
        "2. GIT CONTEXT DISCOVERY: ...",
        "3. COMMIT ANALYSIS: ...",
    ]
    
    if update_changelog:
        steps.append("4. CHANGELOG SECTION: ...")
        steps.append("5. PR CREATION LOGIC: ...")
        steps.append("6. REPORT GENERATION: ...")
    else:
        steps.append("4. PR CREATION LOGIC: ...")
        steps.append("5. REPORT GENERATION: ...")
    
    return "\n\n".join(steps)
```

### 3. Align Detail Levels

Balance the level of detail across prompts:

```python
# Example of standardized changelog formatting instructions
def get_changelog_instructions():
    """Return standardized changelog formatting instructions."""
    return """
CHANGELOG FORMATTING:
1. Group changes by conventional commit types:
   - Added: new features (commits starting with feat:)
   - Changed: updates (commits: refactor:, style:, perf:, chore:)
   - Fixed: bug fixes (commits starting with fix:)
   - Removed: removed features
2. Format each entry: '- <description> (`<commit_hash>`)'
3. Example format:
   ### Added
   - New feature description (`abc123`)
   ### Changed
   - Updated component behavior (`def456`)
   ### Fixed
   - Resolved issue with validation (`ghi789`)
"""
```

### 4. Simplify Complex Logic

Break down complex conditional logic into clearer steps:

```python
# Example of simplified merge strategy logic
def get_merge_strategy_instructions(strategy):
    """Return merge strategy instructions based on strategy type."""
    if strategy == "direct":
        return """
DIRECT MERGE STRATEGY:
1. Commit changes on release branch
2. Push release branch
3. Merge release branch to production branch (main)
4. Tag on production branch if requested
5. Push production branch and tags
"""
    elif strategy == "pr":
        return """
PR MERGE STRATEGY:
1. Commit changes on release branch
2. Push release branch
3. Create a pull request from release branch to production branch
4. Report PR URL
"""
```

### 5. Consistent Branch Handling

Develop a standard approach to branch detection and handling:

```python
# Example of standardized branch handling
def get_branch_handling_instructions():
    """Return standardized branch handling instructions."""
    return """
BRANCH HANDLING:
1. Detect current branch: git symbolic-ref --short HEAD
2. Sanitize branch name for filename (replace / with -)
3. Check if branch exists remotely: git ls-remote --heads origin <branch>
4. Determine base branch using BRANCH STRATEGY DETECTION
5. Report current branch and base branch in output
"""
```

## Implementation Plan

1. Create a new module `dylan/utility_library/shared/prompt_components.py` with standardized components
2. Refactor each runner to use these components:
   - Review runner
   - PR runner
   - Release runner
3. Update tests to ensure behavior remains consistent
4. Update documentation to reflect the new standardized approach

## Benefits

1. **Improved Maintainability**: Changes to common components only need to be made in one place
2. **Consistent Behavior**: Users experience the same patterns across all dylan tools
3. **Reduced Duplication**: Eliminates repeated code across prompts
4. **Better Error Handling**: Standardized approach to handling and reporting errors
5. **Clearer Documentation**: Standardized components are easier to document

## Backwards Compatibility

This change maintains full backward compatibility as it only affects the internal structure of prompts, not their functionality or output format.

## Alternatives Considered

1. **Complete Prompt Rewrite**: Rejected as too disruptive and risky
2. **Template-Based Approach**: Considered but may be less flexible than modular components
3. **No Change**: Rejected as current inconsistencies will grow over time

## Open Questions

1. Should we extract all prompt text to separate files for easier editing?
2. Should we implement a more sophisticated templating system?
3. How should we handle prompt versioning for future changes?

## References

- Current implementation in `dylan/utility_library/dylan_review/dylan_review_runner.py`
- Current implementation in `dylan/utility_library/dylan_pr/dylan_pr_runner.py`
- Current implementation in `dylan/utility_library/dylan_release/dylan_release_runner.py`
