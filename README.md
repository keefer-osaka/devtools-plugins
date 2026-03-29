# export-chat-logs

Claude Code plugin — collects Claude Code and Cursor chat logs, converts them to Markdown, packages as a zip, and sends via Telegram.

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

Follow the prompts to enter:
- **Bot Token**: In Telegram, find `@BotFather` → `/mybots` → select your bot → API Token
- **Chat ID**: In Telegram, find `@userinfobot`, send any message, and it will reply with your chat_id
- **Timezone offset**: Integer, e.g. `8` (UTC+8, Taiwan), `-5` (UTC-5, EST); default is `8`

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
- Cursor: agent transcript JSONL from `~/.cursor/projects/`
- Each session is converted to a Markdown file
- Includes a statistics report (token usage, model info)
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
└── plugin.json          # Plugin metadata
skills/
├── upload/SKILL.md      # /export-chat-logs:upload
└── setup/SKILL.md       # /export-chat-logs:setup
scripts/
├── export.sh            # Main export flow
├── setup.sh             # Show current configuration status
├── save-token.sh        # Write token + chat_id
├── convert_to_markdown.py  # JSONL → Markdown
└── generate_stats.py    # Statistics report
```
