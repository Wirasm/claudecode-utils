"""Lightweight data collectors for git commits and GitHub pull requests.

Falls back gracefully if PyGithub token not available.
"""

from __future__ import annotations

import datetime as dt
import os

from git import InvalidGitRepositoryError, Repo

CommitsT = list[dict[str, str]]
PRsT = list[dict[str, str]]


def collect_commits(since_iso: str) -> CommitsT:
    try:
        repo = Repo(".")
    except InvalidGitRepositoryError as exc:
        raise RuntimeError("Not inside a git repository.") from exc

    revs = repo.iter_commits("--all", since=since_iso)
    commits = [
        dict(
            hash=c.hexsha[:7],
            author=c.author.name,
            date=c.committed_datetime.date().isoformat(),
            msg=c.message.strip().replace("\n", " "),
        )
        for c in revs
    ]
    return commits


def collect_prs(since_datetime: dt.datetime) -> PRsT:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return []

    try:
        from github import Github  # lazy import to avoid requirement if unused
    except ImportError:
        return []

    gh = Github(token)
    user = gh.get_user()
    prs = user.get_pulls(state="all", sort="updated", direction="desc")
    recent = [
        dict(
            id=pr.number,
            title=pr.title,
            state=pr.state,
            updated=pr.updated_at.date().isoformat(),
        )
        for pr in prs
        if pr.updated_at >= since_datetime
    ]
    return recent
