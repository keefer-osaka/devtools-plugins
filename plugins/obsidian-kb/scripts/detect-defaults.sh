#!/usr/bin/env bash
# detect-defaults.sh - Print default vault dir + qmd binary suggestions for setup.
set -euo pipefail
# Output (two lines):
#   DETECTED_VAULT=<path>    (always set; fallback $HOME/Obsidian)
#   DETECTED_QMD=<path|>     (empty string if not found)

if [ -d "$HOME/claude-code/Obsidian" ]; then _v="$HOME/claude-code/Obsidian"
else _v="$HOME/Obsidian"; fi
printf 'DETECTED_VAULT=%s\n' "$_v"

_q="$(command -v qmd 2>/dev/null || true)"
[ -z "$_q" ] && [ -x "$HOME/.bun/bin/qmd" ] && _q="$HOME/.bun/bin/qmd"
[ -z "$_q" ] && [ -x "/usr/local/bin/qmd" ] && _q="/usr/local/bin/qmd"
printf 'DETECTED_QMD=%s\n' "$_q"
