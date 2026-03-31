---
name: setup
description: "Configure Telegram Bot Token, chat ID, timezone, language, output format, and Cowork inclusion for the export-chat-logs plugin."
allowed-tools:
  - Bash
  - Read
disable-model-invocation: true
---

# Configure Telegram

1. Read the current configuration by reading the env file at `~/.config/devtools-plugins/export-chat-logs/.env` (use `$HOME` if `~` doesn't work), then display the settings to the user. Mask the Bot Token (show only first 6 and last 4 characters). If the file doesn't exist, all settings are unset.

2. Ask the user which settings they want to change and **wait for the response** before continuing:

   > Which settings would you like to change? / 請選擇要修改的設定：
   >
   > 1. Bot Token
   > 2. Chat ID
   > 3. Timezone / 時區
   > 4. Language / 語言
   > 5. Output format / 輸出格式
   > 6. Include Cowork / 包含 Cowork
   >
   > Enter the numbers to change (e.g. `3 6`), or press Enter / type `all` to update all settings. / 輸入要修改的編號（例如 `3 6`），或按 Enter / 輸入 `all` 修改全部。

3. Based on the user's selection, ask **only** the questions for the selected settings, one at a time, waiting for a response after each. For unselected settings, use `skip`. If the user entered nothing or `all`, ask all 6 questions — each with a `skip` option to keep the current value.

   **Setting 1 — Bot Token** (ask only if 1 or `all` selected):
   > Please enter your **Telegram Bot Token** (type `skip` to keep current value)
   >
   > **Create a new Bot:**
   > 1. Search for `@BotFather` in Telegram and open a chat
   > 2. Send `/newbot`
   > 3. Follow the prompts to enter the bot name and username (must end with `bot`, e.g. `MyExportBot`)
   > 4. Once created, BotFather will reply with a Token in the format: `123456789:AAF...`
   >
   > **Get the Token for an existing Bot:**
   > 1. Find `@BotFather` in Telegram, send `/mybots`
   > 2. Select your bot → **API Token**

   **Setting 2 — Chat ID** (ask only if 2 or `all` selected):
   > Please enter your **Telegram Chat ID** (type `skip` to keep current value)
   >
   > **Get your personal chat_id:**
   > 1. Search for `@userinfobot` in Telegram and open a chat
   > 2. Send any message (e.g. `/start`)
   > 3. The bot will reply with your `id`, which is your chat_id (a number, e.g. `123456789`)
   >
   > **Get a group chat_id:**
   > 1. Add your bot to the group and grant it admin permissions
   > 2. Send any message in the group
   > 3. Open a browser and go to `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   > 4. Find the `"chat":{"id":...}` field; the group id is negative (e.g. `-100123456789`)

   **Setting 3 — Timezone** (ask only if 3 or `all` selected):
   > Please enter your **timezone offset** (integer, e.g. `8` for UTC+8 Taiwan, `9` for UTC+9 Japan; type `skip` to keep current value)

   **Setting 4 — Language** (ask only if 4 or `all` selected):
   > Select your **language** / 選擇**語言**：
   > - `1` — English
   > - `2` — 繁體中文
   >
   > (Type `skip` to keep current value / 輸入 `skip` 保留現有值)

   **Setting 5 — Output format** (ask only if 5 or `all` selected):
   > Select your **output format** / 選擇**輸出格式**：
   > - `1` — HTML (syntax highlighting + interactive charts / 語法高亮 + 互動式圖表)
   > - `2` — Markdown (plain text / 純文字)
   >
   > (Type `skip` to keep current value / 輸入 `skip` 保留現有值)

   **Setting 6 — Include Cowork** (ask only if 6 or `all` selected):
   > Include **Claude Cowork** sessions? / 是否包含 **Claude Cowork** 的對話？
   > - `1` — Yes / 包含（macOS only）
   > - `2` — No / 不包含
   >
   > (Type `skip` to keep current value / 輸入 `skip` 保留現有值)

4. Map numeric answers to their values before saving:
   - Setting 4: `1` → `en`, `2` → `zh-TW`
   - Setting 5: `1` → `html`, `2` → `md`
   - Setting 6: `1` → `true`, `2` → `false`

5. After collecting all selected values, run — pass `"skip"` for any setting the user did NOT select or explicitly skipped:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-token.sh" "<token or skip>" "<chat_id or skip>" "<timezone or skip>" "<lang or skip>" "<format or skip>" "<include_cowork or skip>"
```

Stop after configuration is complete — do not proceed with the export flow.
