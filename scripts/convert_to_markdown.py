#!/usr/bin/env python3
"""
Convert Claude Code and Cursor JSONL chat logs to human-readable Markdown format.
Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--source claude|cursor] [--cwd PATH]
"""

import json
import re
import sys
import os
import glob
import sqlite3
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

MAX_MSG_LEN = 3000  # Max characters to display per message


def truncate(text, max_len=MAX_MSG_LEN):
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n... *({len(text) - max_len} characters omitted)*"


def clean_string_content(text):
    """Clean string message content: strip control characters, simplify slash command XML, clean Cursor XML tags."""
    # Strip control characters
    text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text).strip()

    # <local-command-stdout>...</local-command-stdout> → skip (return empty)
    if re.match(r'<local-command-stdout>', text):
        return ''

    # <command-name>/CMD</command-name>...<command-message>MSG</command-message>... → compact output
    if re.match(r'<command-name>', text) or re.match(r'<command-message>', text):
        msg_m = re.search(r'<command-message>(.*?)</command-message>', text, re.DOTALL)
        name_m = re.search(r'<command-name>(.*?)</command-name>', text, re.DOTALL)
        if msg_m:
            msg = msg_m.group(1).strip()
            if msg:
                return f"/{msg}"
        if name_m:
            return name_m.group(1).strip()
        return ''

    # Cursor: <user_query>...</user_query> → extract content only
    uq_m = re.search(r'<user_query>(.*?)</user_query>', text, re.DOTALL)
    if uq_m:
        text = uq_m.group(1).strip()

    # Cursor: remove <image_files>...</image_files> blocks
    text = re.sub(r'<image_files>.*?</image_files>', '', text, flags=re.DOTALL).strip()

    # Cursor: remove standalone [Image] markers
    text = re.sub(r'\[Image\]\s*', '', text).strip()

    return text


def extract_text_blocks(content):
    """Extract only text-type blocks from a content array."""
    if isinstance(content, str):
        return clean_string_content(content)
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type", "")
        if t == "text":
            text = clean_string_content(block.get("text", ""))
            if text:
                parts.append(text)
        # tool_result, tool_use, thinking, image are all skipped
    return "\n\n".join(parts)


def convert_claude_jsonl(filepath):
    """Parse a Claude Code session JSONL file. Returns (messages, first_ts, last_ts, title, cwd, models)."""
    messages = []
    first_ts = None
    last_ts = None
    title = None
    cwd = None
    models_seen = []

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Get conversation title from custom-title (use last entry, as it may have been renamed)
            if obj.get("type") == "custom-title":
                t = obj.get("customTitle", "").strip()
                if t:
                    title = t

            msg = obj.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            # Skip meta messages injected from CLAUDE.md / skills
            if obj.get("isMeta"):
                continue

            # Get timestamp and cwd
            ts = obj.get("timestamp", "")
            if ts and first_ts is None:
                first_ts = ts
            if ts:
                last_ts = ts
            if cwd is None:
                cwd = obj.get("cwd", "")

            # Collect model info (only present in assistant messages)
            if role == "assistant":
                model = msg.get("model", "")
                if model and model not in models_seen:
                    models_seen.append(model)

            content = msg.get("content", "")
            text = extract_text_blocks(content)

            if text.strip():
                messages.append((role, text.strip(), ts))

    return messages, first_ts, last_ts, title, cwd, models_seen


def convert_cursor_jsonl(filepath):
    """Parse a Cursor agent transcript JSONL file. Returns (messages, first_ts, last_ts, models).
    Note: Cursor transcript format does not include model info; models always returns an empty list."""
    messages = []
    first_ts = None
    last_ts = None
    models_seen = []  # Cursor does not record model names

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
            if role not in ("user", "assistant"):
                continue

            content = obj.get("message", {}).get("content", [])
            text = extract_text_blocks(content)

            if text.strip():
                ts = obj.get("timestamp", "")
                if ts and first_ts is None:
                    first_ts = ts
                if ts:
                    last_ts = ts
                messages.append((role, text.strip(), ts))

    return messages, first_ts, last_ts, models_seen


def lookup_cursor_composer(composer_id):
    """Look up the name, creation time, models, and cost for a composerId from the Cursor vscdb.
    Returns (name, created_at_iso, models, total_cost_cents) or (None, None, [], 0)."""
    name = None
    created_iso = None

    # Get title and creation time from workspaceStorage
    vscdb_pattern = os.path.expanduser(
        "~/Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb"
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

    # Get usageData (model names + cost) from globalStorage
    models = []
    total_cost_cents = 0
    global_db = os.path.expanduser(
        "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
    )
    try:
        conn = sqlite3.connect(global_db)
        cur = conn.cursor()
        cur.execute("SELECT value FROM cursorDiskKV WHERE key=?", (f"composerData:{composer_id}",))
        row = cur.fetchone()
        conn.close()
        if row:
            data = json.loads(row[0])
            usage = data.get("usageData", {})
            for model, stats in usage.items():
                models.append(model)
                total_cost_cents += stats.get("costInCents", 0)
    except Exception:
        pass

    return name, created_iso, models, total_cost_cents


def convert_cursor_txt(filepath):
    """Parse legacy Cursor .txt format."""
    messages = []
    current_role = None
    current_lines = []

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.rstrip()
            if stripped.startswith("user:"):
                if current_role and current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        messages.append((current_role, text, ""))
                current_role = "user"
                current_lines = [stripped[5:].strip()]
            elif stripped.startswith("assistant:"):
                if current_role and current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        messages.append((current_role, text, ""))
                current_role = "assistant"
                current_lines = [stripped[10:].strip()]
            else:
                if current_role is not None:
                    current_lines.append(stripped)

    if current_role and current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            messages.append((current_role, text, ""))

    return messages, None


def generate_title_from_messages(messages):
    """Generate a title from conversation content (used for unnamed sessions)."""
    for role, text, ts in messages:
        if role == "user" and text.strip():
            first_line = text.strip().split('\n')[0].strip()
            # Strip common markdown and command prefixes
            first_line = re.sub(r'[#*`_~\[\]<>]', '', first_line).strip()
            first_line = re.sub(r'^[@!]', '', first_line).strip()
            if len(first_line) > 3:
                return first_line[:60]
    return None


def format_markdown(messages, first_ts, source_name, cwd=None, title=None, models=None, cost_cents=0):
    lines = []

    # Parse date
    date_str = ""
    if first_ts:
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).astimezone(TZ_LOCAL)
            date_str = dt.strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
        except Exception:
            date_str = first_ts

    # Title
    display_title = title or source_name
    lines.append(f"# {display_title}")
    lines.append("")

    if date_str:
        lines.append(f"**Date:** {date_str}")

    # Project path: show folder name (absolute path)
    if cwd:
        folder_name = Path(cwd).name or cwd
        lines.append(f"**Project:** {folder_name} (`{cwd}`)")

    lines.append(f"**Source:** {source_name}")
    if models:
        model_str = ', '.join(models)
        if cost_cents:
            model_str += f" (${cost_cents / 100:.2f})"
        lines.append(f"**Model:** {model_str}")
    lines.append(f"**Messages:** {len(messages)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not messages:
        lines.append("*(no valid messages)*")
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
            lines.append(f"### User{ts_str}")
        else:
            lines.append(f"### Assistant{ts_str}")
        lines.append("")
        lines.append(truncate(text))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def make_output_path(out_dir, first_ts, title):
    """Generate output filename based on date and title."""
    if first_ts:
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).astimezone(TZ_LOCAL)
            date_str = f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}-{dt.microsecond // 1000:03d}"
        except Exception:
            date_str = "unknown"
    else:
        date_str = "unknown"

    if title:
        title_safe = re.sub(r'[^\w\-]', '_', title)[:60].strip('_')
        filename = f"{date_str}_{title_safe}.md"
    else:
        filename = f"{date_str}.md"
    return os.path.join(out_dir, filename)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 convert_to_markdown.py <input> <output_dir> [--source claude|cursor] [--cwd PATH] [--days N]")
        sys.exit(1)

    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    source = "claude"
    cwd_arg = None
    days_filter = None

    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        if idx + 1 < len(sys.argv):
            source = sys.argv[idx + 1]

    if "--cwd" in sys.argv:
        idx = sys.argv.index("--cwd")
        if idx + 1 < len(sys.argv):
            cwd_arg = sys.argv[idx + 1]

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days_filter = int(sys.argv[idx + 1])
            except ValueError:
                pass

    ext = Path(input_path).suffix.lower()

    last_ts = None

    models = []
    cost_cents = 0

    if source == "cursor" and ext == ".txt":
        messages, first_ts = convert_cursor_txt(input_path)
        title = None
        cwd = cwd_arg
        source_name = "Cursor"
    elif source == "cursor":
        messages, first_ts, last_ts, models = convert_cursor_jsonl(input_path)
        composer_id = Path(input_path).stem
        db_name, db_ts, models, cost_cents = lookup_cursor_composer(composer_id)
        title = db_name
        if not first_ts and db_ts:
            first_ts = db_ts
        cwd = cwd_arg
        source_name = "Cursor"
    else:
        messages, first_ts, last_ts, title, cwd, models = convert_claude_jsonl(input_path)
        if cwd_arg:
            cwd = cwd_arg
        source_name = "Claude Code"

    # If no timestamp, fall back to file modification time (local timezone)
    if not first_ts:
        mtime = os.path.getmtime(input_path)
        dt_mtime = datetime.fromtimestamp(mtime, tz=TZ_LOCAL)
        first_ts = dt_mtime.isoformat()

    # Always use the last timestamp (covers long conversations, resume, compact, etc.)
    active_ts = last_ts or first_ts

    # Apply --days filter if provided
    if days_filter is not None and active_ts:
        try:
            dt_check = datetime.fromisoformat(active_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
            if dt_check < cutoff:
                sys.exit(0)
        except Exception:
            pass

    md = format_markdown(messages, active_ts, source_name, cwd=cwd, title=title, models=models, cost_cents=cost_cents)

    os.makedirs(out_dir, exist_ok=True)
    output_path = make_output_path(out_dir, active_ts, title)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ Done: {len(messages)} messages → {output_path}")


if __name__ == "__main__":
    main()
