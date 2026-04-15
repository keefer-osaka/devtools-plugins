#!/usr/bin/env bash
# save-config.sh - Save Telegram Bot Token, chat_id, timezone offset, language, output format, and Cowork inclusion
# Usage: bash save-config.sh [token] [chat_id] [timezone_offset] [lang] [format] [include_cowork]
#   Pass empty string "" or "skip" or "-" to keep the existing value for any argument.
#   timezone_offset: integer, e.g. 8 for UTC+8 (Taiwan), 9 for UTC+9 (Japan), default 8
#   lang: en or zh-TW, default en
#   format: html or md, default html
#   include_cowork: true or false, default false

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/export-chat-logs"
ENV_FILE="$DATA_DIR/.env"

# Load locale strings (before validation so error messages are localized)
source "$(dirname "$0")/i18n/load.sh"

[ $# -eq 6 ] || { echo "Usage: bash save-config.sh <token> <chat_id> <tz_offset> <lang> <format> <include_cowork>" >&2; exit 2; }

mkdir -p "$DATA_DIR"

normalize_skip_args "$@"; set -- "${_NORMALIZED_ARGS[@]}"

# Token: use first argument if provided, otherwise keep existing, otherwise error
if [ -n "$1" ]; then
  TELEGRAM_BOT_TOKEN="$1"
elif [ -f "$ENV_FILE" ]; then
  TELEGRAM_BOT_TOKEN=$(read_env_val TELEGRAM_BOT_TOKEN)
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
  TELEGRAM_CHAT_ID=$(read_env_val TELEGRAM_CHAT_ID)
  if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "$ERR_CHATID_REQUIRED"
    exit 1
  fi
else
  echo "$ERR_CHATID_REQUIRED"
  exit 1
fi

TZ_OFFSET=$(resolve_arg "$3" TIMEZONE_OFFSET "8")
PLUGIN_LANG=$(resolve_arg "$4" PLUGIN_LANG "en")
OUTPUT_FORMAT=$(resolve_arg "$5" OUTPUT_FORMAT "html")
INCLUDE_COWORK=$(resolve_arg "$6" INCLUDE_COWORK "false")

printf 'TELEGRAM_BOT_TOKEN=%s\nTELEGRAM_CHAT_ID=%s\nTIMEZONE_OFFSET=%s\nPLUGIN_LANG=%s\nOUTPUT_FORMAT=%s\nINCLUDE_COWORK=%s\n' \
  "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_CHAT_ID" "$TZ_OFFSET" "$PLUGIN_LANG" "$OUTPUT_FORMAT" "$INCLUDE_COWORK" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
TZ_LABEL=$(printf "UTC%+d" "$TZ_OFFSET")
_msg="${MSG_CONFIG_SAVED//%TZ_LABEL%/$TZ_LABEL}"
_msg="${_msg//%LANG%/$PLUGIN_LANG}"
_msg="${_msg//%FORMAT%/$OUTPUT_FORMAT}"
_msg="${_msg//%COWORK%/$INCLUDE_COWORK}"
echo "$_msg"
