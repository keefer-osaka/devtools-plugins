# 繁體中文 locale strings for shell scripts (upload.sh, save-config.sh)

# upload.sh - error / warning
ERR_NOT_CONFIGURED="❌ 尚未設定，請執行：/export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token 為空，請執行：/export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id 為空，請執行：/export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  過去 %DAYS% 天內未找到任何對話，跳過。"

# upload.sh - summary text (Telegram message)
SUMMARY_HEADER="📦 對話紀錄匯出"
SUMMARY_USER="👤 使用者：%GIT_USER%"
SUMMARY_PERIOD="📅 期間：%START_DATE% ~ %TODAY%（最近 %DAYS% 天）"
SUMMARY_STATS="📊 統計：%CC_SESSIONS% 個對話"
SUMMARY_SIZE="💾 檔案大小：%ZIP_SIZE%"
SUMMARY_FORMAT_HTML="📝 格式：HTML（語法高亮 + 互動式圖表）"
SUMMARY_FORMAT_MD="📝 格式：Markdown（已省略工具呼叫與技術細節）"
MSG_DONE="✅ 完成！Claude Code：%CC_SESSIONS% 個對話，壓縮檔：%ZIP_SIZE%，已傳送至 Telegram"
STATS_REPORT_SLUG="claude-code_使用報告"
STATS_REPORT_SLUG_COWORK="claude-cowork_使用報告"

# Cowork
SUMMARY_STATS_COWORK="📊 統計：%CC_SESSIONS% 個對話（Claude Code）+ %CW_SESSIONS% 個對話（Claude Cowork）"
MSG_DONE_COWORK="✅ 完成！Claude Code：%CC_SESSIONS% 個對話，Claude Cowork：%CW_SESSIONS% 個對話，壓縮檔：%ZIP_SIZE%，已傳送至 Telegram"

# save-config.sh
ERR_TOKEN_REQUIRED="❌ 需要提供 Token：bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
ERR_CHATID_REQUIRED="❌ 需要提供 Chat ID：bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
MSG_CONFIG_SAVED="✅ 設定已儲存（Token + Chat ID + 時區 %TZ_LABEL% + 語言 %LANG% + 格式 %FORMAT% + Cowork %COWORK%）"
