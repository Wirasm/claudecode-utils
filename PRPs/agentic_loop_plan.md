# Agentic Loop Reimplementation Plan

## Overview

This document outlines a plan for reimplementing the `agentic_loop.py` script to create a streamlined, sequential process that runs all agents in a single worktree. The improved system will maintain context across different agent stages and provide better control over comparison modes.

## Design Principles

1. **Single Worktree**: Run all agents in the same worktree to maintain consistent context
2. **Configurable Comparison**: Support comparing latest commit vs. previous or branch vs. branch
3. **Iterative Improvement**: Automatically re-run development if validation fails
4. **Simple Interface**: Clear CLI with intuitive options
5. **Comprehensive Reporting**: Generate detailed reports at each stage

## Implementation Structure

### Core Components

1. **AgenticLoop Class**:

   - Initialize with branch/commit information
   - Track state and artifacts across stages
   - Manage execution flow with configurable iteration

2. **Agent Stages**:

   - Review: Analyze code and identify issues
   - Develop: Implement fixes based on review
   - Validate: Verify fixes and ensure quality
   - PR: Create pull request if validation passes

3. **Comparison Modes**:
   - Latest Commit: Compare HEAD~1 vs HEAD
   - Branch: Compare base_branch vs head_branch

## Detailed Implementation Plan

### 1. Script Setup

```python
class ComparisonMode(Enum):
    LATEST_COMMIT = "latest_commit"  # Compare HEAD~1 vs HEAD
    BRANCH = "branch"  # Compare base_branch vs head_branch

class AgenticLoop:
    def __init__(
        self,
        base_branch="main",
        head_branch="development-wip",
        comparison_mode=ComparisonMode.BRANCH,
        max_iterations=3,
        output_dir=None,
        verbose=False
    ):
        # Initialize state variables
        self.base_branch = base_branch
        self.head_branch = head_branch
        self.comparison_mode = comparison_mode
        self.max_iterations = max_iterations
        self.iteration = 0
        self.verbose = verbose

        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("tmp") / f"agentic_loop_{int(time.time())}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up paths for artifacts
        self.review_file = self.output_dir / "review.md"
        self.dev_report_file = self.output_dir / "dev_report.md"
        self.validation_file = self.output_dir / "validation.md"
        self.pr_file = self.output_dir / "pr.md"

        # Set up comparison command
        self._setup_comparison_command()
```

### 2. Comparison Command Setup

```python
def _setup_comparison_command(self):
    """Set up the git diff command based on comparison mode"""
    if self.comparison_mode == ComparisonMode.LATEST_COMMIT:
        self.compare_cmd = "HEAD~1...HEAD"
        self.log(f"Comparison mode: Latest commit (HEAD~1 vs HEAD)")
    else:  # ComparisonMode.BRANCH
        self.compare_cmd = f"{self.base_branch}...{self.head_branch}"
        self.log(f"Comparison mode: Branch ({self.base_branch} vs {self.head_branch})")
```

### 3. Agent Execution Methods

```python
def run_review(self):
    """Run the reviewer to analyze code and identify issues"""
    self.log(f"Running review (iteration {self.iteration}/{self.max_iterations})...")

    cmd = [
        "python", "scripts/simple_review.py",
        self.head_branch if self.comparison_mode == ComparisonMode.BRANCH else "--latest-commit",
        "--output", str(self.review_file)
    ]

    if self.verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        success = True
    except subprocess.CalledProcessError as e:
        self.log(f"Review failed: {e}")
        success = False

    return success

def run_development(self):
    """Run the developer to implement fixes identified in the review"""
    self.log(f"Running development (iteration {self.iteration}/{self.max_iterations})...")

    cmd = [
        "python", "scripts/simple_dev.py",
        str(self.review_file),
        "--branch", self.head_branch
    ]

    if self.comparison_mode == ComparisonMode.LATEST_COMMIT:
        cmd.append("--latest-commit")

    cmd.extend(["--output", str(self.dev_report_file)])

    if self.verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        success = True
    except subprocess.CalledProcessError as e:
        self.log(f"Development failed: {e}")
        success = False

    return success

def run_validation(self):
    """Run the validator to verify fixes and ensure quality"""
    self.log(f"Running validation (iteration {self.iteration}/{self.max_iterations})...")

    cmd = [
        "python", "scripts/simple_validator.py",
        str(self.review_file),
        str(self.dev_report_file),
        "--branch", self.head_branch
    ]

    if self.comparison_mode == ComparisonMode.LATEST_COMMIT:
        cmd.append("--latest-commit")

    cmd.extend(["--output", str(self.validation_file)])

    if self.verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        success = result.returncode == 0  # Return code 0 means validation passed
        validation_passed = success
    except subprocess.CalledProcessError as e:
        self.log(f"Validation failed: {e}")
        success = False
        validation_passed = False

    return success, validation_passed

def run_pr(self, pr_title=None):
    """Run the PR manager to create a pull request"""
    self.log(f"Running PR creation...")

    cmd = [
        "python", "scripts/simple_pr.py",
        str(self.validation_file),
        "--branch", self.head_branch,
        "--base", self.base_branch
    ]

    if pr_title:
        cmd.extend(["--title", pr_title])

    cmd.extend(["--output", str(self.pr_file)])

    if self.verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        success = result.returncode == 0
    except subprocess.CalledProcessError as e:
        self.log(f"PR creation failed: {e}")
        success = False

    return success
```

### 4. Main Loop Execution

```python
def run(self):
    """Run the full agentic loop workflow"""
    self.log(f"Starting agentic loop:")
    self.log(f"  Comparison: {self.compare_cmd}")
    self.log(f"  Max iterations: {self.max_iterations}")
    self.log(f"  Output directory: {self.output_dir}")

    while self.iteration < self.max_iterations:
        self.iteration += 1
        self.log(f"\n=== Starting iteration {self.iteration}/{self.max_iterations} ===")

        # Run review phase
        review_success = self.run_review()
        if not review_success:
            self.log("Review phase failed. Stopping loop.")
            break

        # Run development phase
        dev_success = self.run_development()
        if not dev_success:
            self.log("Development phase failed. Stopping loop.")
            break

        # Run validation phase
        validation_success, validation_passed = self.run_validation()
        if not validation_success:
            self.log("Validation phase failed. Stopping loop.")
            break

        # If validation passed, run PR phase and exit
        if validation_passed:
            self.log("Validation passed! Running PR phase.")
            pr_success = self.run_pr()
            if pr_success:
                self.log("PR phase completed successfully.")
            else:
                self.log("PR phase failed.")
            break
        else:
            self.log("Validation failed. Starting next iteration.")

    # Handle reaching max iterations without validation passing
    if self.iteration == self.max_iterations and 'validation_passed' in locals() and not validation_passed:
        self.log(f"Reached maximum iterations ({self.max_iterations}) without passing validation.")

    self.log(f"Agentic loop completed. Output artifacts are in: {self.output_dir}")

    # Return success if validation passed
    return validation_passed if 'validation_passed' in locals() else False
```

### 5. CLI Interface

```python
def main():
    parser = argparse.ArgumentParser(description="Run agentic loop for MCP development")

    # Comparison configuration
    comparison_group = parser.add_mutually_exclusive_group(required=True)
    comparison_group.add_argument("--latest-commit", action="store_true",
                                 help="Compare latest commit to previous (HEAD vs HEAD~1)")
    comparison_group.add_argument("--branches", nargs=2, metavar=("BASE", "HEAD"),
                                 help="Compare two branches (BASE vs HEAD)")

    # Additional options
    parser.add_argument("--max-iterations", type=int, default=3,
                       help="Maximum number of improvement iterations (default: 3)")
    parser.add_argument("--output-dir", help="Directory for output artifacts (default: tmp/agentic_loop_<timestamp>)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--pr-title", help="Title for pull request (default: auto-generated)")

    args = parser.parse_args()

    # Set up the AgenticLoop with the appropriate configuration
    if args.latest_commit:
        loop = AgenticLoop(
            comparison_mode=ComparisonMode.LATEST_COMMIT,
            max_iterations=args.max_iterations,
            output_dir=args.output_dir,
            verbose=args.verbose
        )
    else:
        base_branch, head_branch = args.branches
        loop = AgenticLoop(
            base_branch=base_branch,
            head_branch=head_branch,
            comparison_mode=ComparisonMode.BRANCH,
            max_iterations=args.max_iterations,
            output_dir=args.output_dir,
            verbose=args.verbose
        )

    # Run the loop
    try:
        success = loop.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during agentic loop execution: {e}")
        sys.exit(1)
```

## Key Improvements Over Current Implementation

1. **Simplified Architecture**:

   - Single worktree approach eliminates complexity of managing multiple git worktrees
   - Sequential execution in the same context maintains consistency
   - Reuses the proven simple\_\* scripts rather than reimplementing their functionality

2. **Improved Control**:

   - Clear separation between latest-commit and branch comparison modes
   - Configurable iteration count for fixing complex issues
   - Verbose mode for detailed logging

3. **Better Error Handling**:

   - Graceful failure at each stage with detailed error reporting
   - Appropriate return codes for system integration

4. **Enhanced Workflow**:
   - Automatic re-running of development when validation fails
   - Organized output artifacts with timestamp-based directories
   - Clear CLI interface with intuitive options

## Implementation Steps

1. Create a new agentic_loop.py file in the scripts directory
2. Implement the AgenticLoop class with the core functionality
3. Add the agent execution methods (review, develop, validate, PR)
4. Implement the main CLI interface
5. Test with both comparison modes and various scenarios
6. Add comprehensive documentation

## Usage Examples

```bash
# Compare latest commit to previous commit
uv run python scripts/agentic_loop.py --latest-commit --verbose

# Compare development-wip branch to main branch
uv run python scripts/agentic_loop.py --branches main development-wip --verbose

# Run with custom output directory and PR title
uv run python scripts/agentic_loop.py --latest-commit --output-dir tmp/my_loop --pr-title "Add configuration management" --verbose

# Run with increased iteration limit for complex fixes
uv run python scripts/agentic_loop.py --branches main feature-branch --max-iterations 5 --verbose
```

## Testing Strategy

1. Test the core functionality with simple changes
2. Test both comparison modes (latest-commit and branch)
3. Test error handling by introducing deliberate failures
4. Test iteration with validation failures that require multiple attempts
5. Test PR creation with validation success

## Conclusion

This reimplementation of the agentic*loop.py script will provide a more streamlined, reliable approach to automated code review and improvement. By using a single worktree and leveraging the existing simple*\* scripts, it maintains simplicity while adding flexibility and robustness.
