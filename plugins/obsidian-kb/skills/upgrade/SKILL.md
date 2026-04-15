---
name: upgrade
description: "Upgrade the in-vault knowledge base maintenance scripts (kb-ingest/kb-lint/kb-stats) to match the currently installed obsidian-kb plugin version. Run this after upgrading the plugin itself."
allowed-tools:
  - Bash
disable-model-invocation: true
---

# obsidian-kb Upgrade

Synchronize the vault's in-vault skills with the current plugin version. No interaction required.

## Step 1 — Load configuration

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/load-env.sh"
source "${CLAUDE_PLUGIN_ROOT}/scripts/i18n/load.sh"
```

## Step 2 — Validate

If `VAULT_DIR` is empty:
```bash
echo "$ERR_VAULT_NOT_SET"
exit 1
```

If `VAULT_DIR` exists but is missing `wiki/` or `_schema/`:
```bash
echo "$ERR_VAULT_INVALID"
exit 1
```

## Step 3 — Run install-vault-skills with --force

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/install-vault-skills.sh" "$VAULT_DIR" --force
```

The script handles:
- Version comparison (prints "already up to date" if version matches, unless --force)
- Backup of existing skills to `.backup-<timestamp>/`
- rsync of new vault-payload into `$VAULT_DIR/.claude/skills/`
- `__VAULT_DIR__` placeholder substitution in SKILL.md files
- Writing `_version` and `_installed-by` markers
- Retiring `kb-wiki/` if present

## Step 4 — Done

The script prints the result. No further action needed.
