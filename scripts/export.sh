#!/usr/bin/env bash
# export.sh - Export Claude Code and Cursor chat logs and send to Telegram
# Usage: bash export.sh [days=7]

set -e

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONVERTER="$PLUGIN_ROOT/scripts/convert_to_markdown.py"
STATS_SCRIPT="$PLUGIN_ROOT/scripts/generate_stats.py"

DAYS="${1:-7}"
DAYS=$(echo "$DAYS" | grep -o '[0-9]*' | head -1)
DAYS="${DAYS:-7}"

# Load configuration (token + chat_id)
DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Not configured. Please run: /export-chat-logs:setup"
  exit 1
fi
TELEGRAM_BOT_TOKEN=$(grep 'TELEGRAM_BOT_TOKEN' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
CHAT_ID=$(grep 'TELEGRAM_CHAT_ID' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "❌ Telegram Bot Token is empty. Please run: /export-chat-logs:setup"
  exit 1
fi
if [ -z "$CHAT_ID" ]; then
  echo "❌ Telegram chat_id is empty. Please run: /export-chat-logs:setup"
  exit 1
fi

# Create temp directory
EXPORT_DATE=$(date +%Y%m%d)
TMPDIR_PATH="$TMPDIR/chat-export-${EXPORT_DATE}-$$"
rm -rf "$TMPDIR_PATH"
mkdir -p "$TMPDIR_PATH/claude-code" "$TMPDIR_PATH/cursor"

# Convert Claude Code sessions
CC_COUNT=0
while IFS= read -r jsonl_file; do
  [ -z "$jsonl_file" ] && continue
  PROJECT=$(echo "$jsonl_file" | sed 's|.*/projects/||' | cut -d'/' -f1)
  OUT_DIR="$TMPDIR_PATH/claude-code/$PROJECT"
  mkdir -p "$OUT_DIR"
  python3 "$CONVERTER" "$jsonl_file" "$OUT_DIR" --source claude --days "$DAYS" >/dev/null 2>&1 && CC_COUNT=$((CC_COUNT + 1))
done < <(find "$HOME/.claude/projects" -name "*.jsonl" \
  -not -path "*/subagents/*" \
  -not -path "*/memory/*" \
  -mtime -"$DAYS" 2>/dev/null)

# Convert Cursor sessions
CURSOR_COUNT=0
CURSOR_BASE="$HOME/.cursor/projects"
if [ -d "$CURSOR_BASE" ]; then
  while IFS= read -r cursor_file; do
    [ -z "$cursor_file" ] && continue
    PROJECT=$(echo "$cursor_file" | sed "s|$CURSOR_BASE/||" | cut -d'/' -f1)
    OUT_DIR="$TMPDIR_PATH/cursor/$PROJECT"
    mkdir -p "$OUT_DIR"
    python3 "$CONVERTER" "$cursor_file" "$OUT_DIR" --source cursor --cwd "$PROJECT" --days "$DAYS" >/dev/null 2>&1 && CURSOR_COUNT=$((CURSOR_COUNT + 1))
  done < <(find "$CURSOR_BASE" -path "*/agent-transcripts/*" \
    -not -path "*/subagents/*" \
    \( -name "*.jsonl" -o -name "*.txt" \) \
    -mtime -"$DAYS" 2>/dev/null)
fi

# Exit early if no sessions found
if [ "$CC_COUNT" -eq 0 ] && [ "$CURSOR_COUNT" -eq 0 ]; then
  echo "⚠️  No sessions found in the last ${DAYS} days, skipping."
  rm -rf "$TMPDIR_PATH"
  exit 0
fi

# Generate stats reports (run in parallel)
STATS_DATE=$(date +%Y-%m-%d_%H-%M)
python3 "$STATS_SCRIPT" --projects "$HOME/.claude/projects" --days "$DAYS" \
  --out "$TMPDIR_PATH/${STATS_DATE}_claude-code_stats-report.md" >/dev/null 2>&1 &
python3 "$STATS_SCRIPT" --cursor-projects "$HOME/.cursor/projects" --days "$DAYS" \
  --out "$TMPDIR_PATH/${STATS_DATE}_cursor_stats-report.md" >/dev/null 2>&1 &
wait || true

# Get accurate session count from stats report (consistent with report)
STATS_FILE="$TMPDIR_PATH/${STATS_DATE}_claude-code_stats-report.md"
CC_SESSIONS=$(grep '^\*\*Sessions:\*\*' "$STATS_FILE" 2>/dev/null | grep -o '[0-9]*' | head -1)
CC_SESSIONS="${CC_SESSIONS:-$CC_COUNT}"

# Package as zip
GIT_USER_NAME=$(git config --global user.name 2>/dev/null | tr ' ' '_')
GIT_USER_NAME="${GIT_USER_NAME:-$(whoami)}"
ZIPNAME="$TMPDIR/chat-logs-${GIT_USER_NAME}-${EXPORT_DATE}.zip"
rm -f "$ZIPNAME"
cd "$TMPDIR_PATH" && zip -r "$ZIPNAME" . -x "*.DS_Store" > /dev/null
ZIP_SIZE=$(du -sh "$ZIPNAME" | cut -f1)
ZIP_BYTES=$(stat -f%z "$ZIPNAME" 2>/dev/null || stat -c%s "$ZIPNAME" 2>/dev/null)

# Send to Telegram
START_DATE=$(date -v-${DAYS}d +%Y-%m-%d 2>/dev/null || date -d "-${DAYS} days" +%Y-%m-%d 2>/dev/null)
TODAY=$(date +%Y-%m-%d)
GIT_USER_EMAIL=$(git config --global user.email 2>/dev/null)
GIT_USER_DISPLAY=$(echo "$GIT_USER_NAME" | tr '_' ' ')
if [ -n "$GIT_USER_EMAIL" ]; then
  GIT_USER="${GIT_USER_DISPLAY} <${GIT_USER_EMAIL}>"
else
  GIT_USER="$GIT_USER_DISPLAY"
fi
SUMMARY_TEXT="📦 Chat Log Export
👤 User: ${GIT_USER}
📅 Period: ${START_DATE} ~ ${TODAY} (last ${DAYS} days)
📊 Stats:
  • Claude Code: ${CC_SESSIONS} sessions
  • Cursor: ${CURSOR_COUNT} conversations
💾 File size: ${ZIP_SIZE}
📝 Format: Markdown (tool calls and technical details omitted)"

# Send text summary first
curl -s -o /dev/null -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" \
  --data-urlencode text="$SUMMARY_TEXT"

# Then send the file
if [ "$ZIP_BYTES" -le 52428800 ]; then
  curl -s -o /dev/null -X POST \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
    -F chat_id="$CHAT_ID" \
    -F document=@"$ZIPNAME"
else
  split -b 45m "$ZIPNAME" "${ZIPNAME}.part"
  PART_NUM=1
  PART_TOTAL=$(ls "${ZIPNAME}.part"* | wc -l | tr -d ' ')
  for part in "${ZIPNAME}.part"*; do
    curl -s -o /dev/null -X POST \
      "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
      -F chat_id="$CHAT_ID" \
      -F document=@"$part" \
      -F caption="[${PART_NUM}/${PART_TOTAL}] $(basename "$part")"
    PART_NUM=$((PART_NUM + 1))
  done
  rm -f "${ZIPNAME}.part"*
fi

# Clean up temp directory
rm -rf "$TMPDIR_PATH"
echo "✅ Done! Claude Code: ${CC_SESSIONS} sessions, Cursor: ${CURSOR_COUNT} conversations, zip: ${ZIP_SIZE}, sent to Telegram"
