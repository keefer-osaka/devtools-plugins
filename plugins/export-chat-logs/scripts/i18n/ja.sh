# 日本語 locale strings for shell scripts (upload.sh, save-config.sh)

# upload.sh - error / warning
ERR_NOT_CONFIGURED="❌ 未設定です。実行してください：/export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token が空です。実行してください：/export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id が空です。実行してください：/export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  過去 %DAYS% 日間にセッションが見つかりませんでした。スキップします。"
ERR_STATS_FAILED="❌ 統計の生成に失敗しました。%LOG_FILE% を確認してください。"
ERR_TELEGRAM_FAILED="❌ Telegram へのアップロードに失敗しました（%ENDPOINT%）。token・chat_id・ネットワークを確認してください。"

# upload.sh - summary text (Telegram message)
SUMMARY_HEADER="📦 チャットログエクスポート"
SUMMARY_USER="👤 ユーザー：%GIT_USER%"
SUMMARY_PERIOD="📅 期間：%START_DATE% ~ %TODAY%（過去 %DAYS% 日間）"
SUMMARY_STATS="📊 統計：%CC_SESSIONS% セッション"
SUMMARY_SIZE="💾 ファイルサイズ：%ZIP_SIZE%"
SUMMARY_FORMAT_HTML="📝 形式：HTML（シンタックスハイライト + インタラクティブグラフ）"
SUMMARY_FORMAT_MD="📝 形式：Markdown（ツール呼び出しと技術的詳細は省略）"
MSG_DONE="✅ 完了！Claude Code：%CC_SESSIONS% セッション、zip：%ZIP_SIZE%、Telegram に送信済み"
STATS_REPORT_SLUG="claude-code_使用レポート"
STATS_REPORT_SLUG_COWORK="claude-cowork_使用レポート"

# Cowork
SUMMARY_STATS_COWORK="📊 統計：%CC_SESSIONS% セッション（Claude Code）+ %CW_SESSIONS% セッション（Claude Cowork）"
MSG_DONE_COWORK="✅ 完了！Claude Code：%CC_SESSIONS% セッション、Claude Cowork：%CW_SESSIONS% セッション、zip：%ZIP_SIZE%、Telegram に送信済み"

# save-config.sh
ERR_TOKEN_REQUIRED="❌ Token が必要です：bash save-config.sh <token> <chat_id> [timezone] [lang] [format] [cowork]"
ERR_CHATID_REQUIRED="❌ Chat ID が必要です：bash save-config.sh <token> <chat_id> [timezone] [lang] [format] [cowork]"
MSG_CONFIG_SAVED="✅ 設定を保存しました（Token + Chat ID + タイムゾーン %TZ_LABEL% + 言語 %LANG% + 形式 %FORMAT% + Cowork %COWORK%）"

# install-launchd.sh - weekday names (launchd: 0/7=Sunday, 1=Monday, ..., 6=Saturday)
LAUNCHD_DAY_0="日曜日"
LAUNCHD_DAY_1="月曜日"
LAUNCHD_DAY_2="火曜日"
LAUNCHD_DAY_3="水曜日"
LAUNCHD_DAY_4="木曜日"
LAUNCHD_DAY_5="金曜日"
LAUNCHD_DAY_6="土曜日"
LAUNCHD_DAY_7="日曜日"

# install-launchd.sh - terminal success message
MSG_LAUNCHD_INSTALLED="✅ launchd エージェントをインストールして読み込みました。"
ERR_LAUNCHD_NOT_LOADED="❌ launchd エージェントの読み込みに失敗しました：%PLIST_LABEL%。%PLIST_FILE% を確認して再実行してください。"
MSG_LAUNCHD_SCHEDULE="スケジュール：毎週%DAY_NAME% %HH_MM%（ローカル時間）"
MSG_LAUNCHD_PLIST="Plist：%PLIST_FILE%"
MSG_LAUNCHD_LOG="ログ：  %LOG_FILE%"
MSG_LAUNCHD_TEST="すぐにテスト実行："
MSG_LAUNCHD_REMOVE="削除するには："
MSG_LAUNCHD_SUMMARY_SAVED="サマリー保存先：%SUMMARY_FILE%"

# install-launchd.sh - markdown summary file
LAUNCHD_MD_TITLE="# export-chat-logs 自動エクスポート"
LAUNCHD_MD_SCHEDULE="スケジュール"
LAUNCHD_MD_SCHEDULE_VAL="毎週%DAY_NAME% %HH_MM%（ローカル時間）"
LAUNCHD_MD_LOG="ログ"
LAUNCHD_MD_COMMANDS="## コマンド"
LAUNCHD_MD_TEST="すぐにテスト実行："
LAUNCHD_MD_REMOVE="削除するには："

# auto/SKILL.md - スケジュールを自然言語でフォーマット（例：「毎週月曜日の午後5時」）
# 使用法：fmt_schedule_natural <weekday 0-6> <hour 0-23> <minute 0-59>
fmt_schedule_natural() {
  local _w=$1 _h=$2 _m=$3
  local _day_var="LAUNCHD_DAY_${_w}"
  local _day="${!_day_var}"
  local _period _h12
  if [ "$_h" -lt 12 ]; then _period="午前"; _h12=$_h
  elif [ "$_h" -eq 12 ]; then _period="正午"; _h12=12
  else _period="午後"; _h12=$((_h - 12))
  fi
  if [ "$_m" -eq 0 ]; then
    printf "毎週%sの%s%d時" "$_day" "$_period" "$_h12"
  elif [ "$_m" -eq 30 ]; then
    printf "毎週%sの%s%d時半" "$_day" "$_period" "$_h12"
  else
    printf "毎週%sの%s%d時%d分" "$_day" "$_period" "$_h12" "$_m"
  fi
}
