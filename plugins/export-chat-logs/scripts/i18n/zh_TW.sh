# 繁體中文 locale strings for shell scripts (upload.sh, save-config.sh)

# upload.sh - error / warning
ERR_NOT_CONFIGURED="❌ 尚未設定，請執行：/export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token 為空，請執行：/export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id 為空，請執行：/export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  過去 %DAYS% 天內未找到任何對話，跳過。"
ERR_STATS_FAILED="❌ 統計生成失敗，詳情請查看 %LOG_FILE%。"
ERR_TELEGRAM_FAILED="❌ Telegram 上傳失敗（%ENDPOINT%）。請確認 token、chat_id 與網路。"

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
ERR_TOKEN_REQUIRED="❌ 需要提供 Token：bash save-config.sh <token> <chat_id> [timezone] [lang] [format] [cowork]"
ERR_CHATID_REQUIRED="❌ 需要提供 Chat ID：bash save-config.sh <token> <chat_id> [timezone] [lang] [format] [cowork]"
MSG_CONFIG_SAVED="✅ 設定已儲存（Token + Chat ID + 時區 %TZ_LABEL% + 語言 %LANG% + 格式 %FORMAT% + Cowork %COWORK%）"

# install-launchd.sh - weekday names (launchd: 0/7=Sunday, 1=Monday, ..., 6=Saturday)
LAUNCHD_DAY_0="日"
LAUNCHD_DAY_1="一"
LAUNCHD_DAY_2="二"
LAUNCHD_DAY_3="三"
LAUNCHD_DAY_4="四"
LAUNCHD_DAY_5="五"
LAUNCHD_DAY_6="六"
LAUNCHD_DAY_7="日"

# install-launchd.sh - terminal success message
MSG_LAUNCHD_INSTALLED="✅ launchd agent 已安裝並載入。"
ERR_LAUNCHD_NOT_LOADED="❌ launchd agent 未載入：%PLIST_LABEL%。請檢查 %PLIST_FILE% 後重新執行。"
MSG_LAUNCHD_SCHEDULE="排程：每週%DAY_NAME% %HH_MM%（本地時間）"
MSG_LAUNCHD_PLIST="Plist：%PLIST_FILE%"
MSG_LAUNCHD_LOG="Log：  %LOG_FILE%"
MSG_LAUNCHD_TEST="立即測試執行："
MSG_LAUNCHD_REMOVE="移除："
MSG_LAUNCHD_SUMMARY_SAVED="摘要已儲存：%SUMMARY_FILE%"

# install-launchd.sh - markdown summary file
LAUNCHD_MD_TITLE="# export-chat-logs 自動匯出"
LAUNCHD_MD_SCHEDULE="排程"
LAUNCHD_MD_SCHEDULE_VAL="每週%DAY_NAME% %HH_MM%（本地時間）"
LAUNCHD_MD_LOG="Log"
LAUNCHD_MD_COMMANDS="## 指令"
LAUNCHD_MD_TEST="立即測試執行："
LAUNCHD_MD_REMOVE="移除："

# auto/SKILL.md - 格式化排程時間為自然語言（例如「每週一下午五點」）
# 用法：fmt_schedule_natural <weekday 0-6> <hour 0-23> <minute 0-59>
fmt_schedule_natural() {
  local _w=$1 _h=$2 _m=$3
  local _day_var="LAUNCHD_DAY_${_w}"
  local _day="${!_day_var}"
  local _period _h12
  if [ "$_h" -lt 6 ]; then _period="凌晨"; _h12=$_h
  elif [ "$_h" -lt 12 ]; then _period="上午"; _h12=$_h
  elif [ "$_h" -eq 12 ]; then _period="中午"; _h12=12
  elif [ "$_h" -lt 19 ]; then _period="下午"; _h12=$((_h - 12))
  else _period="晚上"; _h12=$((_h - 12))
  fi
  local _cn=("" "一" "二" "三" "四" "五" "六" "七" "八" "九" "十" "十一" "十二")
  local _hour_str="${_cn[$_h12]}"
  if [ "$_m" -eq 0 ]; then
    printf "每週%s%s%s點" "$_day" "$_period" "$_hour_str"
  elif [ "$_m" -eq 30 ]; then
    printf "每週%s%s%s點半" "$_day" "$_period" "$_hour_str"
  else
    printf "每週%s%s%s點%d分" "$_day" "$_period" "$_hour_str" "$_m"
  fi
}
