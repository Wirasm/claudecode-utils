# Full Review Loop

The Agentic Review Loop is an advanced workflow that orchestrates multiple Claude instances to review, develop, validate, and create PRs within a safe, temporary environment.

## Files

- `full_review_loop_safe.py` - The main implementation with safety features
- `full_review_loop_poc.py` - Proof-of-concept version (less stable)
- `tests/` - Test suite for the review loop

## Key Features

- **Automatic Branching:** Creates a temporary branch by default (e.g., feature-branch-agentic-TIMESTAMP) to avoid modifying the original branch directly.
- **Optional Worktree Isolation:** Use `--worktree` to run the entire process within a dedicated git worktree directory for better isolation.
- **Iterative Improvement:** Runs Reviewer -> Developer -> Re-Reviewer -> Validator loop.
- **Feedback Loop:** If validation fails, the Developer agent receives the validation feedback to attempt fixes in the next iteration.
- **PR Creation:** Creates a pull request via `gh` CLI upon successful validation (can be skipped).
- **Intelligent File Selection:** Centralized logic for selecting appropriate review files for each iteration.
- **Optimized Workflow:** Skips unnecessary steps after validation failure.

## Usage

```bash
# Review latest commit in a new temp branch (default behavior)
uv run python library/full_review_loop/full_review_loop_safe.py --latest

# Review a specific branch in a new temp branch, using a worktree
uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --worktree

# Specify base branch and keep temporary branch after run
uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --base-branch develop --keep-branch
```

## Options

- `--latest` - Compare latest commit to previous commit (HEAD vs HEAD~1)
- `--branch BRANCH` - Source branch to create the temporary work branch from
- `--base-branch BRANCH` - Base branch for comparison in diffs and PR (default: main)
- `--worktree` - Run the entire process within a dedicated git worktree
- `--keep-branch` - Do not delete the temporary work branch after completion
- `--max-iterations N` - Maximum number of improvement cycles (default: 3)
- `--output-dir DIR` - Directory for output files (default: tmp/agentic_loop_TIMESTAMP)
- `--verbose, -v` - Show verbose output
- `--no-pr` - Skip PR creation even if validation passes
- `--pr-title TITLE` - Custom title for PR (default: auto-generated)
- `--timeout N` - Timeout in seconds for each agent (default: 600 - 10 mins)

## Workflow Details

1. **Repository Setup:**
   - Creates a temporary branch from the source branch or latest commit
   - Optionally creates a git worktree for complete isolation

2. **Review Phase:**
   - Reviewer agent analyzes code differences between the temporary branch and base branch
   - Identifies issues with code quality, architecture, error handling, etc.
   - Categorizes issues by priority (CRITICAL, HIGH, MEDIUM, LOW)
   - Provides actionable recommendations for each issue

3. **Development Phase:**
   - Developer agent implements fixes for CRITICAL and HIGH priority issues
   - Uses the review file and any previous validation feedback
   - Creates commits with descriptive messages
   - Writes a development report detailing changes made

4. **Re-Review Phase:**
   - Reviewer agent re-examines the code after fixes have been implemented
   - Checks if previous issues were addressed and identifies any new issues
   - Updates issue list with current state

5. **Validation Phase:**
   - Validator agent verifies that all CRITICAL and HIGH issues were properly addressed
   - Uses both the re-review report and development report
   - Reports whether validation passed or failed

6. **Iteration Loop:**
   - If validation fails and max iterations not reached, continues to the next iteration
   - Developer receives both re-review and validation feedback
   - Workflow optimizes to skip unnecessary steps in subsequent iterations

7. **PR Creation:**
   - After successful validation, PR Manager agent creates a pull request
   - Summarizes changes, issues addressed, and validation results
   - Uses GitHub CLI to push changes and create the PR

## Output Artifacts

All output is saved to the specified output directory (default: tmp/agentic_loop_TIMESTAMP):

- `review_iter_N.md` - Initial review for iteration N
- `dev_report_iter_N.md` - Developer report for iteration N
- `rereview_iter_N.md` - Re-review after development for iteration N
- `validation_iter_N.md` - Validation report for iteration N
- `pr_report.md` - PR creation report (if validation passes)

## Requirements

- Python 3.8+
- Claude CLI installed and configured
- Git
- GitHub CLI (gh) for PR creation