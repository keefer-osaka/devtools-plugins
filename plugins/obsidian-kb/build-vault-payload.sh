#!/usr/bin/env bash
# build-vault-payload.sh - Dev-time tool: sync skills from the live vault into vault-payload/
# and template-ize hardcoded paths to __VAULT_DIR__.
#
# Usage: bash build-vault-payload.sh [<vault_dir>]
#   Default vault_dir: $HOME/claude-code/Obsidian
#
# Run this whenever kb-ingest/kb-lint/kb-stats SKILL.md or scripts are updated in the vault.

set -euo pipefail

VAULT_DIR="${1:-$HOME/claude-code/Obsidian}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD_SKILLS="$SCRIPT_DIR/vault-payload/.claude/skills"
PAYLOAD_TEMPLATES="$SCRIPT_DIR/vault-payload/_schema/templates"

echo "=== build-vault-payload.sh ==="
echo "Source vault: $VAULT_DIR"
echo "Target:       $SCRIPT_DIR/vault-payload/"
echo ""

# Verify source exists
for skill in kb-ingest kb-lint kb-stats; do
  if [ ! -d "$VAULT_DIR/.claude/skills/$skill" ]; then
    echo "❌ Missing: $VAULT_DIR/.claude/skills/$skill" >&2
    exit 1
  fi
done

# Create destination directories
mkdir -p \
  "$PAYLOAD_SKILLS/kb-ingest/scripts" \
  "$PAYLOAD_SKILLS/kb-lint/scripts" \
  "$PAYLOAD_SKILLS/kb-stats/scripts" \
  "$PAYLOAD_TEMPLATES"

# ── kb-ingest ──────────────────────────────────────────────────────────────
echo "→ Syncing kb-ingest..."
rsync -a --delete \
  "$VAULT_DIR/.claude/skills/kb-ingest/scripts/" \
  "$PAYLOAD_SKILLS/kb-ingest/scripts/"

cp "$VAULT_DIR/.claude/skills/kb-ingest/SKILL.md" \
   "$PAYLOAD_SKILLS/kb-ingest/SKILL.md"

# ── kb-lint ────────────────────────────────────────────────────────────────
echo "→ Syncing kb-lint..."
rsync -a --delete \
  "$VAULT_DIR/.claude/skills/kb-lint/scripts/" \
  "$PAYLOAD_SKILLS/kb-lint/scripts/"

cp "$VAULT_DIR/.claude/skills/kb-lint/SKILL.md" \
   "$PAYLOAD_SKILLS/kb-lint/SKILL.md"

# ── kb-stats ───────────────────────────────────────────────────────────────
echo "→ Syncing kb-stats..."
rsync -a --delete \
  "$VAULT_DIR/.claude/skills/kb-stats/scripts/" \
  "$PAYLOAD_SKILLS/kb-stats/scripts/"

cp "$VAULT_DIR/.claude/skills/kb-stats/SKILL.md" \
   "$PAYLOAD_SKILLS/kb-stats/SKILL.md"

# ── Templates ──────────────────────────────────────────────────────────────
echo "→ Syncing templates..."
rsync -a --delete \
  "$VAULT_DIR/_schema/templates/" \
  "$PAYLOAD_TEMPLATES/"

# ── Template-ize hardcoded vault path in SKILL.md files ───────────────────
echo "→ Replacing '$VAULT_DIR' → '__VAULT_DIR__' in SKILL.md files..."
find "$PAYLOAD_SKILLS" -name "SKILL.md" -exec sed -i '' "s|$VAULT_DIR|__VAULT_DIR__|g" {} +

# ── Write _version file ────────────────────────────────────────────────────
source "$SCRIPT_DIR/scripts/plugin-version.sh"
PLUGIN_VERSION=$(plugin_version "$SCRIPT_DIR")
printf '%s' "$PLUGIN_VERSION" > "$PAYLOAD_SKILLS/_version"
echo "→ _version = $PLUGIN_VERSION"

# ── Verify: no absolute paths should remain in SKILL.md ───────────────────
echo ""
echo "=== Verification ==="
LEAKED=$(grep -r "$VAULT_DIR" "$PAYLOAD_SKILLS" --include="*.md" -l 2>/dev/null || true)
if [ -n "$LEAKED" ]; then
  echo "❌ Found leaked absolute paths in:" >&2
  echo "$LEAKED" >&2
  exit 1
fi

# Also check Python scripts don't reference VAULT_DIR directly
# (they should use __file__ dirname resolution — not hardcoded paths)
PY_HARDCODED=$(grep -r "claude-code/Obsidian" "$PAYLOAD_SKILLS" --include="*.py" -l 2>/dev/null || true)
if [ -n "$PY_HARDCODED" ]; then
  echo "⚠️  Python scripts with hardcoded Obsidian path (verify these use __file__ dirname):" >&2
  echo "$PY_HARDCODED" >&2
fi

echo "✅ vault-payload/ is clean — no hardcoded vault paths in SKILL.md files"
echo ""
echo "Files in vault-payload/.claude/skills/:"
find "$PAYLOAD_SKILLS" -type f | sort
