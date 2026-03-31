#!/usr/bin/env bash
# save-token.sh - Save Telegram Bot Token, chat_id, timezone offset, language, output format, and Cowork inclusion
# Usage: bash save-token.sh [token] [chat_id] [timezone_offset] [lang] [format] [include_cowork]
#   Pass empty string "" or "skip" or "-" to keep the existing value for any argument.
#   timezone_offset: integer, e.g. 8 for UTC+8 (Taiwan), 9 for UTC+9 (Japan), default 8
#   lang: en or zh-TW, default en
#   format: html or md, default html
#   include_cowork: true or false, default false

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"

# Load locale strings (before validation so error messages are localized)
source "$(dirname "$0")/i18n/load.sh"

mkdir -p "$DATA_DIR"

# Normalize "skip" / "-" to empty string for all arguments
[ "$1" = "skip" ] || [ "$1" = "-" ] && set -- "" "${@:2}"
[ "$2" = "skip" ] || [ "$2" = "-" ] && set -- "$1" "" "${@:3}"
[ "$3" = "skip" ] || [ "$3" = "-" ] && set -- "$1" "$2" "" "${@:4}"
[ "$4" = "skip" ] || [ "$4" = "-" ] && set -- "$1" "$2" "$3" "" "${@:5}"
[ "$5" = "skip" ] || [ "$5" = "-" ] && set -- "$1" "$2" "$3" "$4" "" "$6"
[ "$6" = "skip" ] || [ "$6" = "-" ] && set -- "$1" "$2" "$3" "$4" "$5" ""

# Token: use first argument if provided, otherwise keep existing, otherwise error
if [ -n "$1" ]; then
  TELEGRAM_BOT_TOKEN="$1"
elif [ -f "$ENV_FILE" ]; then
  TELEGRAM_BOT_TOKEN=$(grep 'TELEGRAM_BOT_TOKEN' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "$ERR_TOKEN_REQUIRED"
    exit 1
  fi
else
  echo "$ERR_TOKEN_REQUIRED"
  exit 1
fi

# Chat ID: use second argument if provided, otherwise keep existing, otherwise error
if [ -n "$2" ]; then
  TELEGRAM_CHAT_ID="$2"
elif [ -f "$ENV_FILE" ]; then
  TELEGRAM_CHAT_ID=$(grep 'TELEGRAM_CHAT_ID' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "$ERR_CHATID_REQUIRED"
    exit 1
  fi
else
  echo "$ERR_CHATID_REQUIRED"
  exit 1
fi

# Timezone: use third argument if provided, otherwise keep existing setting, otherwise default to 8 (UTC+8)
if [ -n "$3" ]; then
  TZ_OFFSET="$3"
elif [ -f "$ENV_FILE" ]; then
  TZ_OFFSET=$(grep 'TIMEZONE_OFFSET' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  TZ_OFFSET="${TZ_OFFSET:-8}"
else
  TZ_OFFSET="8"
fi

# Language: use fourth argument if provided, otherwise keep existing setting, otherwise default to en
if [ -n "$4" ]; then
  PLUGIN_LANG="$4"
elif [ -f "$ENV_FILE" ]; then
  PLUGIN_LANG=$(grep 'PLUGIN_LANG' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  PLUGIN_LANG="${PLUGIN_LANG:-en}"
else
  PLUGIN_LANG="en"
fi

# Output format: use fifth argument if provided, otherwise keep existing setting, otherwise default to html
if [ -n "$5" ]; then
  OUTPUT_FORMAT="$5"
elif [ -f "$ENV_FILE" ]; then
  OUTPUT_FORMAT=$(grep 'OUTPUT_FORMAT' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  OUTPUT_FORMAT="${OUTPUT_FORMAT:-html}"
else
  OUTPUT_FORMAT="html"
fi

# Include Cowork: use sixth argument if provided, otherwise keep existing setting, otherwise default to false
if [ -n "$6" ]; then
  INCLUDE_COWORK="$6"
elif [ -f "$ENV_FILE" ]; then
  INCLUDE_COWORK=$(grep 'INCLUDE_COWORK' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
  INCLUDE_COWORK="${INCLUDE_COWORK:-false}"
else
  INCLUDE_COWORK="false"
fi

printf 'TELEGRAM_BOT_TOKEN=%s\nTELEGRAM_CHAT_ID=%s\nTIMEZONE_OFFSET=%s\nPLUGIN_LANG=%s\nOUTPUT_FORMAT=%s\nINCLUDE_COWORK=%s\n' \
  "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_CHAT_ID" "$TZ_OFFSET" "$PLUGIN_LANG" "$OUTPUT_FORMAT" "$INCLUDE_COWORK" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
TZ_LABEL=$(printf "UTC%+d" "$TZ_OFFSET")
_msg="${MSG_CONFIG_SAVED//%TZ_LABEL%/$TZ_LABEL}"
_msg="${_msg//%LANG%/$PLUGIN_LANG}"
_msg="${_msg//%FORMAT%/$OUTPUT_FORMAT}"
_msg="${_msg//%COWORK%/$INCLUDE_COWORK}"
echo "$_msg"
