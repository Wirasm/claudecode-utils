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
Turn the JSON that follows into Markdown with three sections following excellent standup report practices:
**Yesterday**, **Today**, **Blockers**.

JSON:
{json.dumps(payload, indent=2, ensure_ascii=False)}
"""


def preview(markdown: str) -> None:
    console.rule("[bold green]Stand-up preview")
    console.print(Markdown(markdown))
    console.rule()
