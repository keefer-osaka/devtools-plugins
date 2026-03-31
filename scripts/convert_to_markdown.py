#!/usr/bin/env python3
"""
Convert Claude Code JSONL chat logs to human-readable Markdown format.
Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--days N]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from datetime import datetime, timezone, timedelta
from common import S, TZ_LOCAL, TZ_LABEL, truncate, convert_claude_jsonl, make_output_path


def format_markdown(messages, first_ts, cwd=None, title=None, models=None, source_label=None):
    lines = []

    date_str = ""
    if first_ts:
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).astimezone(TZ_LOCAL)
            date_str = dt.strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
        except Exception:
            date_str = first_ts

    if source_label == "cowork":
        fallback_title = cwd.rstrip("/").split("/")[-1] if cwd else "Claude Cowork"
        display_title = title or fallback_title
        source_display = S["source_name_cowork"]
    else:
        display_title = title or "Claude Code"
        source_display = S["source_name"]
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
        ts_str = ""
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = f" · {dt.astimezone(TZ_LOCAL).strftime('%Y-%m-%d %H:%M')} {TZ_LABEL}"
            except Exception:
                pass
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


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--days N]")
        sys.exit(1)

    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    days_filter = None
    source_label = None

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days_filter = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if "--source-label" in sys.argv:
        idx = sys.argv.index("--source-label")
        if idx + 1 < len(sys.argv):
            source_label = sys.argv[idx + 1]

    messages, first_ts, last_ts, title, cwd, models = convert_claude_jsonl(input_path)

    if not first_ts:
        mtime = os.path.getmtime(input_path)
        dt_mtime = datetime.fromtimestamp(mtime, tz=TZ_LOCAL)
        first_ts = dt_mtime.isoformat()

    active_ts = last_ts or first_ts

    if days_filter is not None and active_ts:
        try:
            dt_check = datetime.fromisoformat(active_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
            if dt_check < cutoff:
                sys.exit(0)
        except Exception:
            pass

    md = format_markdown(messages, active_ts, cwd=cwd, title=title, models=models, source_label=source_label)

    os.makedirs(out_dir, exist_ok=True)
    output_path = make_output_path(out_dir, active_ts, title, ext=".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(S["msg_done_convert"].format(n=len(messages), path=output_path))


if __name__ == "__main__":
    main()
