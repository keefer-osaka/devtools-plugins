# 繁體中文 locale strings for protoc-java-gen

# generate.sh - errors
ERR_NOT_CONFIGURED="❌ 尚未設定，請執行：/protoc-java-gen:setup"
ERR_PROTOC_NOT_FOUND="❌ 找不到 protoc 或無法執行：%PROTOC_PATH%"
ERR_PROTO_DIR_NOT_FOUND="❌ Proto 目錄不存在：%PROTO_DIR%"
ERR_PROTO_FILE_NOT_FOUND="❌ Proto 檔案不存在：%PROTO_FILE%"
ERR_NO_CLASSNAME="❌ %PROTO_FILE% 中找不到 java_outer_classname"
ERR_PROTOC_FAILED="❌ protoc 執行失敗（結束碼 %EXIT_CODE%）"
ERR_NO_TARGETS="⚠️  專案中找不到 %JAVA_FILE% 的對應 Java 檔案"

# generate.sh - info
MSG_AVAILABLE_PROTOS="📋 可用的 .proto 檔案："
MSG_GENERATING="🔧 從 %PROTO_FILE% 產生 Java → %JAVA_FILE%"
MSG_UPDATED="  ✅ 已更新：%TARGET%"
MSG_SKIPPED="  ⏭️  無變更：%TARGET%"
MSG_SUMMARY="📦 完成！已更新 %UPDATED% / %TOTAL% 個檔案，涵蓋 %SUBPROJECTS% 個子專案"
MSG_NO_CHANGES="✅ 全部 %TOTAL% 個檔案皆為最新"

# save-config.sh
MSG_CONFIG_SAVED="✅ 設定已儲存（protoc: %PROTOC_PATH%, 專案: %PROJECT_ROOT%, proto 目錄: %PROTO_DIR%, 語言: %LANG%）"
