# obsidian-kb

Claude Code 的持久記憶知識庫，以 Obsidian 為儲存層。自動從對話歷史萃取知識，整理成結構化 wiki，並支援跨目錄語意搜尋。

## 功能概述

- **`/obsidian-kb:setup`** — 設定 vault 路徑、qmd binary、語言。首次安裝時自動部署維護 skills 進 vault。
- **`/obsidian-kb:search <問題>`** — 對知識庫進行語意搜尋（qmd BM25）。任何目錄均可使用。
- **`/obsidian-kb:upgrade`** — plugin 升級後，同步最新維護腳本進 vault。

安裝完成後，在 **vault 目錄啟動 Claude Code** 可使用：
- `/kb-ingest` — 從 Claude Code JSONL 歷史萃取知識
- `/kb-lint` — 知識庫健康檢查（斷裂連結、孤立頁面等）
- `/kb-stats` — 統計與覆蓋率報告

## 安裝

```
/plugin install obsidian-kb
/obsidian-kb:setup
```

## 需求

- Python 3.x（ingest 腳本使用）
- [qmd](https://github.com/toblu/qmd)（選用，語意搜尋）：`bun install -g @tobilu/qmd`

## 架構

```
~/.claude/projects/**/*.jsonl  (L1: 對話原始紀錄)
         ↓  /kb-ingest
transcripts/                   (L1.5: 清理後歸檔，delta 游標)
         ↓
wiki/                          (L2: 結構化知識頁面)
         ↓  @wiki/hot.md
CLAUDE.md                      (L3: session 啟動注入)
```

知識頁面分類：entities（實體）、concepts（概念）、decisions（決策）、troubleshooting（問題排查）、sources（來源摘要）。

## Plugin 升級後

執行 `/obsidian-kb:upgrade` 將最新維護腳本同步進 vault。

## 語言支援

支援 English、繁體中文（台灣）、日本語。
