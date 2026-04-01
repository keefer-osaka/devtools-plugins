# English locale strings for shell scripts (upload.sh, save-config.sh)

# upload.sh - error / warning
ERR_NOT_CONFIGURED="❌ Not configured. Please run: /export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token is empty. Please run: /export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id is empty. Please run: /export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  No sessions found in the last %DAYS% days, skipping."

# upload.sh - summary text (Telegram message)
SUMMARY_HEADER="📦 Chat Log Export"
SUMMARY_USER="👤 User: %GIT_USER%"
SUMMARY_PERIOD="📅 Period: %START_DATE% ~ %TODAY% (last %DAYS% days)"
SUMMARY_STATS="📊 Stats: %CC_SESSIONS% sessions"
SUMMARY_SIZE="💾 File size: %ZIP_SIZE%"
SUMMARY_FORMAT_HTML="📝 Format: HTML (syntax highlighting + interactive charts)"
SUMMARY_FORMAT_MD="📝 Format: Markdown (tool calls and technical details omitted)"
MSG_DONE="✅ Done! Claude Code: %CC_SESSIONS% sessions, zip: %ZIP_SIZE%, sent to Telegram"
STATS_REPORT_SLUG="claude-code_usage-report"
STATS_REPORT_SLUG_COWORK="claude-cowork_usage-report"

# Cowork
SUMMARY_STATS_COWORK="📊 Stats: %CC_SESSIONS% sessions (Claude Code) + %CW_SESSIONS% sessions (Claude Cowork)"
MSG_DONE_COWORK="✅ Done! Claude Code: %CC_SESSIONS% sessions, Claude Cowork: %CW_SESSIONS% sessions, zip: %ZIP_SIZE%, sent to Telegram"

# save-config.sh
ERR_TOKEN_REQUIRED="❌ Token required: bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
ERR_CHATID_REQUIRED="❌ Chat ID required: bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
MSG_CONFIG_SAVED="✅ Configuration saved (Token + Chat ID + Timezone %TZ_LABEL% + Language %LANG% + Format %FORMAT% + Cowork %COWORK%)"
