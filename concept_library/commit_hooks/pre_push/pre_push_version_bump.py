#!/usr/bin/env python3
"""
pre-push hook - bumps semver & updates CHANGELOG using Claude Code
Never bumps major version during development phase
Works with Max-plan OAuth or ANTHROPIC_API_KEY fallback
"""

import os
import re
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

# Get project root
ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
VERSION_FILE = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"


def run(cmd: list[str]) -> str:
    """Run command and return output"""
    return subprocess.check_output(cmd, text=True).strip()


def call_claude(prompt: str, api_fallback: bool = False) -> tuple[int, str]:
    """Call Claude Code with prompt, optionally forcing API key auth"""
    env = os.environ.copy()
    if api_fallback:
        env["CLAUDE_AUTH"] = "api-key"

    try:
        out = subprocess.check_output(["claude", "-p", "--max-turns", "2", prompt], text=True, env=env)
        return 0, out.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or "").strip()


def extract_version() -> str:
    """Extract current version from pyproject.toml"""
    content = VERSION_FILE.read_text()
    m = re.search(r'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', content)
    if m:
        return m.group(1)
    print("❌ Could not find version in pyproject.toml")
    sys.exit(1)


def latest_tag() -> str | None:
    """Get the latest version tag"""
    tags = run(["git", "tag", "--list", "v[0-9]*", "--sort=-v:refname"])
    return tags.splitlines()[0] if tags else None


# Get current version and commits since last tag
current_ver = extract_version()
tag = latest_tag() or ""
log_range = f"{tag}..HEAD" if tag else "HEAD"
commits = run(["git", "log", "--pretty=format:%s%n%b%n---", log_range])

if not commits.strip():
    sys.exit(0)  # nothing new → allow push

# Get git diff to analyze file changes
diff_files = run(["git", "diff", "--name-only", f"{tag}..HEAD" if tag else "HEAD"])

# Build prompt for Claude
PROMPT = textwrap.dedent(f"""
You are a semantic versioning bot for a development project. Follow these rules EXACTLY:

Input:
- current_version = {current_ver}
- commit_messages = <<<EOF
{commits}
EOF
- changed_files = <<<EOF
{diff_files}
EOF

Rules:
- We are in development (0.x.x versioning)
- NEVER bump to 1.0.0 or higher

Minor bump (0.x.0 -> 0.x+1.0) when:
- feat: commit type
- New root-level folder added in concept_library/ (but NOT subfolders)
- New feature added to src/ directory (main CLI)

Patch bump (0.x.y -> 0.x.y+1) for:
- fix:, chore:, docs:, refactor:, test: commit types
- All other changes

Analysis steps:
1. Check if any changed files indicate a new root folder in concept_library/ (e.g., concept_library/new_concept/*)
2. Check if any changed files are new features in src/ (new commands, new utilities)
3. Look at commit types
4. Use the highest bump type if multiple criteria match

Output EXACTLY THREE lines:
bump:<minor|patch>
new_version:<calculated version>
changelog:<markdown bullet list of changes>
""").strip()

# Try Claude with cached credentials first
code, reply = call_claude(PROMPT)

# Fallback to API key if needed
if code != 0 and os.getenv("ANTHROPIC_API_KEY"):
    print("↻ Retrying with API key...")
    code, reply = call_claude(PROMPT, api_fallback=True)

if code != 0:
    print("⚠️ Claude unavailable – skipping version bump")
    sys.exit(0)  # don't block push

# Parse Claude's response
bump_type = ""
new_ver = ""
change_md = ""

for line in reply.splitlines():
    if line.startswith("bump:"):
        bump_type = line.split(":", 1)[1].strip()
    elif line.startswith("new_version:"):
        new_ver = line.split(":", 1)[1].strip()
    elif line.startswith("changelog:"):
        change_md = line.split(":", 1)[1].strip()

if not new_ver:
    print("⚠️ Invalid response from Claude")
    sys.exit(0)

print(f"► Bumping {current_ver} → {new_ver} ({bump_type})")

# Update version in pyproject.toml
VERSION_FILE.write_text(
    re.sub(r'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', f'version = "{new_ver}"', VERSION_FILE.read_text(), count=1)
)

# Update CHANGELOG.md
today = date.today().isoformat()
# Replace \n in change_md with actual newlines
formatted_changes = change_md.replace("\\n", "\n")
header = f"## [{new_ver}] - {today}\n{formatted_changes}\n\n"
changelog_content = CHANGELOG.read_text()
CHANGELOG.write_text(header + changelog_content)

# Check if files were modified
diff_exit = subprocess.call(["git", "diff", "--quiet"])
if diff_exit != 0:
    print("✗ Version bump & changelog updated.")
    print("  Please commit these changes and push again:")
    print("  git add pyproject.toml CHANGELOG.md")
    print(f'  git commit -m "chore(release): v{new_ver}"')
    sys.exit(1)  # stop push

print("✓ No version changes needed – push continues.")
sys.exit(0)
