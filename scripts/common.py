#!/usr/bin/env python3
"""Shared utilities for devtools-plugins scripts."""

import json
import re
import os
import sys
import importlib.util
from datetime import datetime, timezone, timedelta


def _load_lang():
    env_path = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "devtools-plugins", "export-chat-logs", ".env"
    )
    lang = "en"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("PLUGIN_LANG="):
                    lang = line.split("=", 1)[1].strip().strip("'\"")
                    break
    except Exception:
        pass
    lang_file = lang.replace("-", "_")
    i18n_dir = os.path.join(os.path.dirname(__file__), "i18n")
    locale_path = os.path.join(i18n_dir, f"{lang_file}.py")
    if not os.path.exists(locale_path):
        locale_path = os.path.join(i18n_dir, "en.py")
    spec = importlib.util.spec_from_file_location("_locale", locale_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.S, lang


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


S, LANG_CODE = _load_lang()
TZ_LOCAL, TZ_OFFSET = _load_tz()
TZ_LABEL = f"UTC{TZ_OFFSET:+d}"
MAX_MSG_LEN = 3000


def truncate(text, max_len=MAX_MSG_LEN):
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n\n" + S["truncated"].format(n=len(text) - max_len)


def clean_string_content(text):
    """Clean string message content: strip control characters, simplify slash command XML."""
    text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text).strip()

    if re.match(r'<local-command-stdout>', text):
        return ''

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

            if obj.get("type") == "custom-title":
                t = obj.get("customTitle", "").strip()
                if t:
                    title = t

            msg = obj.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            if obj.get("isMeta"):
                continue

            ts = obj.get("timestamp", "")
            if ts and first_ts is None:
                first_ts = ts
            if ts:
                last_ts = ts
            if cwd is None:
                cwd = obj.get("cwd", "")

            if role == "assistant":
                model = msg.get("model", "")
                if model and model not in models_seen:
                    models_seen.append(model)

            content = msg.get("content", "")
            text = extract_text_blocks(content)

            if text.strip():
                messages.append((role, text.strip(), ts))

    return messages, first_ts, last_ts, title, cwd, models_seen


def generate_title_from_messages(messages):
    """Generate a title from conversation content (used for unnamed sessions)."""
    for role, text, ts in messages:
        if role == "user" and text.strip():
            first_line = text.strip().split('\n')[0].strip()
            first_line = re.sub(r'[#*`_~\[\]<>]', '', first_line).strip()
            first_line = re.sub(r'^[@!]', '', first_line).strip()
            if len(first_line) > 3:
                return first_line[:60]
    return None


def is_trivial_session(filepath):
    """Return True if a session has no meaningful interaction and should be excluded from packaging."""
    input_tokens = output_tokens = 0
    timestamps = []
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
                if obj.get("isMeta"):
                    continue
                msg = obj.get("message", {})
                usage = msg.get("usage", {})
                if usage:
                    input_tokens  += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                ts = obj.get("timestamp", "")
                if ts and msg.get("role") in ("user", "assistant"):
                    timestamps.append(ts)
    except Exception:
        return True

    if input_tokens + output_tokens == 0:
        return True

    if output_tokens >= 100:
        return False

    # Compute active duration (sum consecutive gaps <= 30 min)
    if len(timestamps) >= 2:
        try:
            dts = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps]
            active = sum(
                (dts[i] - dts[i - 1]).total_seconds()
                for i in range(1, len(dts))
                if (dts[i] - dts[i - 1]).total_seconds() <= 1800
            )
            return active < 60
        except Exception:
            pass
    return True  # single message or unparseable → trivial


def make_output_path(out_dir, first_ts, title, ext=".md"):
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
        filename = f"{date_str}_{title_safe}{ext}"
    else:
        filename = f"{date_str}{ext}"
    return os.path.join(out_dir, filename)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--extract-cwd":
        with open(sys.argv[2], encoding="utf-8", errors="ignore") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line:
                    continue
                try:
                    _obj = json.loads(_line)
                    _cwd = _obj.get("cwd", "")
                    if _cwd:
                        print(_cwd.rstrip("/").split("/")[-1])
                        break
                except Exception:
                    pass
