#!/usr/bin/env python3
"""
Generate token usage statistics and conversation category reports.
Supports Claude Code (exact) and Cursor (estimated, characters / 4) sources.
Outputs a Markdown report with Mermaid pie charts (no extra packages required).

Usage:
  # Claude Code (exact)
  python3 generate_stats.py --projects ~/.claude/projects --days 7 --out report.md

  # Cursor (estimated)
  python3 generate_stats.py --cursor-projects ~/.cursor/projects --days 7 --out report.md
"""

import json
import re
import glob
import sqlite3
import argparse
import time
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta


def _load_tz():
    env_path = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "devtools-plugins", "export-chat-logs", ".env"
    )
    offset = 8  # Default UTC+8
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("TIMEZONE_OFFSET="):
                    offset = int(line.split("=", 1)[1].strip())
                    break
    except Exception:
        pass
    return timezone(timedelta(hours=offset)), offset


TZ_LOCAL, TZ_OFFSET = _load_tz()
TZ_LABEL = f"UTC{TZ_OFFSET:+d}"

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


# ── Claude Code ────────────────────────────────────────────────────────────────

def extract_session_stats(filepath):
    """Extract exact token usage from a Claude Code JSONL file."""
    title = None
    input_tokens = 0
    output_tokens = 0
    cache_tokens = 0
    first_messages = []
    first_ts = None
    last_ts = None

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if obj.get("type") == "custom-title":
                    t = obj.get("customTitle", "").strip()
                    if t:
                        title = t

                ts = obj.get("timestamp", "")
                if ts and first_ts is None:
                    first_ts = ts
                if ts:
                    last_ts = ts

                if obj.get("isMeta"):
                    continue

                msg = obj.get("message", {})
                role = msg.get("role", "")

                usage = msg.get("usage", {})
                if usage:
                    input_tokens  += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                    cache_tokens  += (usage.get("cache_read_input_tokens", 0)
                                    + usage.get("cache_creation_input_tokens", 0))

                if role in ("user", "assistant") and len(first_messages) < 6:
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        text = content.strip()
                    elif isinstance(content, list):
                        parts = [b.get("text", "") for b in content
                                 if isinstance(b, dict) and b.get("type") == "text"]
                        text = " ".join(parts).strip()
                    else:
                        text = ""
                    if text:
                        first_messages.append((role, text, ts))

    except Exception:
        pass

    return {
        "title":          title,
        "first_ts":       first_ts,
        "last_ts":        last_ts,
        "input_tokens":   input_tokens,
        "output_tokens":  output_tokens,
        "cache_tokens":   cache_tokens,
        "first_messages": first_messages,
        "estimated":      False,
    }


def find_recent_jsonl(projects_dir, days):
    cutoff = time.time() - days * 86400
    results = []
    if not Path(projects_dir).is_dir():
        return results
    for jsonl in Path(projects_dir).rglob("*.jsonl"):
        parts = set(jsonl.parts)
        if "subagents" in parts or "memory" in parts:
            continue
        try:
            if jsonl.stat().st_mtime >= cutoff:
                results.append(jsonl)
        except OSError:
            pass
    return results


# ── Cursor ─────────────────────────────────────────────────────────────────────

_composer_cache: dict = {}


def lookup_cursor_composer(composer_id):
    """Look up the name, creation time, models, and cost for a composerId from the Cursor vscdb.
    Returns (name, created_at_iso, models, cost_cents)."""
    if composer_id in _composer_cache:
        return _composer_cache[composer_id]
    name = None
    created_iso = None

    vscdb_pattern = str(Path.home() / "Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb")
    for db_path in glob.glob(vscdb_pattern):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT value FROM ItemTable WHERE key='composer.composerData'")
            row = cur.fetchone()
            conn.close()
            if not row:
                continue
            data = json.loads(row[0])
            for composer in data.get("allComposers", []):
                if composer.get("composerId") == composer_id:
                    name = composer.get("name", "").strip() or None
                    created_ms = composer.get("createdAt")
                    if created_ms:
                        dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
                        created_iso = dt.isoformat()
                    break
            if name is not None or created_iso is not None:
                break
        except Exception:
            pass

    models = []
    cost_cents = 0
    global_db = str(Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb")
    try:
        conn = sqlite3.connect(global_db)
        cur = conn.cursor()
        cur.execute("SELECT value FROM cursorDiskKV WHERE key=?", (f"composerData:{composer_id}",))
        row = cur.fetchone()
        conn.close()
        if row:
            data = json.loads(row[0])
            for model, stats in data.get("usageData", {}).items():
                models.append(model)
                cost_cents += stats.get("costInCents", 0)
    except Exception:
        pass

    result = name, created_iso, models, cost_cents
    _composer_cache[composer_id] = result
    return result


def extract_cursor_session_stats(filepath):
    """Estimate token usage from a Cursor JSONL file (characters / 4, split by user/assistant)."""
    composer_id = Path(filepath).stem
    title, created_iso, models, cost_cents = lookup_cursor_composer(composer_id)

    # If creation time not found in vscdb, use mtime
    if not created_iso:
        mtime = Path(filepath).stat().st_mtime
        created_iso = datetime.fromtimestamp(mtime, tz=TZ_LOCAL).isoformat()

    input_chars = 0   # user message character count
    output_chars = 0  # assistant message character count
    first_messages = []

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                role = obj.get("role", "")
                content = obj.get("message", {}).get("content", [])
                if isinstance(content, list):
                    text = " ".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                elif isinstance(content, str):
                    text = content
                else:
                    text = ""

                if role == "user":
                    input_chars += len(text)
                elif role == "assistant":
                    output_chars += len(text)

                if role in ("user", "assistant") and len(first_messages) < 6:
                    if text.strip():
                        first_messages.append((role, text[:300], ""))

    except Exception:
        pass

    return {
        "title":          title,
        "first_ts":       created_iso,
        "input_tokens":   input_chars // 4,
        "output_tokens":  output_chars // 4,
        "cache_tokens":   0,
        "first_messages": first_messages,
        "estimated":      True,
        "models":         models,
        "cost_cents":     cost_cents,
    }


def find_recent_cursor_jsonl(cursor_dir, days):
    cutoff = time.time() - days * 86400
    results = []
    base = Path(cursor_dir)
    if not base.is_dir():
        return results
    for jsonl in base.rglob("*.jsonl"):
        parts = jsonl.parts
        # Only include main JSONLs under agent-transcripts, not subagents
        if "agent-transcripts" not in parts:
            continue
        if "subagents" in parts:
            continue
        try:
            if jsonl.stat().st_mtime >= cutoff:
                results.append(jsonl)
        except OSError:
            pass
    return results


def find_cursor_sqlite_sessions(cursor_projects_dir, days):
    """Find Cursor sessions from workspaceStorage SQLite that have no agent-transcript JSONL."""
    cutoff_ms = (time.time() - days * 86400) * 1000
    base = Path(cursor_projects_dir)

    # Collect composer IDs that already have a JSONL to avoid double-counting
    known_ids = set()
    if base.is_dir():
        for jsonl in base.rglob("*.jsonl"):
            parts = jsonl.parts
            if "agent-transcripts" in parts and "subagents" not in parts:
                known_ids.add(jsonl.stem)

    sessions = []
    seen_ids = set()
    vscdb_pattern = str(
        Path.home() / "Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb"
    )
    for db_path in glob.glob(vscdb_pattern):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT value FROM ItemTable WHERE key='composer.composerData'")
            row = cur.fetchone()
            conn.close()
            if not row:
                continue
            data = json.loads(row[0])
            for composer in data.get("allComposers", []):
                cid = composer.get("composerId", "")
                if not cid or cid in known_ids or cid in seen_ids:
                    continue
                ts_ms = composer.get("lastUpdatedAt") or composer.get("createdAt") or 0
                if ts_ms < cutoff_ms:
                    continue
                name = (composer.get("name") or "").strip()
                if not name:
                    continue  # Skip unnamed conversations
                seen_ids.add(cid)
                subtitle = (composer.get("subtitle") or "").strip()
                dt_obj = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                sessions.append({
                    "title":            name,
                    "subtitle":         subtitle,
                    "first_ts":         dt_obj.isoformat(),
                    "input_tokens":     0,
                    "output_tokens":    0,
                    "cache_tokens":     0,
                    "first_messages":   [],
                    "estimated":        True,
                    "models":           [],
                    "cost_cents":       0,
                    "no_local_content": True,
                })
        except Exception:
            pass

    return sessions


# ── Report generation ──────────────────────────────────────────────────────────

def fmt(n):
    return f"{n:,}"


def mermaid_pie(title, data):
    lines = ["```mermaid", f"pie title {title}"]
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        if value > 0:
            lines.append(f'    "{label}" : {value}')
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


def generate_report(sessions, days, out_path, source_label, is_estimated=False):
    now_str    = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
    start_date = (datetime.now(TZ_LOCAL) - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date   = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d")
    est_note   = "(token counts are estimated: characters / 4)" if is_estimated else ""

    sessions.sort(key=lambda s: s["first_ts"] or "", reverse=True)

    # Separate sessions with content vs. SQLite metadata-only sessions
    content_sessions = [s for s in sessions if not s.get("no_local_content")]
    sqlite_sessions  = [s for s in sessions if s.get("no_local_content")]

    total_input  = sum(s["input_tokens"]  for s in sessions)
    total_output = sum(s["output_tokens"] for s in sessions)
    total_cache  = sum(s["cache_tokens"]  for s in sessions)
    total_all    = total_input + total_output
    total_cost_cents = sum(s.get("cost_cents", 0) for s in sessions)

    cat_input  = {}
    cat_output = {}
    cat_count  = {}
    for s in sessions:
        c = s["category"]
        cat_input[c]  = cat_input.get(c, 0)  + s["input_tokens"]
        cat_output[c] = cat_output.get(c, 0) + s["output_tokens"]
        cat_count[c]  = cat_count.get(c, 0)  + 1

    cat_total = {c: cat_input.get(c, 0) + cat_output.get(c, 0) for c in cat_count}

    # Token distribution only for sessions with content (used for token pie chart)
    cat_total_content = {}
    for s in content_sessions:
        c = s["category"]
        cat_total_content[c] = cat_total_content.get(c, 0) + s["input_tokens"] + s["output_tokens"]

    token_label = "estimated token *" if is_estimated else "token"
    pie_suffix  = " (estimated *)" if is_estimated else ""

    L = []
    L += [
        f"# {source_label} Token Usage Report", "",
        f"**Period:** {start_date} – {end_date} (last {days} days)",
        f"**Generated:** {now_str}",
        f"**Sessions:** {len(sessions)}",
    ]
    if sqlite_sessions:
        L.append(f"  *(includes {len(sqlite_sessions)} history-only sessions †, {len(content_sessions)} with full content)*")
    if is_estimated:
        L.append(f"\n> ⚠️ {est_note}")
    L += ["", "---", ""]

    # Summary
    L += [
        "## Summary", "",
        f"| Item | Count |",
        "|------|-----:|",
        f"| Input {token_label} | {fmt(total_input)} |",
        f"| Output {token_label} | {fmt(total_output)} |",
    ]
    if not is_estimated:
        L.append(f"| Cache tokens | {fmt(total_cache)} |")
    L.append(f"| **Total** | **{fmt(total_all)}** |")
    if total_cost_cents:
        L.append(f"| **Total cost** | **${total_cost_cents / 100:.2f}** |")
    L.append("")
    if total_all > 0:
        in_pct  = total_input  / total_all * 100
        out_pct = total_output / total_all * 100
        L.append(f"> Input {in_pct:.1f}% / Output {out_pct:.1f}%")
        L.append("")
    L += ["---", ""]

    # Conversation type distribution
    L += ["## Conversation Type Distribution", ""]
    L.append(mermaid_pie("Type (Sessions)", cat_count))
    L.append("")
    if total_all > 0:
        L.append(mermaid_pie(f"Tokens by Category{pie_suffix}", cat_total_content))
        L.append("")
    elif sqlite_sessions:
        L.append("> *Token pie chart: no token data available for content sessions, skipped.*")
        L.append("")

    if cat_count:
        L += [
            "<details>",
            "<summary>ASCII version (plain text)</summary>", "",
            "**Session Distribution**",
            ascii_bar(cat_count, len(sessions)),
            "",
        ]
        if total_all > 0:
            L += [
                f"**{token_label} Usage Distribution**",
                ascii_bar(cat_total, total_all),
                "",
            ]
        L += ["</details>", ""]

    # Category breakdown
    L += [
        "### Category Breakdown", "",
        f"| Category | Sessions | Input {token_label} | Output {token_label} | Total | Share |",
        "|------|:--------:|----------:|----------:|-----:|-----:|",
    ]
    for cat in sorted(cat_count, key=lambda c: -cat_count.get(c, 0)):
        ci  = cat_input.get(cat, 0)
        co  = cat_output.get(cat, 0)
        ct  = ci + co
        pct = ct / total_all * 100 if total_all else 0
        L.append(f"| {cat} | {cat_count[cat]} | {fmt(ci)} | {fmt(co)} | {fmt(ct)} | {pct:.1f}% |")
    L += ["", "---", ""]

    # Session details (content sessions only)
    has_model_col = any(s.get("models") for s in content_sessions)
    if content_sessions:
        if has_model_col:
            L += [
                "## Session Details", "",
                f"| Date/Time | Title | Category | Model | Cost | Input | Output | Total |",
                "|----------|------|------|------|-----:|-----:|-----:|-----:|",
            ]
        else:
            L += [
                "## Session Details", "",
                f"| Date/Time | Title | Category | Input | Output | Total |",
                "|----------|------|------|-----:|-----:|-----:|",
            ]
        for s in content_sessions:
            ts_str = ""
            if s["first_ts"]:
                try:
                    dt = datetime.fromisoformat(s["first_ts"].replace("Z", "+00:00")).astimezone(TZ_LOCAL)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_str = (s["first_ts"] or "")[:16]
            title_display = (s["title"] or "*(untitled)*")[:40]
            total_s = s["input_tokens"] + s["output_tokens"]
            if has_model_col:
                model_str = ", ".join(s.get("models") or []) or "-"
                cost_str = f"${s.get('cost_cents', 0) / 100:.2f}" if s.get("cost_cents") else "-"
                L.append(
                    f"| {ts_str} | {title_display} | {s['category']}"
                    f" | {model_str} | {cost_str}"
                    f" | {fmt(s['input_tokens'])} | {fmt(s['output_tokens'])} | {fmt(total_s)} |"
                )
            else:
                L.append(
                    f"| {ts_str} | {title_display} | {s['category']}"
                    f" | {fmt(s['input_tokens'])} | {fmt(s['output_tokens'])} | {fmt(total_s)} |"
                )
        L.append("")

    # Historical conversation list (SQLite metadata only)
    if sqlite_sessions:
        L += [
            "---", "",
            "## History-Only Sessions †", "",
            "> † These sessions have no local content (Cursor did not output agent-transcripts before this version). Metadata only.", "",
            "| Date/Time | Title | Category | Modified Files |",
            "|----------|------|------|---------|",
        ]
        for s in sqlite_sessions:
            ts_str = ""
            if s["first_ts"]:
                try:
                    dt = datetime.fromisoformat(s["first_ts"].replace("Z", "+00:00")).astimezone(TZ_LOCAL)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_str = (s["first_ts"] or "")[:16]
            title_display = (s["title"] or "*(untitled)*")[:50]
            subtitle_display = (s.get("subtitle") or "-")[:60]
            L.append(f"| {ts_str} | {title_display} | {s['category']} | {subtitle_display} |")
        L.append("")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(L), encoding="utf-8")
    est_tag = " (estimated)" if is_estimated else ""
    sqlite_tag = f" (+{len(sqlite_sessions)} history-only)" if sqlite_sessions else ""
    print(f"✅ {source_label} stats report{est_tag}: {len(sessions)} sessions{sqlite_tag}, total {fmt(total_all)} tokens → {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects",        help="Claude Code projects directory")
    parser.add_argument("--cursor-projects", help="Cursor projects directory")
    parser.add_argument("--days",  type=int, default=7)
    parser.add_argument("--out",   required=True)
    args = parser.parse_args()

    if args.cursor_projects:
        jsonl_files = find_recent_cursor_jsonl(args.cursor_projects, args.days)
        sessions = []
        for fp in jsonl_files:
            s = extract_cursor_session_stats(fp)
            s["category"] = categorize(s["title"], s["first_messages"])
            sessions.append(s)

        # Add historical sessions without agent-transcripts (SQLite metadata only)
        for s in find_cursor_sqlite_sessions(args.cursor_projects, args.days):
            s["category"] = categorize(
                f"{s['title'] or ''} {s.get('subtitle', '')}", []
            )
            sessions.append(s)

        if not sessions:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text("# Cursor Token Usage Report\n\n*(no sessions found)*\n", encoding="utf-8")
            print("⚠️  No Cursor sessions found, writing empty report.")
            return
        generate_report(sessions, args.days, args.out, "Cursor", is_estimated=True)

    elif args.projects:
        jsonl_files = find_recent_jsonl(args.projects, args.days)
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
        sessions = []
        for fp in jsonl_files:
            s = extract_session_stats(fp)
            active_ts = s["last_ts"] or s["first_ts"]
            if not active_ts:
                continue  # Skip empty sessions with no message timestamps
            try:
                dt = datetime.fromisoformat(active_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
                if dt < cutoff_dt:
                    continue  # last_ts out of range, skip (consistent with convert_to_markdown.py)
            except Exception:
                pass
            s["category"] = categorize(s["title"], s["first_messages"])
            sessions.append(s)
        if not sessions:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text("# Claude Code Token Usage Report\n\n*(no sessions found)*\n", encoding="utf-8")
            print("⚠️  No JSONL files found, writing empty report.")
            return
        generate_report(sessions, args.days, args.out, "Claude Code", is_estimated=False)

    else:
        print("Error: please provide --projects or --cursor-projects")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
