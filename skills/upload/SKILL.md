---
name: upload
description: "Package Claude Code and Cursor chat logs as Markdown zip and upload to Telegram. Use when user says 'export chat logs', 'upload logs', or provides a number of days."
allowed-tools:
  - Bash
  - Read
disable-model-invocation: true
argument-hint: "[days=7]"
---

# Export Chat Logs

Parse the number of days (default 7) and run the export script:

```bash
DAYS=${ARGUMENTS:-7}
DAYS=$(echo "$DAYS" | grep -o '[0-9]*' | head -1)
DAYS=${DAYS:-7}
bash "${CLAUDE_PLUGIN_ROOT}/scripts/export.sh" "$DAYS"
```
