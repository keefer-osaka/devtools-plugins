---
name: auto
description: "Generate a launchd plist for automated weekly chat log exports on macOS. Use when user says 'auto export', 'automate export', 'set up launchd', 'weekly export', or 'schedule export'."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Schedule Automated Chat Log Export

**Silent mode:** Do not print any text between steps — this includes step names, headers, or labels (e.g. do NOT output "Step 7" or any step identifier). Proceed directly from one step to the next without outputting status messages, summaries, or confirmations. Only allowed outputs: (1) the Telegram-not-configured error, (2) AskUserQuestion calls, (3) the script's stdout (Step 6).

## Step 1 — Read current config

Read `~/.config/devtools-plugins/export-chat-logs/.env` (use `$HOME` if `~` doesn't work).

Extract:
- `CURRENT_TOKEN` (present if set)
- `CURRENT_CHAT_ID` (present if set)
- `CURRENT_LANG` (default: `en`)

Then detect existing launchd schedule:

```bash
PLIST="$HOME/Library/LaunchAgents/com.devtools-plugins.export-chat-logs.plist"
HAS_EXISTING=0
if command -v plutil >/dev/null 2>&1 && [ -f "$PLIST" ]; then
  _W=$(plutil -extract StartCalendarInterval.Weekday raw "$PLIST" 2>/dev/null)
  _H=$(plutil -extract StartCalendarInterval.Hour raw "$PLIST" 2>/dev/null)
  _M=$(plutil -extract StartCalendarInterval.Minute raw "$PLIST" 2>/dev/null)
  if [[ "$_W" =~ ^[0-9]+$ ]] && [[ "$_H" =~ ^[0-9]+$ ]] && [[ "$_M" =~ ^[0-9]+$ ]] \
     && [ "$_W" -le 7 ] && [ "$_H" -le 23 ] && [ "$_M" -le 59 ]; then
    [ "$_W" -eq 7 ] && _W=0
    EXISTING_WEEKDAY=$_W
    EXISTING_HOUR=$_H
    EXISTING_MINUTE=$_M
    HAS_EXISTING=1
  fi
fi
```

**If `CURRENT_TOKEN` or `CURRENT_CHAT_ID` is empty or the file does not exist:**
Stop and print (EN/ZH-TW/JA trilingual):

> ⚠️ Telegram is not configured. Run `/export-chat-logs:setup` first, then re-run `/export-chat-logs:auto`.
> ⚠️ Telegram 尚未設定。請先執行 `/export-chat-logs:setup`，再重新執行 `/export-chat-logs:auto`。
> ⚠️ Telegram が設定されていません。先に `/export-chat-logs:setup` を実行してから `/export-chat-logs:auto` を再実行してください。

---

## Step 2 — Determine language (`SETUP_LANG`)

`SETUP_LANG = CURRENT_LANG`

Read `"${CLAUDE_PLUGIN_ROOT}/skills/auto/questions/${SETUP_LANG}.json"`, store as `Q`.

---

## Step 3 — Ask schedule time

First, load i18n and resolve the suggested time:

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/i18n/load.sh"
```

If `HAS_EXISTING == 1`:
- `SUGGESTED_WEEKDAY = EXISTING_WEEKDAY`, `SUGGESTED_HOUR = EXISTING_HOUR`, `SUGGESTED_MINUTE = EXISTING_MINUTE`
- `SUGGESTED_LOCAL = $(fmt_schedule_natural $SUGGESTED_WEEKDAY $SUGGESTED_HOUR $SUGGESTED_MINUTE)`
- Replace `"(Recommended)"` → `"(Keep current)"` / `"（建議）"` → `"（保留現有）"` / `"（推奨）"` → `"（現状維持）"` in the option label after substituting `<SUGGESTED_TIME>`

Else (no existing plist):
- `SUGGESTED_WEEKDAY = 1`, `SUGGESTED_HOUR = 17`, `SUGGESTED_MINUTE = 0`
- `SUGGESTED_LOCAL = $(fmt_schedule_natural 1 17 0)`

Substitute `<SUGGESTED_TIME>` in `Q["schedule_time"]` with `SUGGESTED_LOCAL`, apply the Keep current label replacement if applicable, then use AskUserQuestion.

**Handling answers:**
- Recommended / Keep current option selected → `FINAL_WEEKDAY = SUGGESTED_WEEKDAY`, `FINAL_HOUR = SUGGESTED_HOUR`, `FINAL_MINUTE = SUGGESTED_MINUTE`
- `"Custom time"` / `"自訂時間"` / `"カスタム時間"` selected → wait for text field input
- Text field input:
  - If it looks like a cron expression (5 space-separated fields, e.g. `30 23 * * 0`) → extract minute, hour, day-of-week fields; treat as local time
  - Otherwise parse as natural language (e.g. `"every Sunday at 10:30pm"`, `"每週日晚上十點半"`, `"毎週日曜日の夜10時半"`) → extract weekday, hour, minute as local time

Store as `FINAL_WEEKDAY`, `FINAL_HOUR`, `FINAL_MINUTE`.

---

## Step 4 — Ask export days

Use `Q["export_days"]` with AskUserQuestion.

**Handling answers:**
- `"7 days (Recommended)"` / `"7 天（建議）"` / `"7 日間（推奨）"` → `DAYS=7`
- `"14 days"` / `"14 天"` / `"14 日間"` → `DAYS=14`
- `"30 days"` / `"30 天"` / `"30 日間"` → `DAYS=30`
- Text field input (number) → `DAYS=<number>`

---

## Step 5 — Install launchd agent

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/install-launchd.sh" \
  "$FINAL_WEEKDAY" "$FINAL_HOUR" "$FINAL_MINUTE" \
  "$DAYS" "${CLAUDE_PLUGIN_ROOT}" "$SETUP_LANG"
```

The script handles everything: plist generation, `launchctl` load, summary markdown file, and success message. Print the script's output as-is. No further output needed.
