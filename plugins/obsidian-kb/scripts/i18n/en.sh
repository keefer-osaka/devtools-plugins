# English locale strings for obsidian-kb shell scripts

# save-config.sh
MSG_CONFIG_SAVED="✅ Configuration saved (Vault: %VAULT_DIR% | Lang: %LANG% | qmd: %QMD_BIN% | Collection: %QMD_COLLECTION%)"

# init-vault.sh
MSG_VAULT_EXISTS="❌ Vault already has wiki/ or _schema/ — aborting init to prevent data loss."
MSG_VAULT_INITIALIZED="✅ Vault initialized at %VAULT_DIR%"

# install-vault-skills.sh
MSG_SKILLS_ALREADY_CURRENT="✅ In-vault skills are already at version %VERSION% — nothing to update."
MSG_SKILLS_INSTALLED="✅ In-vault skills installed (version %VERSION%) at %VAULT_DIR%/.claude/skills/"
MSG_SKILLS_UPGRADED="✅ In-vault skills upgraded from %OLD_VERSION% → %NEW_VERSION%. Backup: %BACKUP_DIR%"
MSG_KB_WIKI_RETIRED="ℹ️  Moved existing kb-wiki/ to backup — use /obsidian-kb:search instead."
MSG_NEXT_STEPS="→ Start Claude Code in your vault directory to use /kb-ingest, /kb-lint, /kb-stats
→ To sync skills after a plugin upgrade, run: /obsidian-kb:upgrade"

# search.sh / search skill
ERR_NOT_CONFIGURED="❌ Not configured. Please run: /obsidian-kb:setup"
ERR_QMD_NOT_FOUND="❌ qmd not found. Configure it with /obsidian-kb:setup or install via: bun install -g @tobilu/qmd"
MSG_QMD_FALLBACK="⚠️  qmd unavailable — falling back to wiki/index.md for manual navigation."
MSG_NO_RESULTS="No results found. Falling back to lex search..."
MSG_NO_RESULTS_LEX="No results in lex search either. Reading wiki/index.md for manual navigation."

# upgrade skill
ERR_VAULT_NOT_SET="❌ VAULT_DIR not set. Please run: /obsidian-kb:setup"
ERR_VAULT_INVALID="❌ Vault directory is invalid (missing wiki/ or _schema/). Please run: /obsidian-kb:setup"
MSG_UPGRADE_DONE="✅ Upgrade complete."
MSG_UPGRADE_NOOP="✅ Already up to date (version %VERSION%)."
