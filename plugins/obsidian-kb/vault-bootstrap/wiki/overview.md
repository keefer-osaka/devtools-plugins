# 知識庫全局摘要

> 此檔案由 `/kb-ingest` 維護，記錄知識庫整體狀態。

## 狀態

- **初始化日期**：（待填入）
- **總頁面數**：0
- **最後 ingest**：（尚未執行）

## 架構說明

此知識庫使用 Karpathy LLM Wiki 三層架構：
1. **L1**：`~/.claude/projects/**/*.jsonl`（全域 JSONL 對話原始紀錄）
2. **L1.5**：`transcripts/`（清理後對話歸檔，delta 游標追蹤）
3. **L2**：`wiki/`（結構化知識頁面）

## 安裝資訊

由 `obsidian-kb` plugin 初始化。使用 `/kb-ingest` 開始擷取知識。
