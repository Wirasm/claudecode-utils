#!/usr/bin/env -S uv run --script
"""
Automated Bug Triaging - A proof-of-concept tool that uses Claude to analyze GitHub issues.

This tool:
1. Fetches GitHub issues from a repository
2. Uses Claude to categorize issues by severity and type
3. Assigns issues to components
4. Generates reproduction steps
5. Suggests potential fixes

Typical usage:
    # Analyze all open issues in a repository
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo

    # Analyze a specific issue
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --issue 123

    # Analyze issues with a specific label
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --label bug

    # Generate a markdown report
    uv run python concept_library/automated_bug_triage/bug_triage_poc.py --repo owner/repo --output report.md

Arguments:
    --repo          Repository name in format "owner/repo"
    --issue         Specific issue number to analyze (optional)
    --label         Filter issues by label (optional)
    --max-issues    Maximum number of issues to analyze (default: 10)
    --output        Output file path for the report (default: bug_triage_report.md)
    --model         Claude CLI executable name (default: "claude")
    --dry-run       Fetch issues but don't analyze with Claude
    --verbose       Print detailed logs
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Import PyGithub with fallback
try:
    from github import Auth, Github

    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Constants
DEFAULT_MAX_ISSUES = 10
DEFAULT_OUTPUT = "bug_triage_report.md"
DEFAULT_MODEL = "claude"


def log(message, verbose=False):
    """Print log message if verbose mode is enabled."""
    if verbose:
        print(f"[BUG TRIAGE] {message}")


def fetch_issues_with_pygithub(
    repo_name, issue_number=None, label=None, max_issues=DEFAULT_MAX_ISSUES, verbose=False
):
    """Fetch issues from GitHub using PyGithub."""
    log(f"Fetching issues from {repo_name} using PyGithub", verbose)

    # Get GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log("GITHUB_TOKEN environment variable not set", verbose)
        return None

    try:
        # Authenticate with GitHub
        auth = Auth.Token(token)
        github = Github(auth=auth)

        # Get repository
        repo = github.get_repo(repo_name)

        # Fetch specific issue if requested
        if issue_number:
            try:
                issue = repo.get_issue(number=int(issue_number))
                return [issue]
            except Exception as e:
                log(f"Error fetching issue #{issue_number}: {str(e)}", verbose)
                return []

        # Fetch issues with filters
        query_params = {"state": "open", "sort": "created", "direction": "desc"}

        if label:
            query_params["labels"] = [label]

        issues = list(repo.get_issues(**query_params)[:max_issues])
        log(f"Found {len(issues)} issues", verbose)
        return issues

    except Exception as e:
        log(f"Error with PyGithub: {str(e)}", verbose)
        return None
    finally:
        if "github" in locals():
            github.close()


def fetch_issues_with_github_cli(
    repo_name, issue_number=None, label=None, max_issues=DEFAULT_MAX_ISSUES, verbose=False
):
    """Fetch issues from GitHub using GitHub CLI as fallback."""
    log(f"Fetching issues from {repo_name} using GitHub CLI", verbose)

    # Build gh CLI command
    if issue_number:
        cmd = [
            "gh",
            "issue",
            "view",
            issue_number,
            "--repo",
            repo_name,
            "--json",
            "number,title,body,createdAt,updatedAt,state,labels,assignees,comments",
        ]
    else:
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo_name,
            "--state",
            "open",
            "--json",
            "number,title,body,createdAt,updatedAt,state,labels,assignees",
            "--limit",
            str(max_issues),
        ]

        if label:
            cmd.extend(["--label", label])

    try:
        log(f"Running command: {' '.join(cmd)}", verbose)
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Parse the JSON output
        if issue_number:
            # For single issue view, gh returns a single JSON object
            issues = [json.loads(result.stdout)]
        else:
            # For issue list, gh returns an array of JSON objects
            issues = json.loads(result.stdout)

        log(f"Found {len(issues)} issues", verbose)
        return issues

    except subprocess.CalledProcessError as e:
        log(f"Error with GitHub CLI: {e.stderr}", verbose)
        return None
    except json.JSONDecodeError as e:
        log(f"Error parsing GitHub CLI output: {str(e)}", verbose)
        return None
    except Exception as e:
        log(f"Unexpected error with GitHub CLI: {str(e)}", verbose)
        return None


def fetch_repository_structure(repo_name, verbose=False):
    """Fetch repository structure to help with component assignment."""
    log(f"Fetching repository structure for {repo_name}", verbose)

    try:
        # Use GitHub CLI to get repository structure
        cmd = ["gh", "api", f"repos/{repo_name}/git/trees/main?recursive=1"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Parse the JSON output
        tree_data = json.loads(result.stdout)

        # Extract file paths to understand component structure
        if "tree" in tree_data:
            file_paths = [item["path"] for item in tree_data["tree"] if item["type"] == "blob"]

            # Organize files by directory
            components = {}
            for path in file_paths:
                # Get the top-level directory
                top_dir = path.split("/")[0] if "/" in path else "root"
                if top_dir not in components:
                    components[top_dir] = []
                components[top_dir].append(path)

            return components

    except Exception as e:
        log(f"Error fetching repository structure: {str(e)}", verbose)

    # Return a minimal structure if we couldn't fetch the real one
    return {"src": [], "docs": [], "tests": []}


def analyze_issue_with_claude(issue, repo_structure, model=DEFAULT_MODEL, verbose=False):
    """Analyze a GitHub issue using Claude."""
    log(f"Analyzing issue #{issue['number']} with Claude", verbose)

    # Prepare issue data
    issue_data = {
        "number": issue["number"],
        "title": issue["title"],
        "body": issue["body"] or "",
        "created_at": issue.get("createdAt", ""),
        "updated_at": issue.get("updatedAt", ""),
        "labels": [label["name"] for label in issue.get("labels", [])],
    }

    # Create prompt for Claude
    prompt = f"""
    I need you to analyze this GitHub issue and provide:
    1. A severity categorization (critical, high, medium, low)
    2. The bug type (functional, UI/UX, performance, security, etc.)
    3. The component this likely belongs to
    4. Clear reproduction steps
    5. Potential approaches for fixing this issue

    # Issue Information
    - Number: #{issue_data["number"]}
    - Title: {issue_data["title"]}
    - Created: {issue_data["created_at"]}
    - Updated: {issue_data["updated_at"]}
    - Labels: {", ".join(issue_data["labels"]) if issue_data["labels"] else "None"}

    # Issue Description
    {issue_data["body"]}

    # Repository Structure
    Here's the structure of the repository to help with component assignment:
    {json.dumps(repo_structure, indent=2)}

    Please provide your analysis in this JSON format:
    ```json
    {{
      "severity": "critical|high|medium|low",
      "bug_type": "functional|ui_ux|performance|security|...",
      "component": "name of the most relevant component",
      "reproduction_steps": [
        "step 1",
        "step 2",
        ...
      ],
      "fix_suggestions": [
        "approach 1",
        "approach 2",
        ...
      ],
      "reasoning": "explain why you categorized this issue this way"
    }}
    ```

    Make your best determination based on the information available. If certain details are unclear,
    note this in your reasoning but still provide the most likely categorization.
    """

    # Create temporary file for the prompt
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        prompt_file = f.name
        f.write(prompt)

    try:
        # Run Claude to analyze the issue
        cmd = [model, "-p", "@" + prompt_file, "--print"]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Extract JSON result from Claude's response
        claude_response = result.stdout

        # Find JSON output in the response
        json_start = claude_response.find("```json")
        json_end = claude_response.rfind("```")

        if json_start == -1 or json_end == -1:
            log("Could not find JSON in Claude's response", verbose)
            return None

        # Extract and parse the JSON
        json_text = claude_response[json_start + 7 : json_end].strip()
        analysis_result = json.loads(json_text)

        return analysis_result

    except subprocess.CalledProcessError as e:
        log(f"Error running Claude: {e.stderr if hasattr(e, 'stderr') else str(e)}", verbose)
        return None
    except json.JSONDecodeError as e:
        log(f"Error parsing Claude's JSON output: {str(e)}", verbose)
        return None
    except Exception as e:
        log(f"Unexpected error with Claude: {str(e)}", verbose)
        return None
    finally:
        # Clean up the temporary file
        try:
            os.unlink(prompt_file)
        except:
            pass


def generate_report(issues, analyses, output_file, verbose=False):
    """Generate a markdown report with the analysis results."""
    log(f"Generating report to {output_file}", verbose)

    report = []

    # Report header
    report.append("# Automated Bug Triage Report")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Summary statistics
    if analyses:
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        bug_type_counts = {}
        component_counts = {}

        for issue_num, analysis in analyses.items():
            if analysis:
                severity = analysis.get("severity", "unknown").lower()
                bug_type = analysis.get("bug_type", "unknown").lower()
                component = analysis.get("component", "unknown").lower()

                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                bug_type_counts[bug_type] = bug_type_counts.get(bug_type, 0) + 1
                component_counts[component] = component_counts.get(component, 0) + 1

        # Add summary section
        report.append("## Summary\n")
        report.append("### Issues by Severity")
        for severity, count in severity_counts.items():
            if count > 0:
                report.append(f"- **{severity.title()}**: {count}")

        report.append("\n### Issues by Type")
        for bug_type, count in sorted(bug_type_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{bug_type.replace('_', ' ').title()}**: {count}")

        report.append("\n### Issues by Component")
        for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{component.replace('_', ' ').title()}**: {count}")

        report.append("\n")

    # Individual issue analyses
    report.append("## Issue Analyses\n")

    # Sort issues by severity (if available)
    def get_severity_weight(issue_num):
        if issue_num not in analyses or not analyses[issue_num]:
            return 4  # Unknown severity gets lowest priority
        severity = analyses[issue_num].get("severity", "").lower()
        weights = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return weights.get(severity, 4)

    sorted_issues = sorted(issues, key=lambda i: get_severity_weight(i["number"]))

    for issue in sorted_issues:
        issue_num = issue["number"]
        analysis = analyses.get(issue_num)

        report.append(f"### Issue #{issue_num}: {issue['title']}")

        # Add links to GitHub issue
        if isinstance(issue.get("url"), str):
            report.append(f"[View on GitHub]({issue['url']})\n")

        if analysis:
            # Display severity with appropriate formatting
            severity = analysis.get("severity", "unknown").lower()
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "unknown": "⚪",
            }

            report.append(f"**Severity**: {severity_emoji.get(severity, '⚪')} {severity.title()}")
            report.append(
                f"**Bug Type**: {analysis.get('bug_type', 'Unknown').replace('_', ' ').title()}"
            )
            report.append(
                f"**Component**: {analysis.get('component', 'Unknown').replace('_', ' ').title()}"
            )

            # Reproduction steps
            report.append("\n#### Reproduction Steps")
            if analysis.get("reproduction_steps"):
                for i, step in enumerate(analysis["reproduction_steps"], 1):
                    report.append(f"{i}. {step}")
            else:
                report.append("No reproduction steps available.")

            # Fix suggestions
            report.append("\n#### Potential Fix Approaches")
            if analysis.get("fix_suggestions"):
                for i, suggestion in enumerate(analysis["fix_suggestions"], 1):
                    report.append(f"- {suggestion}")
            else:
                report.append("No fix suggestions available.")

            # Reasoning (optional)
            if analysis.get("reasoning"):
                report.append("\n#### Analysis Reasoning")
                report.append(analysis["reasoning"])
        else:
            report.append("*No analysis available for this issue.*")

        report.append("\n---\n")

    # Write the report to file
    with open(output_file, "w") as f:
        f.write("\n".join(report))

    log(f"Report generated successfully: {output_file}", verbose)
    return output_file


def main():
    """Main entry point for the bug triage tool."""
    parser = argparse.ArgumentParser(description="Automated bug triaging tool using Claude")
    parser.add_argument("--repo", required=True, help="Repository name in format 'owner/repo'")
    parser.add_argument("--issue", help="Specific issue number to analyze")
    parser.add_argument("--label", help="Filter issues by label")
    parser.add_argument(
        "--max-issues",
        type=int,
        default=DEFAULT_MAX_ISSUES,
        help=f"Maximum number of issues to analyze (default: {DEFAULT_MAX_ISSUES})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output file path for the report (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude CLI executable name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Fetch issues but don't analyze with Claude"
    )
    parser.add_argument("--verbose", action="store_true", help="Print detailed logs")

    args = parser.parse_args()

    # Validate repository name format
    if "/" not in args.repo:
        print(f"Error: Repository name must be in the format 'owner/repo', got '{args.repo}'")
        sys.exit(1)

    # Check for issue number format
    if args.issue and not args.issue.isdigit():
        print(f"Error: Issue number must be a number, got '{args.issue}'")
        sys.exit(1)

    # Fetch issues (try PyGithub first, fall back to GitHub CLI)
    issues = None

    if GITHUB_AVAILABLE:
        issues = fetch_issues_with_pygithub(
            args.repo,
            issue_number=args.issue,
            label=args.label,
            max_issues=args.max_issues,
            verbose=args.verbose,
        )

    # Fall back to GitHub CLI if PyGithub failed or is not available
    if issues is None:
        issues = fetch_issues_with_github_cli(
            args.repo,
            issue_number=args.issue,
            label=args.label,
            max_issues=args.max_issues,
            verbose=args.verbose,
        )

    # Check if we successfully fetched issues
    if issues is None:
        print("Error: Failed to fetch issues. Check your repository name and GitHub access.")
        sys.exit(1)

    if not issues:
        print("No issues found matching your criteria.")
        sys.exit(0)

    print(f"Found {len(issues)} issues to analyze.")

    # Fetch repository structure for component assignment
    repo_structure = fetch_repository_structure(args.repo, verbose=args.verbose)

    # Analyze issues with Claude (unless dry-run)
    analyses = {}
    if not args.dry_run:
        for issue in issues:
            issue_num = issue["number"]
            print(f"Analyzing issue #{issue_num}: {issue['title']}")

            analysis = analyze_issue_with_claude(
                issue, repo_structure, model=args.model, verbose=args.verbose
            )

            analyses[issue_num] = analysis

    # Generate report
    report_path = generate_report(issues, analyses, args.output, verbose=args.verbose)
    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    main()
