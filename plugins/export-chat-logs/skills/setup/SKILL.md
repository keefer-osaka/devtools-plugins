---
name: setup
description: "Configure Telegram Bot Token, chat ID, timezone, language, output format, and Cowork inclusion for the export-chat-logs plugin."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Configure Telegram

## Step 1 — Read current configuration

Read `~/.config/devtools-plugins/export-chat-logs/.env` (use `$HOME` if `~` doesn't work) to extract the raw values. If the file does not exist, all values are unset and this is a first-time setup.

Do NOT run `setup.sh` — current values will be shown directly in the AskUserQuestion options.

Extract these values from the .env:
- `CURRENT_TOKEN` (mask it: show first 6 and last 4 characters, e.g. `123456...F4x2`)
- `CURRENT_CHAT_ID`
- `CURRENT_TZ` (format as `UTC+N`)
- `CURRENT_LANG`
- `CURRENT_FORMAT`
- `CURRENT_COWORK`

## Step 2 — Branch: first-time vs. reconfigure

- **First-time** (`.env` does not exist): skip Step 3, go directly to Step 4 → 5 → 6 (all settings selected)
- **Existing config**: proceed to Step 3 (menu)

## Step 3 — Menu (existing config only)

Use AskUserQuestion with `multiSelect: true`. In each option's description, show the current value; if unset, show `(not set / 未設定)`.

```json
{
  "questions": [{
    "question": "Which settings would you like to change? / 請選擇要修改的設定：",
    "header": "Settings",
    "multiSelect": true,
    "options": [
      {
        "label": "Bot Token",
        "description": "(current: <MASKED_TOKEN> / 目前：<MASKED_TOKEN>)"
      },
      {
        "label": "Chat ID",
        "description": "(current: <CURRENT_CHAT_ID> / 目前：<CURRENT_CHAT_ID>)"
      },
      {
        "label": "Preferences / 偏好設定",
        "description": "(current: <CURRENT_TZ>, <CURRENT_LANG>, <CURRENT_FORMAT>, Cowork: <CURRENT_COWORK> / 目前：<CURRENT_TZ>, <CURRENT_LANG>, <CURRENT_FORMAT>, Cowork: <CURRENT_COWORK>)"
      }
    ]
  }]
}
```

For unselected settings, use `skip` when calling `save-config.sh`.

## Step 4 — Bot Token (if selected or first-time)

Use AskUserQuestion. Tell the user to paste their token in the **Other** field.

**When current token exists:**
```json
{
  "questions": [{
    "question": "Enter your Telegram Bot Token in the 'Other' field, or keep the current value. / 在「Other」欄位貼上你的 Telegram Bot Token，或保留現有值。",
    "header": "Bot Token",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep current / 保留現值",
        "description": "<MASKED_TOKEN>"
      },
      {
        "label": "How to get a token / 如何取得 Token",
        "description": "Telegram → @BotFather → /newbot (new) or /mybots → API Token (existing)"
      }
    ]
  }]
}
```

**When no current token (first-time):**
```json
{
  "questions": [{
    "question": "Enter your Telegram Bot Token in the 'Other' field. / 在「Other」欄位貼上你的 Telegram Bot Token。",
    "header": "Bot Token",
    "multiSelect": false,
    "options": [
      {
        "label": "How to get a token / 如何取得 Token",
        "description": "Telegram → @BotFather → /newbot (new) or /mybots → API Token (existing)"
      },
      {
        "label": "Skip for now / 稍後設定",
        "description": "Required for export — you must set this before exporting / 匯出時必填，請在匯出前完成設定"
      }
    ]
  }]
}
```

**Handling answers:**
- User types via "Other" → use that text as the token
- "Keep current / 保留現值" → use `skip`
- "Skip for now / 稍後設定" → use `skip`
- "How to get a token / 如何取得 Token" → print the following instructions, then ask Step 4 again:

  > **Create a new Bot:**
  > 1. Search for `@BotFather` in Telegram and open a chat
  > 2. Send `/newbot`
  > 3. Follow the prompts to enter the bot name and username (must end with `bot`, e.g. `MyExportBot`)
  > 4. Once created, BotFather will reply with a Token in the format: `123456789:AAF...`
  >
  > **Get the Token for an existing Bot:**
  > 1. Find `@BotFather` in Telegram, send `/mybots`
  > 2. Select your bot → **API Token**
  >
  > Then paste the token in the **Other** field. / 取得後，在「Other」欄位貼上 Token。

## Step 5 — Chat ID (if selected or first-time)

Use AskUserQuestion. Tell the user to paste their Chat ID in the **Other** field.

**When current Chat ID exists:**
```json
{
  "questions": [{
    "question": "Enter your Telegram Chat ID in the 'Other' field, or keep the current value. / 在「Other」欄位貼上你的 Telegram Chat ID，或保留現有值。",
    "header": "Chat ID",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep current / 保留現值",
        "description": "<CURRENT_CHAT_ID>"
      },
      {
        "label": "How to get Chat ID / 如何取得 Chat ID",
        "description": "Personal: @userinfobot → send any message → copy 'id' / Group: add bot as admin, send a message, check getUpdates API"
      }
    ]
  }]
}
```

**When no current Chat ID (first-time):**
```json
{
  "questions": [{
    "question": "Enter your Telegram Chat ID in the 'Other' field. / 在「Other」欄位貼上你的 Telegram Chat ID。",
    "header": "Chat ID",
    "multiSelect": false,
    "options": [
      {
        "label": "How to get Chat ID / 如何取得 Chat ID",
        "description": "Personal: @userinfobot → send any message → copy 'id' / Group: add bot as admin, send a message, check getUpdates API"
      },
      {
        "label": "Skip for now / 稍後設定",
        "description": "Required for export — you must set this before exporting / 匯出時必填，請在匯出前完成設定"
      }
    ]
  }]
}
```

**Handling answers:**
- User types via "Other" → use that text as the Chat ID
- "Keep current / 保留現值" → use `skip`
- "Skip for now / 稍後設定" → use `skip`
- "How to get Chat ID / 如何取得 Chat ID" → print the following instructions, then ask Step 5 again:

  > **Get your personal chat_id:**
  > 1. Search for `@userinfobot` in Telegram and open a chat
  > 2. Send any message (e.g. `/start`)
  > 3. The bot will reply with your `id` — that is your chat_id (a number, e.g. `123456789`)
  >
  > **Get a group chat_id:**
  > 1. Add your bot to the group and grant it admin permissions
  > 2. Send any message in the group
  > 3. Open a browser and go to `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
  > 4. Find the `"chat":{"id":...}` field; the group id is negative (e.g. `-100123456789`)
  >
  > Then paste the Chat ID in the **Other** field. / 取得後，在「Other」欄位貼上 Chat ID。

## Step 6 — Preferences (if "Preferences" selected or first-time)

Use a single AskUserQuestion call with up to 4 questions (Timezone + Language + Format + Cowork). For each question, append `(current / 目前)` to the description of the option that matches the current value.

```json
{
  "questions": [
    {
      "question": "Select your timezone / 選擇時區 (type a custom offset in 'Other', e.g. -5, 5, 0 / 在「Other」輸入自訂偏移量)",
      "header": "Timezone",
      "multiSelect": false,
      "options": [
        {
          "label": "UTC+8",
          "description": "Taiwan, Singapore, HK, China / 台灣、新加坡、香港、中國"
        },
        {
          "label": "UTC+9",
          "description": "Japan, Korea / 日本、韓國"
        },
        {
          "label": "UTC+0",
          "description": "UK, UTC / 英國"
        }
      ]
    },
    {
      "question": "Select language / 選擇語言",
      "header": "Language",
      "multiSelect": false,
      "options": [
        {
          "label": "English",
          "description": "All output in English"
        },
        {
          "label": "繁體中文",
          "description": "所有輸出使用繁體中文"
        }
      ]
    },
    {
      "question": "Select output format / 選擇輸出格式",
      "header": "Output Format",
      "multiSelect": false,
      "options": [
        {
          "label": "HTML",
          "description": "Syntax highlighting + interactive charts / 語法高亮 + 互動式圖表"
        },
        {
          "label": "Markdown",
          "description": "Plain text, simpler / 純文字，較簡潔"
        }
      ]
    },
    {
      "question": "Include Claude Cowork sessions? / 是否包含 Claude Cowork 的對話？",
      "header": "Cowork",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes / 是",
          "description": "Include Cowork sessions (macOS only) / 包含 Cowork 對話（僅 macOS）"
        },
        {
          "label": "No / 否",
          "description": "Claude Code only / 僅 Claude Code"
        }
      ]
    }
  ]
}
```

## Step 7 — Map answers and save

Map the collected answers to config values:

| Answer | Value |
|--------|-------|
| "Keep current / 保留現值" | `skip` |
| "Skip for now / 稍後設定" | `skip` |
| Token / Chat ID typed via Other | use as-is |
| "UTC+8" | `8` |
| "UTC+9" | `9` |
| "UTC+0" | `0` |
| Timezone typed via Other (e.g. `-5`, `5`) | use as-is |
| "English" | `en` |
| "繁體中文" | `zh-TW` |
| "HTML" | `html` |
| "Markdown" | `md` |
| "Yes / 是" | `true` |
| "No / 否" | `false` |
| Setting not selected in menu | `skip` |

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-config.sh" "<token or skip>" "<chat_id or skip>" "<timezone or skip>" "<lang or skip>" "<format or skip>" "<include_cowork or skip>"
```

Stop after configuration is complete — do not proceed with the export flow.
