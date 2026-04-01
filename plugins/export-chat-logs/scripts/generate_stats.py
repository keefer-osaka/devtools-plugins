#!/usr/bin/env python3
"""
Generate token usage statistics and conversation category reports for Claude Code.
Outputs a Markdown or HTML report (no extra packages required).

Usage:
  python3 generate_stats.py --projects ~/.claude/projects --days 7 --out report.md [--format md|html]
"""

import json
import argparse
import html as _html
import time
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from datetime import datetime, timezone, timedelta
from common import S, LANG_CODE, TZ_LOCAL, TZ_LABEL, make_output_path, parse_ts, compute_active_duration, parse_session, is_trivial_stats

# Category keywords (matched against title + first few user messages)
CATEGORIES = {
    "Coding": [
        "code", "function", "implement", "class", "feature", "create", "build",
        "write", "add", "api", "endpoint", "component", "module", "script",
    ],
    "Debugging": [
        "debug", "error", "bug", "fix", "issue", "broken", "fail", "crash",
        "not work", "wrong", "problem", "traceback", "exception",
    ],
    "Config": [
        "config", "setup", "install", "hook", "setting", "env", "configure",
        "deploy", "docker", "ci", "cd", "pipeline", "workflow",
    ],
    "Docs": [
        "explain", "document", "readme", "comment", "how", "what", "why",
        "describe", "summary", "help", "guide",
    ],
    "Refactoring": [
        "refactor", "optimize", "improve", "clean", "restructure", "performance",
        "simplify", "reorganize",
    ],
}


def categorize(title, first_messages):
    text = (title or "").lower()
    for role, content, _ in first_messages[:5]:
        if role == "user":
            text += " " + content[:300].lower()

    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"



def find_recent_jsonl(projects_dir, days):
    cutoff = time.time() - days * 86400
    results = []
    if not Path(projects_dir).is_dir():
        return results
    for jsonl in Path(projects_dir).rglob("*.jsonl"):
        if jsonl.name == "audit.jsonl":
            continue
        parts = set(jsonl.parts)
        if "subagents" in parts or "memory" in parts:
            continue
        try:
            if jsonl.stat().st_mtime >= cutoff:
                results.append(jsonl)
        except OSError:
            pass
    return results


# ── Link helpers ───────────────────────────────────────────────────────────────

def _compute_conv_link(s, conv_base, report_path):
    """Return relative URL from stats report to conversation HTML, or None."""
    active_ts = s.get("last_ts") or s.get("first_ts")
    filepath  = s.get("filepath")
    if not active_ts or not filepath or not conv_base:
        return None

    claude_projects = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if str(filepath).startswith(claude_projects):
        # Normal Claude Code path: derive project_display from filesystem path
        project_dir  = Path(filepath).parent.name
        home_encoded = os.path.expanduser("~").replace("/", "-")
        if project_dir.startswith(home_encoded + "-"):
            project_display = project_dir[len(home_encoded) + 1:]
        elif project_dir == home_encoded:
            project_display = ""
        else:
            project_display = project_dir
    else:
        # Cowork path: derive project_display from virtual cwd last segment
        cwd = s.get("cwd", "")
        project_display = cwd.rstrip("/").split("/")[-1] if cwd else Path(filepath).parent.name

    fname = os.path.basename(make_output_path(".", active_ts, s.get("title"), ext=".html"))
    if project_display:
        target = os.path.join(conv_base, project_display, fname)
    else:
        target = os.path.join(conv_base, fname)
    if not os.path.exists(target):
        return None
    return os.path.relpath(target, os.path.dirname(report_path))


# ── Shared helpers ─────────────────────────────────────────────────────────────

def fmt(n):
    return f"{n:,}"


def fmt_duration(seconds):
    if seconds < 60:
        return "< 1m"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def _compute_stats(sessions):
    """Compute aggregated stats dict from session list."""
    total_input    = sum(s["input_tokens"]  for s in sessions)
    total_output   = sum(s["output_tokens"] for s in sessions)
    total_cache_read   = sum(s.get("cache_read", 0)     for s in sessions)
    total_cache_creation = sum(s.get("cache_creation", 0) for s in sessions)
    total_all      = total_input + total_output

    cat_input  = {}
    cat_output = {}
    cat_count  = {}
    tool_totals   = {}
    proj_tokens   = {}
    proj_sessions = {}
    model_sessions = {}

    for s in sessions:
        c = s["category"]
        cat_input[c]  = cat_input.get(c, 0)  + s["input_tokens"]
        cat_output[c] = cat_output.get(c, 0) + s["output_tokens"]
        cat_count[c]  = cat_count.get(c, 0)  + 1

        for tool, cnt in (s.get("tool_counts") or {}).items():
            tool_totals[tool] = tool_totals.get(tool, 0) + cnt

        proj = s.get("project") or "Unknown"
        proj_tokens[proj]   = proj_tokens.get(proj, 0) + s["input_tokens"] + s["output_tokens"]
        proj_sessions[proj] = proj_sessions.get(proj, 0) + 1

        for model in (s.get("models") or []):
            model_sessions[model] = model_sessions.get(model, 0) + 1

    cat_total = {c: cat_input.get(c, 0) + cat_output.get(c, 0) for c in cat_count}
    return {
        "total_input": total_input, "total_output": total_output,
        "total_all": total_all,
        "total_cache_read": total_cache_read,
        "total_cache_creation": total_cache_creation,
        "cat_input": cat_input, "cat_output": cat_output,
        "cat_count": cat_count, "cat_total": cat_total,
        "tool_totals": tool_totals,
        "proj_tokens": proj_tokens, "proj_sessions": proj_sessions,
        "model_sessions": model_sessions,
    }


# ── Markdown report ────────────────────────────────────────────────────────────

def _mermaid_label(s):
    """Sanitize a label for use in Mermaid pie charts (remove angle brackets)."""
    return s.replace("<", "(").replace(">", ")")


def mermaid_pie(title, data):
    lines = ["```mermaid", f"pie title {title}"]
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        if value > 0:
            lines.append(f'    "{_mermaid_label(label)}" : {value}')
    lines.append("```")
    return "\n".join(lines)


def ascii_bar(data, total, width=24):
    lines = []
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        if value == 0:
            continue
        pct = value / total * 100 if total else 0
        bar_len = int(pct / 100 * width)
        bar = "█" * bar_len + "░" * (width - bar_len)
        lines.append(f"`{bar}` {pct:5.1f}%  {label}")
    return "\n".join(lines)


def generate_report(sessions, days, out_path, skipped=0, source_label=None):
    now_str    = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
    start_date = (datetime.now(TZ_LOCAL) - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date   = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d")

    sessions.sort(key=lambda s: s["first_ts"] or "", reverse=True)
    d = _compute_stats(sessions)
    total_input, total_output, total_all = (
        d["total_input"], d["total_output"], d["total_all"])
    total_cache_read, total_cache_creation = d["total_cache_read"], d["total_cache_creation"]
    cat_input, cat_output, cat_count, cat_total = (
        d["cat_input"], d["cat_output"], d["cat_count"], d["cat_total"])
    tool_totals    = d["tool_totals"]
    proj_tokens    = d["proj_tokens"]
    proj_sessions  = d["proj_sessions"]
    model_sessions = d["model_sessions"]

    report_title = S["report_title_cowork"] if source_label == "cowork" else S["report_title"]

    L = []
    L += [
        f"# {report_title}", "",
        f"**{S['label_period']}:** {start_date} – {end_date} (last {days} days)",
        f"**{S['label_generated']}:** {now_str}",
        f"**{S['label_sessions']}:** {len(sessions)}"
        + (f"  {S['skipped_sessions'].format(n=skipped)}" if skipped else ""),
        "", "---", "",
    ]

    # Summary
    total_cache_all = total_cache_read + total_cache_creation
    hit_rate_str = (
        f"{total_cache_read / total_cache_all * 100:.1f}% "
        f"(read: {fmt(total_cache_read)} / total: {fmt(total_cache_all)})"
        if total_cache_all > 0 else "N/A"
    )
    L += [
        f"## {S['section_summary']}", "",
        f"| {S['col_item']} | {S['col_count']} |",
        "|------|-----:|",
        f"| {S['row_input']} | {fmt(total_input)} |",
        f"| {S['row_output']} | {fmt(total_output)} |",
        f"| {S['row_cache_read']} | {fmt(total_cache_read)} |",
        f"| {S['row_cache_creation']} | {fmt(total_cache_creation)} |",
        f"| **{S['row_total']}** | **{fmt(total_all)}** |",
        f"| {S['row_cache_hit_rate']} | {hit_rate_str} |",
        "",
    ]
    if total_all > 0:
        in_pct  = total_input  / total_all * 100
        out_pct = total_output / total_all * 100
        L.append(f"> {S['summary_ratio'].format(in_pct=in_pct, out_pct=out_pct)}")
        L.append("")
    L += ["---", ""]

    # Conversation type distribution
    L += [f"## {S['section_type_dist']}", ""]
    L.append(mermaid_pie(S["pie_type_sessions"], cat_count))
    L.append("")
    if total_all > 0:
        cat_total_display = {S.get(f"cat_{k}", k): v for k, v in cat_total.items()}
        L.append(mermaid_pie(S["pie_tokens_by_cat"], cat_total_display))
        L.append("")

    if cat_count:
        cat_count_display = {S.get(f"cat_{k}", k): v for k, v in cat_count.items()}
        L += [
            "<details>",
            f"<summary>{S['ascii_label']}</summary>", "",
            S["ascii_session_dist"],
            ascii_bar(cat_count_display, len(sessions)),
            "",
        ]
        if total_all > 0:
            L += [
                S["ascii_token_dist"],
                ascii_bar(cat_total_display, total_all),
                "",
            ]
        L += ["</details>", ""]

    # Category breakdown
    L += [
        f"### {S['section_cat_breakdown']}", "",
        f"| {S['col_category']} | {S['col_sessions']} | {S['col_input']} | {S['col_output']} | {S['col_total']} | {S['col_share']} |",
        "|------|:--------:|----------:|----------:|-----:|-----:|",
    ]
    for cat in sorted(cat_count, key=lambda c: -cat_count.get(c, 0)):
        ci  = cat_input.get(cat, 0)
        co  = cat_output.get(cat, 0)
        ct  = ci + co
        pct = ct / total_all * 100 if total_all else 0
        cat_disp = S.get(f"cat_{cat}", cat)
        L.append(f"| {cat_disp} | {cat_count[cat]} | {fmt(ci)} | {fmt(co)} | {fmt(ct)} | {pct:.1f}% |")
    L += ["", "---", ""]

    # Tool usage
    if tool_totals:
        total_tool_calls = sum(tool_totals.values())
        top_tools = sorted(tool_totals.items(), key=lambda x: -x[1])[:8]
        other_calls = total_tool_calls - sum(v for _, v in top_tools)
        pie_data = dict(top_tools)
        if other_calls > 0:
            pie_data["Other"] = other_calls
        L += [f"## {S['section_tool_usage']}", ""]
        L.append(mermaid_pie(S["section_tool_usage"], pie_data))
        L.append("")
        L += [
            f"| {S['col_tool_name']} | {S['col_tool_calls']} | {S['col_share']} |",
            "|------|-----:|-----:|",
        ]
        for tool, cnt in sorted(tool_totals.items(), key=lambda x: -x[1]):
            pct = cnt / total_tool_calls * 100 if total_tool_calls else 0
            L.append(f"| {tool} | {fmt(cnt)} | {pct:.1f}% |")
        L += ["", "---", ""]

    # Project breakdown
    if proj_tokens:
        total_proj_tokens = sum(proj_tokens.values())
        top_projs = sorted(proj_tokens.items(), key=lambda x: -x[1])[:8]
        other_proj = total_proj_tokens - sum(v for _, v in top_projs)
        pie_proj = dict(top_projs)
        if other_proj > 0:
            pie_proj["Other"] = other_proj
        L += [f"## {S['section_project_breakdown']}", ""]
        L.append(mermaid_pie(S["section_project_breakdown"], pie_proj))
        L.append("")
        L += [
            f"| {S['col_project']} | {S['col_sessions']} | {S['col_total']} | {S['col_share']} |",
            "|------|:------:|-----:|-----:|",
        ]
        for proj in sorted(proj_tokens, key=lambda p: -proj_tokens[p]):
            pt  = proj_tokens[proj]
            ps  = proj_sessions.get(proj, 0)
            pct = pt / total_proj_tokens * 100 if total_proj_tokens else 0
            L.append(f"| {proj} | {ps} | {fmt(pt)} | {pct:.1f}% |")
        L += ["", "---", ""]

    # Model usage
    if model_sessions:
        total_model_sess = sum(model_sessions.values())
        L += [f"## {S['section_model_usage']}", ""]
        L.append(mermaid_pie(S["section_model_usage"], model_sessions))
        L.append("")
        L += [
            f"| {S['col_model']} | {S['col_sessions']} | {S['col_share']} |",
            "|------|:------:|-----:|",
        ]
        for model in sorted(model_sessions, key=lambda m: -model_sessions[m]):
            ms  = model_sessions[model]
            pct = ms / total_model_sess * 100 if total_model_sess else 0
            L.append(f"| {model} | {ms} | {pct:.1f}% |")
        L += ["", "---", ""]

    # Session details
    has_model_col = any(s.get("models") for s in sessions)
    if sessions:
        header_cols = [S["col_datetime"], S["col_title"], S["col_category"]]
        sep_cols    = ["----------", "------", "------"]
        if has_model_col:
            header_cols.append(S["col_model"])
            sep_cols.append("------")
        header_cols.append(S["col_duration"])
        sep_cols.append("------:")
        header_cols += [S["col_input"], S["col_output"], S["col_total"]]
        sep_cols    += ["-----:", "-----:", "-----:"]

        L += [
            f"## {S['section_session_details']}", "",
            "| " + " | ".join(header_cols) + " |",
            "|" + "|".join(sep_cols) + "|",
        ]
        for s in sessions:
            ts_str = ""
            if s["first_ts"]:
                try:
                    ts_str = parse_ts(s["first_ts"]).astimezone(TZ_LOCAL).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_str = (s["first_ts"] or "")[:16]
            title_display = (s["title"] or S["untitled"])[:40]
            total_s   = s["input_tokens"] + s["output_tokens"]
            cat_disp  = S.get(f"cat_{s['category']}", s['category'])
            dur_str   = fmt_duration(s["duration"]) if s.get("duration") is not None else "-"
            cells = [ts_str, title_display, cat_disp]
            if has_model_col:
                cells.append(", ".join(s.get("models") or []) or "-")
            cells += [dur_str, fmt(s["input_tokens"]), fmt(s["output_tokens"]), fmt(total_s)]
            L.append("| " + " | ".join(cells) + " |")
        L.append("")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(L), encoding="utf-8")
    msg_key = "msg_stats_done_cowork" if source_label == "cowork" else "msg_stats_done"
    print(S[msg_key].format(sessions=len(sessions), tokens=fmt(total_all), path=out_path))


# ── HTML report ────────────────────────────────────────────────────────────────

_CHART_COLORS = [
    "#4c9be8", "#57c17e", "#f0a445", "#e06b6b", "#9b8ae8",
    "#4ecdc4", "#f7a072", "#c47eb5", "#a8d8b9", "#f4d35e",
]

_STATS_CSS = """
:root {
  --bg: #ffffff; --bg-alt: #f6f8fa; --border: #d0d7de;
  --text: #1f2328; --text-muted: #656d76;
  --link: #0969da; --th-bg: #f6f8fa;
  --accent: #0969da;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117; --bg-alt: #161b22; --border: #30363d;
    --text: #e6edf3; --text-muted: #8b949e;
    --link: #388bfd; --th-bg: #161b22;
    --accent: #388bfd;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 14px; line-height: 1.6;
  color: var(--text); background: var(--bg);
}
.container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid var(--border); }
header h1 { font-size: 22px; font-weight: 700; margin-bottom: 10px; }
.meta { display: flex; flex-wrap: wrap; gap: 4px 20px; font-size: 13px; color: var(--text-muted); }
.meta b { color: var(--text); font-weight: 500; }
.section { margin: 24px 0; }
.section h2 {
  font-size: 18px; font-weight: 600;
  padding-bottom: 8px; margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.section h3 { font-size: 15px; font-weight: 600; margin: 16px 0 10px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
th {
  background: var(--th-bg); font-weight: 600;
  text-align: left; padding: 8px 12px;
  border: 1px solid var(--border);
}
td { padding: 6px 12px; border: 1px solid var(--border); }
tr:nth-child(even) td { background: var(--bg-alt); }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.charts { display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; margin: 16px 0; }
.chart-box { flex: 1; min-width: 280px; max-width: 460px; }
details { margin: 8px 0; }
summary {
  cursor: pointer; padding: 6px 0;
  color: var(--text-muted); font-size: 13px;
  user-select: none;
}
summary:hover { color: var(--text); }
details pre {
  background: var(--bg-alt); padding: 12px; border-radius: 6px;
  font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 12px; overflow-x: auto; margin-top: 8px;
  border: 1px solid var(--border);
}
blockquote {
  border-left: 3px solid var(--accent);
  padding: 6px 14px; margin: 8px 0;
  color: var(--text-muted); background: var(--bg-alt);
  border-radius: 0 4px 4px 0; font-size: 13px;
}
a.conv-link { color: var(--link); text-decoration: none; }
a.conv-link:hover { text-decoration: underline; }
.bar-chart { width: 100%; margin: 12px 0; }
.bar-row { display: flex; align-items: center; gap: 8px; margin: 5px 0; font-size: 13px; }
.bar-label { flex: 0 0 220px; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text); }
.bar-track { flex: 1; background: var(--bg-alt); border-radius: 3px; height: 16px; border: 1px solid var(--border); }
.bar-fill { height: 100%; border-radius: 3px; min-width: 2px; }
.bar-pct { flex: 0 0 42px; text-align: right; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.bar-val { flex: 0 0 64px; text-align: right; color: var(--text-muted); font-variant-numeric: tabular-nums; }
"""


def _html_table(headers, rows, col_classes=None):
    """Generate an HTML table. col_classes: list of CSS class strings per column."""
    if col_classes is None:
        col_classes = [""] * len(headers)
    th_cells = "".join(
        f'<th class="{c}">{_html.escape(str(h))}</th>'
        for h, c in zip(headers, col_classes)
    )
    row_parts = []
    for row in rows:
        td_cells = "".join(
            f'<td class="{c}">{_html.escape(str(v))}</td>'
            for v, c in zip(row, col_classes)
        )
        row_parts.append(f"<tr>{td_cells}</tr>")
    return (
        f"<table><thead><tr>{th_cells}</tr></thead>"
        f"<tbody>{''.join(row_parts)}</tbody></table>"
    )


def _bar_chart_html(data, total, show_count=True):
    """Generate a horizontal bar chart as HTML."""
    rows = sorted(data.items(), key=lambda x: -x[1])
    parts = ['<div class="bar-chart">']
    for i, (label, value) in enumerate(rows):
        pct = value / total * 100 if total else 0
        color = _CHART_COLORS[i % len(_CHART_COLORS)]
        val_cell = f'<span class="bar-val">{fmt(value)}</span>' if show_count else ""
        parts.append(
            f'<div class="bar-row">'
            f'<span class="bar-label" title="{_html.escape(label)}">{_html.escape(label)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<span class="bar-pct">{pct:.1f}%</span>'
            f'{val_cell}'
            f'</div>'
        )
    parts.append('</div>')
    return "\n".join(parts)


def generate_html_report(sessions, days, out_path, conv_base=None, skipped=0, source_label=None):
    now_str    = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
    start_date = (datetime.now(TZ_LOCAL) - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date   = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d")
    lang_attr  = LANG_CODE

    sessions.sort(key=lambda s: s["first_ts"] or "", reverse=True)
    d = _compute_stats(sessions)
    total_input, total_output, total_all = (
        d["total_input"], d["total_output"], d["total_all"])
    total_cache_read, total_cache_creation = d["total_cache_read"], d["total_cache_creation"]
    cat_input, cat_output, cat_count, cat_total = (
        d["cat_input"], d["cat_output"], d["cat_count"], d["cat_total"])
    tool_totals    = d["tool_totals"]
    proj_tokens    = d["proj_tokens"]
    proj_sessions  = d["proj_sessions"]
    model_sessions = d["model_sessions"]

    report_title = S["report_title_cowork"] if source_label == "cowork" else S["report_title"]
    title_esc = _html.escape(report_title)
    parts = []

    # Header
    parts.append(
        f'<header>'
        f'<h1>{title_esc}</h1>'
        f'<div class="meta">'
        f'<span>{_html.escape(S["label_period"])}: <b>{_html.escape(start_date)} – {_html.escape(end_date)} (last {days} days)</b></span>'
        f'<span>{_html.escape(S["label_generated"])}: <b>{_html.escape(now_str)}</b></span>'
        f'<span>{_html.escape(S["label_sessions"])}: <b>{len(sessions)}</b></span>'
        + (f'<span style="color:var(--text-muted)">{_html.escape(S["skipped_sessions"].format(n=skipped))}</span>' if skipped else "")
        + '</div></header>'
    )

    # Summary section
    total_cache_all = total_cache_read + total_cache_creation
    hit_rate_str = (
        f"{total_cache_read / total_cache_all * 100:.1f}% "
        f"(read: {fmt(total_cache_read)} / total: {fmt(total_cache_all)})"
        if total_cache_all > 0 else "N/A"
    )
    summary_rows = [
        [S["row_input"],          fmt(total_input)],
        [S["row_output"],         fmt(total_output)],
        [S["row_cache_read"],     fmt(total_cache_read)],
        [S["row_cache_creation"], fmt(total_cache_creation)],
        [S["row_total"],          fmt(total_all)],
        [S["row_cache_hit_rate"], hit_rate_str],
    ]
    summary_table = _html_table(
        [S["col_item"], S["col_count"]],
        summary_rows,
        col_classes=["", "num"],
    )
    ratio_html = ""
    if total_all > 0:
        in_pct  = total_input  / total_all * 100
        out_pct = total_output / total_all * 100
        ratio_text = S["summary_ratio"].format(in_pct=in_pct, out_pct=out_pct)
        ratio_html = f"<blockquote>{_html.escape(ratio_text)}</blockquote>"

    parts.append(
        f'<div class="section">'
        f'<h2>{_html.escape(S["section_summary"])}</h2>'
        f'{summary_table}'
        f'{ratio_html}'
        f'</div>'
    )

    # Type distribution section
    cat_count_display = {S.get(f"cat_{k}", k): v for k, v in cat_count.items()}
    cat_total_display = {S.get(f"cat_{k}", k): v for k, v in cat_total.items()}

    type_charts = _bar_chart_html(cat_count_display, len(sessions))
    if total_all > 0:
        type_charts += f'<h3 style="margin:16px 0 8px;font-size:14px;font-weight:600;color:var(--text-muted)">{_html.escape(S["pie_tokens_by_cat"])}</h3>'
        type_charts += _bar_chart_html(cat_total_display, total_all)

    parts.append(
        f'<div class="section">'
        f'<h2>{_html.escape(S["section_type_dist"])}</h2>'
        f'{type_charts}'
        f'</div>'
    )

    # Tool usage section
    if tool_totals:
        total_tool_calls = sum(tool_totals.values())
        parts.append(
            f'<div class="section">'
            f'<h2>{_html.escape(S["section_tool_usage"])}</h2>'
            f'{_bar_chart_html(tool_totals, total_tool_calls)}'
            f'</div>'
        )

    # Project breakdown section
    if proj_tokens:
        total_proj_tokens = sum(proj_tokens.values())
        parts.append(
            f'<div class="section">'
            f'<h2>{_html.escape(S["section_project_breakdown"])}</h2>'
            f'{_bar_chart_html(proj_tokens, total_proj_tokens)}'
            f'</div>'
        )

    # Model usage section
    if model_sessions:
        total_model_sess = sum(model_sessions.values())
        parts.append(
            f'<div class="section">'
            f'<h2>{_html.escape(S["section_model_usage"])}</h2>'
            f'{_bar_chart_html(model_sessions, total_model_sess)}'
            f'</div>'
        )

    # Session details
    if sessions:
        has_model_col = any(s.get("models") for s in sessions)
        sess_headers = [S["col_datetime"], S["col_title"], S["col_category"]]
        sess_classes = ["", "", ""]
        if has_model_col:
            sess_headers.append(S["col_model"])
            sess_classes.append("")
        sess_headers.append(S["col_duration"])
        sess_classes.append("num")
        sess_headers += [S["col_input"], S["col_output"], S["col_total"]]
        sess_classes += ["num", "num", "num"]

        sess_rows_html = []
        for s in sessions:
            ts_str = ""
            if s["first_ts"]:
                try:
                    ts_str = parse_ts(s["first_ts"]).astimezone(TZ_LOCAL).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_str = (s["first_ts"] or "")[:16]
            title_text = (s["title"] or S["untitled"])[:40]
            total_s   = s["input_tokens"] + s["output_tokens"]
            cat_disp  = S.get(f"cat_{s['category']}", s['category'])
            dur_str   = fmt_duration(s["duration"]) if s.get("duration") is not None else "-"

            link = _compute_conv_link(s, conv_base, out_path)
            if link:
                title_cell = (
                    f'<td><a class="conv-link" href="{_html.escape(link)}" target="_blank">'
                    f'{_html.escape(title_text)} ↗</a></td>'
                )
            else:
                title_cell = f'<td>{_html.escape(title_text)}</td>'

            cells = [
                f'<td>{_html.escape(ts_str)}</td>',
                title_cell,
                f'<td>{_html.escape(cat_disp)}</td>',
            ]
            if has_model_col:
                cells.append(f'<td>{_html.escape(", ".join(s.get("models") or []) or "-")}</td>')
            cells += [
                f'<td class="num">{_html.escape(dur_str)}</td>',
                f'<td class="num">{fmt(s["input_tokens"])}</td>',
                f'<td class="num">{fmt(s["output_tokens"])}</td>',
                f'<td class="num">{fmt(total_s)}</td>',
            ]
            sess_rows_html.append(f"<tr>{''.join(cells)}</tr>")

        th_cells = "".join(
            f'<th class="{c}">{_html.escape(str(h))}</th>'
            for h, c in zip(sess_headers, sess_classes)
        )
        sess_table = (
            f"<table><thead><tr>{th_cells}</tr></thead>"
            f"<tbody>{''.join(sess_rows_html)}</tbody></table>"
        )
        parts.append(
            f'<div class="section">'
            f'<h2>{_html.escape(S["section_session_details"])}</h2>'
            f'{sess_table}'
            f'</div>'
        )

    body = "\n".join(parts)
    html_doc = f"""<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_esc}</title>
  <style>{_STATS_CSS}</style>
</head>
<body>
  <div class="container">
    {body}
  </div>
</body>
</html>"""

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html_doc, encoding="utf-8")
    msg_key = "msg_stats_done_cowork" if source_label == "cowork" else "msg_stats_done"
    print(S[msg_key].format(sessions=len(sessions), tokens=fmt(total_all), path=out_path))


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", action="append", required=True,
                        help="Projects directory (may be specified multiple times)")
    parser.add_argument("--days",   type=int, default=7)
    parser.add_argument("--out",    required=True)
    parser.add_argument("--format", choices=["md", "html"], default="md", dest="fmt")
    parser.add_argument("--conv-base", default=None,
                        help="Base directory of conversation HTML files (for linking)")
    parser.add_argument("--source-label", default=None, choices=["cowork"],
                        help="Label for report title/output message (omit for Claude Code)")
    args = parser.parse_args()

    jsonl_files = []
    for proj_dir in args.projects:
        jsonl_files.extend(find_recent_jsonl(proj_dir, args.days))

    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    sessions = []
    skipped = 0
    for fp in jsonl_files:
        s = parse_session(fp)
        active_ts = s["last_ts"] or s["first_ts"]
        if not active_ts:
            continue
        try:
            dt = parse_ts(active_ts).astimezone(timezone.utc)
            if dt < cutoff_dt:
                continue
        except Exception:
            pass
        s["category"] = categorize(s["title"], s["messages"][:6])
        s["filepath"] = str(fp)

        # Duration: sum only consecutive gaps <= 30 min (active time, excludes resume breaks)
        try:
            tss = s.get("msg_timestamps") or []
            if len(tss) >= 2:
                s["duration"] = compute_active_duration(tss)
            elif s["first_ts"] and s["last_ts"]:
                diff = (parse_ts(s["last_ts"]) - parse_ts(s["first_ts"])).total_seconds()
                s["duration"] = diff if diff <= 1800 else None
            else:
                s["duration"] = None
        except Exception:
            s["duration"] = None

        # Project name from cwd
        cwd_val = s.get("cwd") or ""
        s["project"] = cwd_val.rstrip("/").split("/")[-1] if cwd_val else "Unknown"

        if is_trivial_stats(s["output_tokens"], s["input_tokens"] + s["output_tokens"], s.get("duration")):
            skipped += 1
            continue

        sessions.append(s)

    if not sessions:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        if args.fmt == "html":
            empty_html = (
                f'<!DOCTYPE html><html lang="{LANG_CODE}"><head><meta charset="UTF-8">'
                f'<title>{_html.escape(S["report_title"])}</title></head>'
                f'<body><p>{_html.escape(S["no_sessions_found"])}</p></body></html>'
            )
            Path(args.out).write_text(empty_html, encoding="utf-8")
        else:
            Path(args.out).write_text(f"# {S['report_title']}\n\n{S['no_sessions_found']}\n", encoding="utf-8")
        print(S["warn_no_files"])
        return

    if args.fmt == "html":
        generate_html_report(sessions, args.days, args.out, conv_base=args.conv_base, skipped=skipped, source_label=args.source_label)
    else:
        generate_report(sessions, args.days, args.out, skipped=skipped, source_label=args.source_label)


if __name__ == "__main__":
    main()
