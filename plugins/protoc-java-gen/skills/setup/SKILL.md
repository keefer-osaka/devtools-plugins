---
name: setup
description: "Configure protoc path, project root, proto directory, and language for the protoc-java-gen plugin."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Configure protoc-java-gen

## Step 1 — Read current configuration

Read `~/.config/devtools-plugins/protoc-java-gen/.env` (use `$HOME` if `~` doesn't work).
If the file does not exist, all values are unset and this is a first-time setup.

Extract:
- `CURRENT_PROTOC_PATH`
- `CURRENT_PROJECT_ROOT`
- `CURRENT_PROTO_DIR`
- `CURRENT_LANG`

## Step 2 — Branch: first-time vs. reconfigure

- **First-time** (`.env` does not exist): skip Step 3, go directly to Step 4 → 5 → 6 → 7
- **Existing config**: proceed to Step 3 (menu)

## Step 3 — Menu (existing config only)

Use AskUserQuestion with `multiSelect: true`. Show current value in each option's description; if unset, show `(not set / 未設定)`.

```json
{
  "questions": [{
    "question": "Which settings would you like to change? / 請選擇要修改的設定項目：",
    "header": "Settings / 設定",
    "multiSelect": true,
    "options": [
      {
        "label": "Protoc Path / Protoc 路徑",
        "description": "(current / 目前: <CURRENT_PROTOC_PATH>)"
      },
      {
        "label": "Project Root / 專案根目錄",
        "description": "(current / 目前: <CURRENT_PROJECT_ROOT>)"
      },
      {
        "label": "Proto Directory / Proto 目錄",
        "description": "(current / 目前: <CURRENT_PROTO_DIR>)"
      },
      {
        "label": "Language / 語言",
        "description": "(current / 目前: <CURRENT_LANG>)"
      }
    ]
  }]
}
```

For unselected settings, use `skip` when calling `save-config.sh`. **Do NOT call AskUserQuestion for unselected steps — skip those steps entirely and go straight to Step 8.**

## Step 4 — Protoc Path (only if "Protoc Path / Protoc 路徑" was selected in Step 3, or first-time setup)

Use AskUserQuestion. User selects a common path or enters a custom one via **Other**.

**When current path exists:**
```json
{
  "questions": [{
    "question": "Select the path to your protoc binary, or enter a custom path in 'Other'. / 選擇 protoc 執行檔路徑，或在「Other」輸入自訂路徑。",
    "header": "Protoc Path / Protoc 路徑",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep current / 保留現值",
        "description": "<CURRENT_PROTOC_PATH>"
      },
      {
        "label": "/usr/local/bin/protoc",
        "description": "Homebrew or system-wide install / Homebrew 或系統安裝"
      },
      {
        "label": "/usr/bin/protoc",
        "description": "System install / 系統安裝"
      }
    ]
  }]
}
```

**When no current path (first-time):**
```json
{
  "questions": [{
    "question": "Select the path to your protoc binary, or enter a custom path in 'Other'. / 選擇 protoc 執行檔路徑，或在「Other」輸入自訂路徑。",
    "header": "Protoc Path / Protoc 路徑",
    "multiSelect": false,
    "options": [
      {
        "label": "/usr/local/bin/protoc",
        "description": "Homebrew or system-wide install / Homebrew 或系統安裝"
      },
      {
        "label": "/usr/bin/protoc",
        "description": "System install / 系統安裝"
      }
    ]
  }]
}
```

**Handling answers:**
- "Keep current / 保留現值" → use `skip`
- Option selected → use that path as-is
- User types via "Other" → use that text as the path

## Step 5 — Project Root (only if "Project Root / 專案根目錄" was selected in Step 3, or first-time setup)

Use AskUserQuestion. User enters the absolute path to the project root via **Other**.

**When current root exists:**
```json
{
  "questions": [{
    "question": "Enter the absolute path to your project root in 'Other', or keep current. / 在「Other」輸入專案根目錄的絕對路徑，或保留現值。",
    "header": "Project Root / 專案根目錄",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep current / 保留現值",
        "description": "<CURRENT_PROJECT_ROOT>"
      }
    ]
  }]
}
```

**When no current root (first-time):**
```json
{
  "questions": [{
    "question": "Enter the absolute path to your project root in 'Other'. / 在「Other」輸入專案根目錄的絕對路徑。",
    "header": "Project Root / 專案根目錄",
    "multiSelect": false,
    "options": [
      {
        "label": "Enter path in Other field below / 在下方 Other 欄位輸入路徑",
        "description": "e.g. /Users/you/Projects/myapp"
      },
      {
        "label": "Skip for now / 稍後設定",
        "description": "Required for codegen — set this before running / 執行前必填"
      }
    ]
  }]
}
```

**Handling answers:**
- "Keep current / 保留現值" → use `skip`
- "Skip for now / 稍後設定" → use `skip`
- "Enter path in Other field below / ..." selected without Other text → ask again
- User types via "Other" → use that text as the project root

## Step 6 — Proto Directory (only if "Proto Directory / Proto 目錄" was selected in Step 3, or first-time setup)

Use AskUserQuestion. User selects the relative path to the proto directory inside the project root.

**When current dir exists:**
```json
{
  "questions": [{
    "question": "Select the proto directory (relative to project root), or enter a custom path in 'Other'. / 選擇 proto 目錄（相對於專案根目錄），或在「Other」輸入自訂路徑。",
    "header": "Proto Directory / Proto 目錄",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep current / 保留現值",
        "description": "<CURRENT_PROTO_DIR>"
      },
      {
        "label": "proto",
        "description": "Default / 預設: <project_root>/proto"
      },
      {
        "label": "src/main/proto",
        "description": "Maven/Gradle standard layout / 標準目錄結構"
      }
    ]
  }]
}
```

**When no current dir (first-time):**
```json
{
  "questions": [{
    "question": "Select the proto directory (relative to project root), or enter a custom path in 'Other'. / 選擇 proto 目錄（相對於專案根目錄），或在「Other」輸入自訂路徑。",
    "header": "Proto Directory / Proto 目錄",
    "multiSelect": false,
    "options": [
      {
        "label": "proto",
        "description": "Default / 預設: <project_root>/proto"
      },
      {
        "label": "src/main/proto",
        "description": "Maven/Gradle standard layout / 標準目錄結構"
      }
    ]
  }]
}
```

**Handling answers:**
- "Keep current / 保留現值" → use `skip`
- Option selected → use that value as-is
- User types via "Other" → use that text

## Step 7 — Language (only if "Language / 語言" was selected in Step 3, or first-time setup)

Use AskUserQuestion. Append `(current / 目前)` to the option matching `CURRENT_LANG`.

```json
{
  "questions": [{
    "question": "Select output language. / 選擇輸出語言。",
    "header": "Language / 語言",
    "multiSelect": false,
    "options": [
      {
        "label": "English",
        "description": "All output in English / 所有輸出使用英文"
      },
      {
        "label": "繁體中文",
        "description": "所有輸出使用繁體中文 / All output in Traditional Chinese"
      }
    ]
  }]
}
```

**Handling answers:**
- "Keep current / 保留現值" → use `skip`
- "English" → `en`
- "繁體中文" → `zh-TW`

## Step 8 — Map answers and save

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-config.sh" "<protoc_path or skip>" "<project_root or skip>" "<proto_dir or skip>" "<lang or skip>"
```

Stop after configuration is complete — do not proceed with the run flow.
