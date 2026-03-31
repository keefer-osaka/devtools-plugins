#!/usr/bin/env bash
# export.sh - Export Claude Code chat logs and send to Telegram
# Usage: bash export.sh [days=7]

set -e

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATS_SCRIPT="$PLUGIN_ROOT/scripts/generate_stats.py"

# Load locale strings
source "$PLUGIN_ROOT/scripts/i18n/load.sh"

DAYS="${1:-7}"
DAYS=$(echo "$DAYS" | grep -o '[0-9]*' | head -1)
DAYS="${DAYS:-7}"

# Load configuration (token + chat_id)
DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "$ERR_NOT_CONFIGURED"
  exit 1
fi
TELEGRAM_BOT_TOKEN=$(grep 'TELEGRAM_BOT_TOKEN' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
CHAT_ID=$(grep 'TELEGRAM_CHAT_ID' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
OUTPUT_FORMAT=$(grep 'OUTPUT_FORMAT' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
OUTPUT_FORMAT="${OUTPUT_FORMAT:-html}"
INCLUDE_COWORK=$(grep 'INCLUDE_COWORK' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
INCLUDE_COWORK="${INCLUDE_COWORK:-false}"

# Select converter based on output format
if [ "$OUTPUT_FORMAT" = "html" ]; then
  CONVERTER="$PLUGIN_ROOT/scripts/convert_to_html.py"
else
  CONVERTER="$PLUGIN_ROOT/scripts/convert_to_markdown.py"
fi
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "$ERR_TOKEN_EMPTY"
  exit 1
fi
if [ -z "$CHAT_ID" ]; then
  echo "$ERR_CHATID_EMPTY"
  exit 1
fi

# Create temp directory
EXPORT_DATE=$(date +%Y%m%d)
TMPDIR_PATH="$TMPDIR/chat-export-${EXPORT_DATE}-$$"
rm -rf "$TMPDIR_PATH"
mkdir -p "$TMPDIR_PATH/claude-code"
if [ "$INCLUDE_COWORK" = "true" ]; then
  mkdir -p "$TMPDIR_PATH/claude-cowork"
fi

# Strip home directory prefix from project folder name (e.g. -Users-user-foo-bar → foo-bar)
HOME_ENCODED=$(echo "$HOME" | tr '/' '-')

# Convert Claude Code sessions
CC_COUNT=0
while IFS= read -r jsonl_file; do
  [ -z "$jsonl_file" ] && continue
  PROJECT=$(echo "$jsonl_file" | sed 's|.*/projects/||' | cut -d'/' -f1)
  PROJECT_DISPLAY=$(echo "$PROJECT" | sed "s/^${HOME_ENCODED}-//;s/^${HOME_ENCODED}$//")
  OUT_DIR="$TMPDIR_PATH/claude-code/$PROJECT_DISPLAY"
  mkdir -p "$OUT_DIR"
  python3 -c "import sys; sys.path.insert(0,'$PLUGIN_ROOT/scripts'); from common import is_trivial_session; sys.exit(0 if is_trivial_session(sys.argv[1]) else 1)" "$jsonl_file" 2>/dev/null && continue
  python3 "$CONVERTER" "$jsonl_file" "$OUT_DIR" --days "$DAYS" >/dev/null 2>&1 && CC_COUNT=$((CC_COUNT + 1))
done < <(find "$HOME/.claude/projects" -name "*.jsonl" \
  -not -path "*/subagents/*" \
  -not -path "*/memory/*" \
  -mtime -"$DAYS" 2>/dev/null)

# Convert Claude Cowork sessions (opt-in, macOS only)
CW_COUNT=0
COWORK_PATHS=()
if [ "$INCLUDE_COWORK" = "true" ]; then
  COWORK_PATHS=(
    "$HOME/Library/Application Support/Claude/local-agent-mode-sessions"
    "$HOME/Library/Application Support/Claude/claude-code-sessions"
  )
  for COWORK_BASE in "${COWORK_PATHS[@]}"; do
    [ -d "$COWORK_BASE" ] || continue
    while IFS= read -r jsonl_file; do
      [ -z "$jsonl_file" ] && continue
      CW_PROJECT=$(python3 "$PLUGIN_ROOT/scripts/common.py" --extract-cwd "$jsonl_file" 2>/dev/null)
      CW_PROJECT="${CW_PROJECT:-unknown}"
      OUT_DIR="$TMPDIR_PATH/claude-cowork/$CW_PROJECT"
      mkdir -p "$OUT_DIR"
      python3 -c "import sys; sys.path.insert(0,'$PLUGIN_ROOT/scripts'); from common import is_trivial_session; sys.exit(0 if is_trivial_session(sys.argv[1]) else 1)" "$jsonl_file" 2>/dev/null && continue
      python3 "$CONVERTER" "$jsonl_file" "$OUT_DIR" --days "$DAYS" --source-label cowork >/dev/null 2>&1 && CW_COUNT=$((CW_COUNT + 1))
    done < <(find "$COWORK_BASE" -name "*.jsonl" \
      -not -path "*/subagents/*" \
      -not -path "*/memory/*" \
      -not -name "audit.jsonl" \
      -mtime -"$DAYS" 2>/dev/null)
  done
fi

# Exit early if no sessions found
if [ "$CC_COUNT" -eq 0 ] && [ "$CW_COUNT" -eq 0 ]; then
  echo "${WARN_NO_SESSIONS//%DAYS%/$DAYS}"
  rm -rf "$TMPDIR_PATH"
  exit 0
fi

# Generate stats report
STATS_DATE=$(date +%Y-%m-%d_%H-%M)
STATS_EXT=$( [ "$OUTPUT_FORMAT" = "html" ] && echo "html" || echo "md" )

# Claude Code stats
CC_STATS_FILE="$TMPDIR_PATH/${STATS_DATE}_${STATS_REPORT_SLUG}.${STATS_EXT}"
python3 "$STATS_SCRIPT" \
  --projects "$HOME/.claude/projects" \
  --days "$DAYS" \
  --format "$OUTPUT_FORMAT" \
  --out "$CC_STATS_FILE" \
  --conv-base "$TMPDIR_PATH/claude-code" >/dev/null 2>&1

# Claude Cowork stats (only when there are Cowork sessions)
if [ "$INCLUDE_COWORK" = "true" ] && [ "$CW_COUNT" -gt 0 ]; then
  CW_STATS_FILE="$TMPDIR_PATH/${STATS_DATE}_${STATS_REPORT_SLUG_COWORK}.${STATS_EXT}"
  CW_STATS_CMD=(python3 "$STATS_SCRIPT"
    --days "$DAYS"
    --format "$OUTPUT_FORMAT"
    --out "$CW_STATS_FILE"
    --conv-base "$TMPDIR_PATH/claude-cowork"
    --source-label cowork
  )
  for COWORK_BASE in "${COWORK_PATHS[@]}"; do
    [ -d "$COWORK_BASE" ] && CW_STATS_CMD+=(--projects "$COWORK_BASE")
  done
  "${CW_STATS_CMD[@]}" >/dev/null 2>&1
fi

CC_SESSIONS=$(grep '^\*\*Sessions:\*\*' "$CC_STATS_FILE" 2>/dev/null | grep -o '[0-9]*' | head -1)
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
_s1="${SUMMARY_USER//%GIT_USER%/$GIT_USER}"
_s2="${SUMMARY_PERIOD//%START_DATE%/$START_DATE}"; _s2="${_s2//%TODAY%/$TODAY}"; _s2="${_s2//%DAYS%/$DAYS}"
if [ "$INCLUDE_COWORK" = "true" ] && [ "$CW_COUNT" -gt 0 ]; then
  _s3="${SUMMARY_STATS_COWORK//%CC_SESSIONS%/$CC_SESSIONS}"
  _s3="${_s3//%CW_SESSIONS%/$CW_COUNT}"
else
  _s3="${SUMMARY_STATS//%CC_SESSIONS%/$CC_SESSIONS}"
fi
_s4="${SUMMARY_SIZE//%ZIP_SIZE%/$ZIP_SIZE}"
if [ "$OUTPUT_FORMAT" = "html" ]; then
  _s5="$SUMMARY_FORMAT_HTML"
else
  _s5="$SUMMARY_FORMAT_MD"
fi
SUMMARY_TEXT="$SUMMARY_HEADER
$_s1
$_s2
$_s3
$_s4
$_s5"

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
if [ "$INCLUDE_COWORK" = "true" ] && [ "$CW_COUNT" -gt 0 ]; then
  _done="${MSG_DONE_COWORK//%CC_SESSIONS%/$CC_SESSIONS}"
  _done="${_done//%CW_SESSIONS%/$CW_COUNT}"
  _done="${_done//%ZIP_SIZE%/$ZIP_SIZE}"
else
  _done="${MSG_DONE//%CC_SESSIONS%/$CC_SESSIONS}"
  _done="${_done//%ZIP_SIZE%/$ZIP_SIZE}"
fi
echo "$_done"
