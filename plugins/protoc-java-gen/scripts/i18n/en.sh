# English locale strings for protoc-java-gen

# generate.sh - errors
ERR_NOT_CONFIGURED="❌ Not configured. Please run: /protoc-java-gen:setup"
ERR_PROTOC_NOT_FOUND="❌ protoc not found or not executable: %PROTOC_PATH%"
ERR_PROTO_DIR_NOT_FOUND="❌ Proto directory not found: %PROTO_DIR%"
ERR_PROTO_FILE_NOT_FOUND="❌ Proto file not found: %PROTO_FILE%"
ERR_NO_CLASSNAME="❌ No java_outer_classname found in %PROTO_FILE%"
ERR_PROTOC_FAILED="❌ protoc failed (exit code %EXIT_CODE%)"
ERR_NO_TARGETS="⚠️  No matching Java files found in project for %JAVA_FILE%"

# generate.sh - info
MSG_AVAILABLE_PROTOS="📋 Available .proto files:"
MSG_GENERATING="🔧 Generating Java from %PROTO_FILE% → %JAVA_FILE%"
MSG_UPDATED="  ✅ Updated: %TARGET%"
MSG_SKIPPED="  ⏭️  Unchanged: %TARGET%"
MSG_SUMMARY="📦 Done! Updated %UPDATED% / %TOTAL% files in %SUBPROJECTS% subproject(s)"
MSG_NO_CHANGES="✅ All %TOTAL% file(s) already up to date"

# save-config.sh
MSG_CONFIG_SAVED="✅ Configuration saved (protoc: %PROTOC_PATH%, project: %PROJECT_ROOT%, proto_dir: %PROTO_DIR%, lang: %LANG%)"
