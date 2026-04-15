# obsidian-kb

Persistent knowledge base for Claude Code, built on Obsidian. Extracts knowledge from your Claude Code conversation history, stores it in a structured wiki, and makes it searchable from any working directory.

## Overview

- **`/obsidian-kb:setup`** — Configure vault path, qmd binary, and language. Deploys maintenance skills into the vault on first install.
- **`/obsidian-kb:search <question>`** — Semantic search across your knowledge base (BM25 via qmd). Works from any directory.
- **`/obsidian-kb:upgrade`** — Sync the latest maintenance scripts into your vault after upgrading the plugin.

After setup, these skills become available **inside your vault directory**:
- `/kb-ingest` — Extract knowledge from Claude Code JSONL history
- `/kb-lint` — Check knowledge base health (broken links, orphaned pages, etc.)
- `/kb-stats` — Statistics and coverage report

## Installation

```
/plugin install obsidian-kb
/obsidian-kb:setup
```

## Requirements

- Python 3.x (for ingest scripts)
- [qmd](https://github.com/toblu/qmd) (optional, for semantic search): `bun install -g @tobilu/qmd`

## Architecture

```
~/.claude/projects/**/*.jsonl  (L1: raw conversation history)
         ↓  /kb-ingest
transcripts/                   (L1.5: cleaned conversation archive)
         ↓
wiki/                          (L2: structured knowledge wiki)
         ↓  @wiki/hot.md
CLAUDE.md                      (L3: session injection)
```

Knowledge pages are organized into: entities, concepts, decisions, troubleshooting, sources.

## After Plugin Upgrade

Run `/obsidian-kb:upgrade` to sync the latest maintenance scripts into your vault.

## Languages

Supports English, 繁體中文 (Traditional Chinese), and 日本語.
