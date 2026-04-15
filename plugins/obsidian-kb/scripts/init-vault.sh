#!/usr/bin/env bash
# init-vault.sh - Initialize a new Obsidian vault skeleton
# Usage: bash init-vault.sh <vault_dir>

set -euo pipefail

VAULT_DIR="${1:-}"
VAULT_DIR="${VAULT_DIR/#\~/$HOME}"
if [ -z "$VAULT_DIR" ]; then
  echo "Usage: bash init-vault.sh <vault_dir>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="${SCRIPT_DIR%/*}"

source "$SCRIPT_DIR/i18n/load.sh"
source "$SCRIPT_DIR/vault-lib.sh"

# Abort if vault is existing or partial — avoid overwriting data
_vs=$(vault_state "$VAULT_DIR")
if [ "$_vs" = "existing" ] || [ "$_vs" = "partial" ]; then
  echo "$MSG_VAULT_EXISTS" >&2
  exit 1
fi

mkdir -p "$VAULT_DIR"
rsync -a "$PLUGIN_ROOT/vault-bootstrap/wiki/" "$VAULT_DIR/wiki/"

mkdir -p "$VAULT_DIR/_schema/templates"
printf '{}' > "$VAULT_DIR/_schema/sessions.json"
printf '0' > "$VAULT_DIR/_schema/.watermark"
printf '0' > "$VAULT_DIR/_schema/.all_watermark"
rsync -a "$PLUGIN_ROOT/vault-payload/_schema/templates/" "$VAULT_DIR/_schema/templates/"

mkdir -p "$VAULT_DIR/transcripts"

fmt "$MSG_VAULT_INITIALIZED" VAULT_DIR "$VAULT_DIR"
