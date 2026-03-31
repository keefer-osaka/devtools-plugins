# 繁體中文 locale strings for shell scripts (export.sh, setup.sh, save-token.sh)

# export.sh - error / warning
ERR_NOT_CONFIGURED="❌ 尚未設定，請執行：/export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token 為空，請執行：/export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id 為空，請執行：/export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  過去 %DAYS% 天內未找到任何對話，跳過。"

# export.sh - summary text (Telegram message)
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
LABEL_COWORK_SET="包含 Cowork：%VALUE%"
LABEL_COWORK_UNSET="包含 Cowork：（未設定，預設 false）"

# save-token.sh
ERR_TOKEN_REQUIRED="❌ 需要提供 Token：bash save-token.sh <token> <chat_id> [timezone] [lang] [format]"
ERR_CHATID_REQUIRED="❌ 需要提供 Chat ID：bash save-token.sh <token> <chat_id> [timezone] [lang] [format]"
MSG_CONFIG_SAVED="✅ 設定已儲存（Token + Chat ID + 時區 %TZ_LABEL% + 語言 %LANG% + 格式 %FORMAT% + Cowork %COWORK%）"

# setup.sh - labels
LABEL_BOT_TOKEN_SET="Bot Token：%VALUE%"
LABEL_BOT_TOKEN_UNSET="Bot Token：（未設定）"
LABEL_CHAT_ID_SET="Chat ID：%VALUE%"
LABEL_CHAT_ID_UNSET="Chat ID：（未設定）"
LABEL_TIMEZONE_SET="時區：%VALUE%"
LABEL_TIMEZONE_UNSET="時區：（未設定，預設 UTC+8）"
LABEL_LANG_SET="語言：%VALUE%"
LABEL_LANG_UNSET="語言：（未設定，預設 en）"
LABEL_FORMAT_SET="輸出格式：%VALUE%"
LABEL_FORMAT_UNSET="輸出格式：（未設定，預設 html）"
