#!/usr/bin/env bash
# save-config.sh - Save protoc-java-gen configuration
# Usage: bash save-config.sh [protoc_path] [project_root] [proto_dir] [lang]
#   Pass "skip" or "-" to keep the existing value for any argument.
#   proto_dir: relative to project_root, default "proto"
#   lang: en or zh-TW, default en

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/protoc-java-gen"
ENV_FILE="$DATA_DIR/.env"

source "$(dirname "$0")/i18n/load.sh"

mkdir -p "$DATA_DIR"

# Normalize "skip" / "-" to empty string
[ "$1" = "skip" ] || [ "$1" = "-" ] && set -- "" "${@:2}"
[ "$2" = "skip" ] || [ "$2" = "-" ] && set -- "$1" "" "${@:3}"
[ "$3" = "skip" ] || [ "$3" = "-" ] && set -- "$1" "$2" "" "$4"
[ "$4" = "skip" ] || [ "$4" = "-" ] && set -- "$1" "$2" "$3" ""

# PROTOC_PATH
if [ -n "$1" ]; then
  PROTOC_PATH="$1"
elif [ -f "$ENV_FILE" ]; then
  PROTOC_PATH=$(read_env_val PROTOC_PATH)
fi

# PROJECT_ROOT
if [ -n "$2" ]; then
  PROJECT_ROOT="$2"
elif [ -f "$ENV_FILE" ]; then
  PROJECT_ROOT=$(read_env_val PROJECT_ROOT)
fi

# PROTO_DIR
if [ -n "$3" ]; then
  PROTO_DIR="$3"
elif [ -f "$ENV_FILE" ]; then
  PROTO_DIR=$(read_env_val PROTO_DIR)
  PROTO_DIR="${PROTO_DIR:-proto}"
else
  PROTO_DIR="proto"
fi

# PLUGIN_LANG
if [ -n "$4" ]; then
  PLUGIN_LANG="$4"
elif [ -f "$ENV_FILE" ]; then
  PLUGIN_LANG=$(read_env_val PLUGIN_LANG)
  PLUGIN_LANG="${PLUGIN_LANG:-en}"
else
  PLUGIN_LANG="en"
fi

printf 'PROTOC_PATH=%s\nPROJECT_ROOT=%s\nPROTO_DIR=%s\nPLUGIN_LANG=%s\n' \
  "$PROTOC_PATH" "$PROJECT_ROOT" "$PROTO_DIR" "$PLUGIN_LANG" > "$ENV_FILE"
chmod 600 "$ENV_FILE"

_msg="${MSG_CONFIG_SAVED//%PROTOC_PATH%/$PROTOC_PATH}"
_msg="${_msg//%PROJECT_ROOT%/$PROJECT_ROOT}"
_msg="${_msg//%PROTO_DIR%/$PROTO_DIR}"
_msg="${_msg//%LANG%/$PLUGIN_LANG}"
echo "$_msg"
