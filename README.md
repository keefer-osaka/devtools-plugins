# export-chat-logs

Claude Code plugin — collects Claude Code and Cowork chat logs, converts them to HTML or Markdown, packages as a zip, and sends via Telegram.

> **Note:** This plugin works with **Claude Code (CLI)** conversations. **Claude Cowork** sessions can also be included (opt-in, macOS only). Claude Desktop Chat and claude.ai web conversations are stored server-side and cannot be accessed locally.

[繁體中文](README.zh-TW.md)

## Installation

### Method 1: `claude --plugin-dir` (local development / quick test)

```bash
git clone https://github.com/keefer-osaka/devtools-plugins.git /path/to/devtools-plugins
claude --plugin-dir /path/to/devtools-plugins
```

### Method 2: Via plugin marketplace

```
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install export-chat-logs@devtools-plugins
```

After installation, **restart Claude Code** to see the `/export-chat-logs:setup` and `/export-chat-logs:upload` commands. `/reload-plugins` will not load newly installed skills.

### Uninstall

```
/plugin uninstall export-chat-logs@devtools-plugins
/reload-plugins
```

Remove marketplace source:

```
/plugin marketplace remove devtools-plugins
```

---

## Initial Setup

After installation, run the following command to configure your Telegram Bot Token, chat_id, and timezone:

```
/export-chat-logs:setup
```

A numbered menu is shown — select which settings to change (e.g. `3 6`), then answer only those prompts:

- **Bot Token**: In Telegram, find `@BotFather` → `/mybots` → select your bot → API Token
- **Chat ID**: In Telegram, find `@userinfobot`, send any message, and it will reply with your chat_id
- **Timezone offset**: Integer, e.g. `8` (UTC+8, Taiwan), `9` (UTC+9, Japan); default is `8`
- **Language**: `1` English / `2` Traditional Chinese; default is `en`
- **Output format**: `1` HTML (syntax highlighting + interactive charts) / `2` Markdown; default is `html`
- **Include Cowork**: `1` Yes / `2` No; include Claude Cowork sessions (macOS only); default is No

Settings are saved to `~/.config/devtools-plugins/export-chat-logs/.env` (permissions 600, not in repo).

---

## Usage

### Export (default 7 days)

```
/export-chat-logs:upload
```

### Specify number of days

```
/export-chat-logs:upload 14
```

### Non-interactive mode (`claude -p`)

```bash
claude -p "upload chat logs" --allowedTools "Bash,Read"
claude -p "upload chat logs 14" --allowedTools "Bash,Read"
```

---

## Requirements

- macOS (Linux requires minor adjustments to the `date` command)
- Python 3
- `curl`, `zip`
- Claude Code CLI

---

## Exported Content

- Claude Code: JSONL session logs from `~/.claude/projects/`
- Claude Cowork (opt-in): session logs from `~/Library/Application Support/Claude/` (macOS only)
- Each session is converted to an HTML file (or Markdown if configured)
- HTML includes syntax highlighting (highlight.js) and interactive charts (Mermaid.js)
- Includes a statistics report (session count, model usage, tool usage, category breakdown)
- Packaged as a zip and sent to Telegram

---

## Troubleshooting

### Plugin not updating after `git pull`

The marketplace caches a specific version locally. If changes are not reflected after pulling, clear the cache and reinstall:

```bash
rm -rf ~/.claude/plugins/cache/devtools-plugins
```

Then reinstall in Claude Code:

```
/plugin marketplace remove devtools-plugins
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install export-chat-logs@devtools-plugins
```

Restart Claude Code after reinstalling.

---

## File Structure

```
.claude-plugin/
└── plugin.json             # Plugin metadata
skills/
├── upload/SKILL.md         # /export-chat-logs:upload
└── setup/SKILL.md          # /export-chat-logs:setup
scripts/
├── common.py               # Shared logic (JSONL parsing, i18n/tz loading)
├── export.sh               # Main export flow
├── setup.sh                # Show current configuration status
├── save-token.sh           # Write token + chat_id + timezone + language + format
├── convert_to_html.py      # JSONL → HTML (syntax highlighting + charts)
├── convert_to_markdown.py  # JSONL → Markdown
├── generate_stats.py       # Statistics report (HTML or Markdown)
└── i18n/                   # Locale strings
    ├── en.sh / en.py           # English
    └── zh_TW.sh / zh_TW.py    # Traditional Chinese
```
