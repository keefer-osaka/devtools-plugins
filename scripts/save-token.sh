#!/usr/bin/env bash
# save-token.sh - Save Telegram Bot Token, chat_id, and timezone offset
# Usage: bash save-token.sh <token> <chat_id> [timezone_offset]
#   timezone_offset: integer, e.g. 8 for UTC+8 (Taiwan), -5 for UTC-5 (EST), default 8

if [ -z "$1" ]; then
  echo "❌ Token required: bash save-token.sh <token> <chat_id> [timezone_offset]"
  exit 1
fi
if [ -z "$2" ]; then
  echo "❌ Chat ID required: bash save-token.sh <token> <chat_id> [timezone_offset]"
  exit 1
fi

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
mkdir -p "$DATA_DIR"
ENV_FILE="$DATA_DIR/.env"

# Timezone: use third argument if provided, otherwise keep existing setting, otherwise default to 8 (UTC+8)
if [ -n "$3" ]; then
  TZ_OFFSET="$3"
elif [ -f "$ENV_FILE" ]; then
  TZ_OFFSET=$(grep 'TIMEZONE_OFFSET' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  TZ_OFFSET="${TZ_OFFSET:-8}"
else
  TZ_OFFSET="8"
fi

printf 'TELEGRAM_BOT_TOKEN=%s\nTELEGRAM_CHAT_ID=%s\nTIMEZONE_OFFSET=%s\n' "$1" "$2" "$TZ_OFFSET" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
TZ_LABEL=$(printf "UTC%+d" "$TZ_OFFSET")
echo "✅ Configuration saved (Token + Chat ID + Timezone ${TZ_LABEL})"
