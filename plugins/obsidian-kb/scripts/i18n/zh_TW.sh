# 繁體中文（台灣）locale strings for obsidian-kb shell scripts

# save-config.sh
MSG_CONFIG_SAVED="✅ 設定已儲存（Vault: %VAULT_DIR% | 語言: %LANG% | qmd: %QMD_BIN% | Collection: %QMD_COLLECTION%）"

# init-vault.sh
MSG_VAULT_EXISTS="❌ Vault 已有 wiki/ 或 _schema/，中止初始化以防資料遺失。"
MSG_VAULT_INITIALIZED="✅ Vault 已初始化：%VAULT_DIR%"

# install-vault-skills.sh
MSG_SKILLS_ALREADY_CURRENT="✅ Vault 內 skills 已是最新版本 %VERSION%，無需更新。"
MSG_SKILLS_INSTALLED="✅ Vault 內 skills 已安裝（版本 %VERSION%）：%VAULT_DIR%/.claude/skills/"
MSG_SKILLS_UPGRADED="✅ Vault 內 skills 已從 %OLD_VERSION% 升級至 %NEW_VERSION%。備份：%BACKUP_DIR%"
MSG_KB_WIKI_RETIRED="ℹ️  已將現有 kb-wiki/ 移至備份——請改用 /obsidian-kb:search。"
MSG_NEXT_STEPS="→ 在 vault 目錄啟動 Claude Code 即可使用 /kb-ingest、/kb-lint、/kb-stats
→ 若日後升級 plugin，請執行 /obsidian-kb:upgrade 同步 vault 內 skills"

# search.sh / search skill
ERR_NOT_CONFIGURED="❌ 尚未設定，請先執行：/obsidian-kb:setup"
ERR_QMD_NOT_FOUND="❌ 找不到 qmd。請執行 /obsidian-kb:setup 設定，或安裝：bun install -g @tobilu/qmd"
MSG_QMD_FALLBACK="⚠️  qmd 無法使用——改為讀取 wiki/index.md 手動導航。"
MSG_NO_RESULTS="無命中結果，改用 lex 搜尋..."
MSG_NO_RESULTS_LEX="lex 搜尋也無命中，讀取 wiki/index.md 手動導航。"

# upgrade skill
ERR_VAULT_NOT_SET="❌ 未設定 VAULT_DIR，請先執行：/obsidian-kb:setup"
ERR_VAULT_INVALID="❌ Vault 目錄不合法（缺少 wiki/ 或 _schema/），請先執行：/obsidian-kb:setup"
MSG_UPGRADE_DONE="✅ 升級完成。"
MSG_UPGRADE_NOOP="✅ 已是最新版本（%VERSION%），無需更新。"
