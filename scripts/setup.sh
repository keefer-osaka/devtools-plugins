#!/usr/bin/env bash
# setup.sh - Display current Telegram configuration status
# Usage: bash setup.sh

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"

CURRENT_TOKEN=""
CURRENT_CHAT_ID=""
CURRENT_TZ=""
if [ -f "$ENV_FILE" ]; then
  CURRENT_TOKEN=$(grep 'TELEGRAM_BOT_TOKEN' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_CHAT_ID=$(grep 'TELEGRAM_CHAT_ID' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_TZ=$(grep 'TIMEZONE_OFFSET' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
fi

if [ -n "$CURRENT_TOKEN" ]; then
  echo "Bot Token: ${CURRENT_TOKEN:0:6}...${CURRENT_TOKEN: -4}"
else
  echo "Bot Token: (not set)"
fi

if [ -n "$CURRENT_CHAT_ID" ]; then
  echo "Chat ID: ${CURRENT_CHAT_ID}"
else
  echo "Chat ID: (not set)"
fi

if [ -n "$CURRENT_TZ" ]; then
  TZ_LABEL=$(printf "UTC%+d" "$CURRENT_TZ")
  echo "Timezone: ${TZ_LABEL}"
else
  echo "Timezone: (not set, default UTC+8)"
fi
