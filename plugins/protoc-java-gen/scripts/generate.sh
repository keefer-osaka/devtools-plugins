#!/usr/bin/env bash
# generate.sh - Generate Java from a .proto file and copy to matching subprojects
# Usage: bash generate.sh [file.proto]
#   No argument: list available .proto files

DATA_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/devtools-plugins/protoc-java-gen"
ENV_FILE="$DATA_DIR/.env"

source "$(dirname "$0")/i18n/load.sh"

# --- Load config ---
if [ ! -f "$ENV_FILE" ]; then
  echo "$ERR_NOT_CONFIGURED"
  exit 1
fi

PROTOC_PATH=$(read_env_val PROTOC_PATH)
PROJECT_ROOT=$(read_env_val PROJECT_ROOT)
PROTO_DIR_REL=$(read_env_val PROTO_DIR)
PROTO_DIR_REL="${PROTO_DIR_REL:-proto}"
PROTO_DIR="$PROJECT_ROOT/$PROTO_DIR_REL"

# --- Validate ---
if [ ! -x "$PROTOC_PATH" ]; then
  echo "${ERR_PROTOC_NOT_FOUND//%PROTOC_PATH%/$PROTOC_PATH}"
  exit 1
fi

if [ ! -d "$PROTO_DIR" ]; then
  echo "${ERR_PROTO_DIR_NOT_FOUND//%PROTO_DIR%/$PROTO_DIR}"
  exit 1
fi

# --- No argument: list available protos ---
if [ -z "$1" ]; then
  echo "$MSG_AVAILABLE_PROTOS"
  find "$PROTO_DIR" -maxdepth 1 -name '*.proto' | sort | while read -r f; do
    echo "  $(basename "$f")"
  done
  exit 0
fi

PROTO_FILE="$1"
PROTO_PATH="$PROTO_DIR/$PROTO_FILE"

if [ ! -f "$PROTO_PATH" ]; then
  PROTO_PATH="$PROTO_FILE"
  if [ ! -f "$PROTO_PATH" ]; then
    echo "${ERR_PROTO_FILE_NOT_FOUND//%PROTO_FILE%/$PROTO_FILE}"
    exit 1
  fi
fi

# --- Extract java_outer_classname ---
JAVA_CLASS=$(grep -o 'java_outer_classname\s*=\s*"[^"]*"' "$PROTO_PATH" | grep -o '"[^"]*"' | tr -d '"')
if [ -z "$JAVA_CLASS" ]; then
  echo "${ERR_NO_CLASSNAME//%PROTO_FILE%/$(basename "$PROTO_PATH")}"
  exit 1
fi
JAVA_FILE="${JAVA_CLASS}.java"

_msg="${MSG_GENERATING//%PROTO_FILE%/$(basename "$PROTO_PATH")}"
_msg="${_msg//%JAVA_FILE%/$JAVA_FILE}"
echo "$_msg"

# --- Run protoc ---
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

(cd "$PROTO_DIR" && "$PROTOC_PATH" --java_out="$WORK_DIR" --proto_path=. "$(basename "$PROTO_PATH")")
PROTOC_EXIT=$?
if [ $PROTOC_EXIT -ne 0 ]; then
  echo "${ERR_PROTOC_FAILED//%EXIT_CODE%/$PROTOC_EXIT}"
  exit 1
fi

# Generated file is under proto/ package directory
GENERATED="$WORK_DIR/proto/$JAVA_FILE"
if [ ! -f "$GENERATED" ]; then
  # Try without package subdir (fallback)
  GENERATED=$(find "$WORK_DIR" -name "$JAVA_FILE" | head -1)
fi

if [ -z "$GENERATED" ] || [ ! -f "$GENERATED" ]; then
  echo "${ERR_PROTOC_FAILED//%EXIT_CODE%/generated file not found}"
  exit 1
fi

# --- Find targets in subprojects ---
TARGETS=()
while IFS= read -r line; do
  TARGETS+=("$line")
done < <(find "$PROJECT_ROOT" -path "*/src/main/java/proto/$JAVA_FILE" 2>/dev/null)

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "${ERR_NO_TARGETS//%JAVA_FILE%/$JAVA_FILE}"
  exit 1
fi

# --- Diff and overwrite ---
UPDATED=0
SUBPROJECTS=()
for TARGET in "${TARGETS[@]}"; do
  if diff -q "$GENERATED" "$TARGET" > /dev/null 2>&1; then
    echo "${MSG_SKIPPED//%TARGET%/$TARGET}"
  else
    cp "$GENERATED" "$TARGET"
    echo "${MSG_UPDATED//%TARGET%/$TARGET}"
    UPDATED=$((UPDATED + 1))
    SUBPROJECT=$(echo "$TARGET" | sed 's|/src/main/java/.*||')
    SUBPROJECTS+=("$SUBPROJECT")
  fi
done

TOTAL=${#TARGETS[@]}
UNIQUE_SUBPROJECTS=$(printf '%s\n' "${SUBPROJECTS[@]}" | sort -u | wc -l | tr -d ' ')

if [ "$UPDATED" -eq 0 ]; then
  echo "${MSG_NO_CHANGES//%TOTAL%/$TOTAL}"
else
  _msg="${MSG_SUMMARY//%UPDATED%/$UPDATED}"
  _msg="${_msg//%TOTAL%/$TOTAL}"
  _msg="${_msg//%SUBPROJECTS%/$UNIQUE_SUBPROJECTS}"
  echo "$_msg"
fi
