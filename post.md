# Sharing my Agentic Review Loop tool 🛠️

Hey folks!

Just wanted to share that I've cleaned up and generalized the Agentic Loop System I mentioned a few days ago. It's now ready if anyone wants to try it out in their own projects.

## Quick Refresher

It's a system where multiple Claude instances work together to:

- Review your code
- Implement fixes
- Validate the changes
- Create a PR

Everything happens in branches so it's safe to use with your actual code.
You can also flag `--worktree` to use git worktrees for even better isolation.

## Core Features

- **Automatic Branching:** Creates temp branches to keep your original branch untouched
- **Worktree Isolation:** Optional complete isolation using git worktrees
- **Iterative Improvement:** Runs through multiple improvement cycles as needed
- **Smart Workflow:** Skips unnecessary steps when continuing after validation fails
- **File Management:** Properly tracks artifacts across iterations
- **Comprehensive Reports:** Detailed reports for each step of the process
- **PR Creation:** Generates detailed PRs with the GitHub CLI when validation passes

## Setup and Usage

The core script is at `library/full_review_loop/full_review_loop_safe.py` - you can just copy it into your project and run it:

1. Write some code
2. Commit
3. Run the script

You can review the latest commit:

```bash
uv run python library/full_review_loop/full_review_loop_safe.py --latest --verbose
```

Or review a specific branch against main:

```bash
uv run python library/full_review_loop/full_review_loop_safe.py --branch feature-branch --worktree --verbose
```

There is a range of arguments you can use to customize the behavior. Check out the README for more details.

I've also split out the components so you can use them individually if you want (will probably add this feature to the CLI at some point):

```bash
# Just want a code review?
uv run python library/simple_review/simple_review_poc.py my-branch --output review.md

# Just implement fixes from a review?
uv run python library/simple_dev/simple_dev_poc.py review.md --output dev_report.md
```

## My Experience

I've been using this regularly for a few weeks now:

- It's saved me a ton of time on code reviews
- The PRs it creates are super detailed
- It's surprisingly good at fixing subtle bugs

The repo has READMEs for each component if you want to check it out. Would love to hear if anyone gives it a try!