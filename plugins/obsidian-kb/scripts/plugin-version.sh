#!/usr/bin/env bash
# plugin_version <plugin_root> — Print version from .claude-plugin/plugin.json
# Usage: source plugin-version.sh; PLUGIN_VERSION=$(plugin_version "$PLUGIN_ROOT")
plugin_version() {
  local pj="$1/.claude-plugin/plugin.json"
  if command -v rg >/dev/null 2>&1; then
    rg -o '"version"\s*:\s*"([^"]+)"' --replace '$1' "$pj" | head -1
  else
    grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$pj" \
      | head -1 | sed 's/.*"\([^"]*\)"$/\1/'
  fi
}
