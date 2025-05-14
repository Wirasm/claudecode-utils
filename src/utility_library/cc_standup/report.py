"""
Prompt builder + Rich helpers.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List

from rich.console import Console
from rich.markdown import Markdown

console = Console()


def build_prompt(commits: List[Dict[str, str]], prs: List[Dict[str, str]]) -> str:
    today = dt.date.today().isoformat()
    payload: Dict[str, Any] = {"commits": commits, "prs": prs}

    return f"""You are an scrum standup assistant preparing a stand-up report for **{today}**.
Your task is to IMMEDIATELY generate a Markdown document with three sections based on the provided JSON data:
**Yesterday**, **Today**, **Blockers**. Do not wait for user confirmation before generating the report.

Create a well-formatted Markdown document with the following characteristics:
1. Use headers (##) for the main sections (Yesterday, Today, Blockers)
2. Group related commits by topic when possible
3. Use bullet points for individual items
4. Highlight important achievements or milestones
5. Keep it concise but informative
6. DO NOT INCLUDE ANY MESSAGES ASKING FOR USER CONFIRMATION

Here is the JSON data to use for generating the report:
{json.dumps(payload, indent=2, ensure_ascii=False)}
"""


def preview(markdown: str) -> None:
    console.rule("[bold green]Stand-up preview")
    console.print(Markdown(markdown))
    console.rule()
