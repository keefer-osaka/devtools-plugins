# 日本語 locale strings for obsidian-kb shell scripts

# save-config.sh
MSG_CONFIG_SAVED="✅ 設定を保存しました（Vault: %VAULT_DIR% | 言語: %LANG% | qmd: %QMD_BIN% | Collection: %QMD_COLLECTION%）"

# init-vault.sh
MSG_VAULT_EXISTS="❌ Vault に wiki/ または _schema/ が既に存在します — データ損失防止のため初期化を中止します。"
MSG_VAULT_INITIALIZED="✅ Vault を初期化しました：%VAULT_DIR%"

# install-vault-skills.sh
MSG_SKILLS_ALREADY_CURRENT="✅ Vault 内のスキルはすでに最新バージョン %VERSION% です — 更新不要。"
MSG_SKILLS_INSTALLED="✅ Vault 内スキルをインストールしました（バージョン %VERSION%）：%VAULT_DIR%/.claude/skills/"
MSG_SKILLS_UPGRADED="✅ Vault 内スキルを %OLD_VERSION% → %NEW_VERSION% にアップグレードしました。バックアップ：%BACKUP_DIR%"
MSG_KB_WIKI_RETIRED="ℹ️  既存の kb-wiki/ をバックアップに移動しました — 代わりに /obsidian-kb:search を使用してください。"
MSG_NEXT_STEPS="→ vault ディレクトリで Claude Code を起動すると /kb-ingest、/kb-lint、/kb-stats が使用できます
→ plugin のアップグレード後は /obsidian-kb:upgrade で vault 内スキルを同期してください"

# search.sh / search skill
ERR_NOT_CONFIGURED="❌ 設定されていません。先に実行してください：/obsidian-kb:setup"
ERR_QMD_NOT_FOUND="❌ qmd が見つかりません。/obsidian-kb:setup で設定するか、インストール：bun install -g @tobilu/qmd"
MSG_QMD_FALLBACK="⚠️  qmd が利用できません — wiki/index.md で手動ナビゲーションにフォールバックします。"
MSG_NO_RESULTS="結果が見つかりません。lex 検索にフォールバック中..."
MSG_NO_RESULTS_LEX="lex 検索でも結果なし。wiki/index.md で手動ナビゲーションします。"

# upgrade skill
ERR_VAULT_NOT_SET="❌ VAULT_DIR が設定されていません。先に実行してください：/obsidian-kb:setup"
ERR_VAULT_INVALID="❌ Vault ディレクトリが無効です（wiki/ または _schema/ がありません）。先に実行してください：/obsidian-kb:setup"
MSG_UPGRADE_DONE="✅ アップグレード完了。"
MSG_UPGRADE_NOOP="✅ すでに最新バージョン（%VERSION%）です — 更新不要。"
