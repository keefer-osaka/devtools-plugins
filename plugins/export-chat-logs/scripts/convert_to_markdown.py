#!/usr/bin/env python3
"""
Convert Claude Code JSONL chat logs to human-readable Markdown format.
Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--days N]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from common import S, truncate, safe_format_ts, resolve_display_title, converter_main


def format_markdown(messages, first_ts, cwd=None, title=None, models=None, source_label=None, first_user_message=""):
    lines = []

    date_str = safe_format_ts(first_ts) if first_ts else ""

    display_title, source_display = resolve_display_title(title, cwd, source_label, first_user_message)
    lines.append(f"# {display_title}")
    lines.append("")

    if date_str:
        lines.append(f"**{S['label_date']}:** {date_str}")
    if cwd:
        folder_name = Path(cwd).name or cwd
        lines.append(f"**{S['label_project']}:** {folder_name} (`{cwd}`)")
    lines.append(f"**{S['label_source']}:** {source_display}")
    if models:
        lines.append(f"**{S['label_model']}:** {', '.join(models)}")
    lines.append(f"**{S['label_messages']}:** {len(messages)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not messages:
        lines.append(S["no_messages"])
        return "\n".join(lines)

    for role, text, ts in messages:
        _ts = safe_format_ts(ts, fallback="") if ts else ""
        ts_str = f" · {_ts}" if _ts else ""
        if role == "user":
            lines.append(f"### {S['role_user']}{ts_str}")
        else:
            lines.append(f"### {S['role_assistant']}{ts_str}")
        lines.append("")
        lines.append(truncate(text))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    converter_main(format_markdown, ".md")
