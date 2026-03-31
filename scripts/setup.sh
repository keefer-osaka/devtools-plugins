#!/usr/bin/env bash
# setup.sh - Display current Telegram configuration status
# Usage: bash setup.sh

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"

# Load locale strings
source "$(dirname "$0")/i18n/load.sh"

CURRENT_TOKEN=""
CURRENT_CHAT_ID=""
CURRENT_TZ=""
CURRENT_LANG=""
CURRENT_FORMAT=""
CURRENT_COWORK=""
if [ -f "$ENV_FILE" ]; then
  CURRENT_TOKEN=$(grep 'TELEGRAM_BOT_TOKEN' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_CHAT_ID=$(grep 'TELEGRAM_CHAT_ID' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_TZ=$(grep 'TIMEZONE_OFFSET' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_LANG=$(grep 'PLUGIN_LANG' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_FORMAT=$(grep 'OUTPUT_FORMAT' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  CURRENT_COWORK=$(grep 'INCLUDE_COWORK' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
fi

if [ -n "$CURRENT_TOKEN" ]; then
  _masked="${CURRENT_TOKEN:0:6}...${CURRENT_TOKEN: -4}"
  echo "${LABEL_BOT_TOKEN_SET//%VALUE%/$_masked}"
else
  echo "$LABEL_BOT_TOKEN_UNSET"
fi

if [ -n "$CURRENT_CHAT_ID" ]; then
  echo "${LABEL_CHAT_ID_SET//%VALUE%/$CURRENT_CHAT_ID}"
else
  echo "$LABEL_CHAT_ID_UNSET"
fi

if [ -n "$CURRENT_TZ" ]; then
  TZ_LABEL=$(printf "UTC%+d" "$CURRENT_TZ")
  echo "${LABEL_TIMEZONE_SET//%VALUE%/$TZ_LABEL}"
else
  echo "$LABEL_TIMEZONE_UNSET"
fi

if [ -n "$CURRENT_LANG" ]; then
  echo "${LABEL_LANG_SET//%VALUE%/$CURRENT_LANG}"
else
  echo "$LABEL_LANG_UNSET"
fi

if [ -n "$CURRENT_FORMAT" ]; then
  echo "${LABEL_FORMAT_SET//%VALUE%/$CURRENT_FORMAT}"
else
  echo "$LABEL_FORMAT_UNSET"
fi

if [ -n "$CURRENT_COWORK" ]; then
  echo "${LABEL_COWORK_SET//%VALUE%/$CURRENT_COWORK}"
else
  echo "$LABEL_COWORK_UNSET"
fi
