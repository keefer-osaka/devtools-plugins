#!/usr/bin/env bash
# load-env.sh - Load obsidian-kb .env values into environment variables
# Usage: source "$(dirname "$0")/load-env.sh"
# After sourcing: VAULT_DIR, PLUGIN_LANG, QMD_BIN, QMD_COLLECTION are set

_DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/obsidian-kb"
_ENV_FILE="$_DATA_DIR/.env"

VAULT_DIR=""
PLUGIN_LANG="en"
QMD_BIN=""
QMD_COLLECTION="obsidian-wiki"

if [ -f "$_ENV_FILE" ]; then
  while IFS= read -r _line; do
    _k="${_line%%=*}"
    _v="${_line#*=}"; _v="${_v//\"/}"; _v="${_v//\'/}"; _v="${_v// /}"
    case "$_k" in
      VAULT_DIR)      [ -n "$_v" ] && VAULT_DIR="$_v" ;;
      PLUGIN_LANG)    [ -n "$_v" ] && PLUGIN_LANG="$_v" ;;
      QMD_BIN)        [ -n "$_v" ] && QMD_BIN="$_v" ;;
      QMD_COLLECTION) [ -n "$_v" ] && QMD_COLLECTION="$_v" ;;
    esac
  done < "$_ENV_FILE"
fi
