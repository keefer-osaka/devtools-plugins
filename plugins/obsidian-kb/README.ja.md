# obsidian-kb

Obsidian をストレージとして使用する Claude Code の永続記憶ナレッジベース。会話履歴から知識を自動抽出し、構造化された wiki に整理し、任意のディレクトリからセマンティック検索を可能にします。

## 機能

- **`/obsidian-kb:setup`** — vault パス、qmd バイナリ、言語を設定。初回インストール時はメンテナンススキルを vault にデプロイ。
- **`/obsidian-kb:search <質問>`** — ナレッジベースをセマンティック検索（qmd BM25）。任意のディレクトリから使用可能。
- **`/obsidian-kb:upgrade`** — プラグインアップグレード後、最新のメンテナンススクリプトを vault に同期。

セットアップ完了後、**vault ディレクトリで Claude Code を起動**すると利用可能：
- `/kb-ingest` — Claude Code の JSONL 履歴から知識を抽出
- `/kb-lint` — ナレッジベースのヘルスチェック（リンク切れ、孤立ページなど）
- `/kb-stats` — 統計とカバレッジレポート

## インストール

```
/plugin install obsidian-kb
/obsidian-kb:setup
```

## 必要要件

- Python 3.x（インジェストスクリプト用）
- [qmd](https://github.com/toblu/qmd)（任意、セマンティック検索用）：`bun install -g @tobilu/qmd`

## アーキテクチャ

```
~/.claude/projects/**/*.jsonl  (L1: 会話生データ)
         ↓  /kb-ingest
transcripts/                   (L1.5: クリーン済みアーカイブ)
         ↓
wiki/                          (L2: 構造化ナレッジページ)
         ↓  @wiki/hot.md
CLAUDE.md                      (L3: セッション起動時注入)
```

ページカテゴリ：entities（エンティティ）、concepts（概念）、decisions（決定）、troubleshooting（トラブルシューティング）、sources（ソースまとめ）。

## プラグインアップグレード後

`/obsidian-kb:upgrade` を実行して最新のメンテナンススクリプトを vault に同期してください。

## 言語サポート

English、繁體中文（台湾）、日本語をサポート。
