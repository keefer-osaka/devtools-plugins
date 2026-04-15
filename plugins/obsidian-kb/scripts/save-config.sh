#!/usr/bin/env bash
# save-config.sh - Save obsidian-kb configuration
set -euo pipefail
# Usage: bash save-config.sh [vault_dir] [lang] [qmd_bin] [qmd_collection]
#   Pass empty string "", "skip", or "-" to keep existing value for any argument.
#   vault_dir: absolute path to the Obsidian vault directory
#   lang: en, zh-TW, or ja (default: en)
#   qmd_bin: path to qmd binary, or "none" to disable search (default: auto-detect)
#   qmd_collection: qmd collection name (default: obsidian-wiki)

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/obsidian-kb"
ENV_FILE="$DATA_DIR/.env"

source "$(dirname "$0")/i18n/load.sh"

[ $# -eq 4 ] || { echo "Usage: bash save-config.sh <vault_dir> <lang> <qmd_bin> <qmd_collection>" >&2; exit 2; }

mkdir -p "$DATA_DIR"

normalize_skip_args "$@"; set -- "${_NORMALIZED_ARGS[@]}"

VAULT_DIR=$(resolve_arg "$1" VAULT_DIR "")
[ -n "$VAULT_DIR" ] && VAULT_DIR="${VAULT_DIR/#\~/$HOME}"
PLUGIN_LANG=$(resolve_arg "$2" PLUGIN_LANG "en")
QMD_BIN=$(resolve_arg "$3" QMD_BIN "")
QMD_COLLECTION=$(resolve_arg "$4" QMD_COLLECTION "obsidian-wiki")

printf 'VAULT_DIR=%s\nPLUGIN_LANG=%s\nQMD_BIN=%s\nQMD_COLLECTION=%s\n' \
  "$VAULT_DIR" "$PLUGIN_LANG" "$QMD_BIN" "$QMD_COLLECTION" > "$ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true

fmt "$MSG_CONFIG_SAVED" VAULT_DIR "$VAULT_DIR" LANG "$PLUGIN_LANG" QMD_BIN "${QMD_BIN:-none}" QMD_COLLECTION "$QMD_COLLECTION"
