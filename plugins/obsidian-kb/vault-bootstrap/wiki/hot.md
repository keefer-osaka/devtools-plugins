# Hot Cache

> 此檔案由 `/kb-ingest` 自動維護，保持 ~500 字。
> 記錄最近重要的上下文，session 啟動時必讀。

_最後更新：（尚未初始化）_

---

## 知識庫架構

此 vault 是依照 Karpathy「LLM Wiki」三層模式建立的 Claude 持久記憶：

```
~/.claude/projects/**/*.jsonl (L1: 全域 JSONL)
        ↓ /kb-ingest skill
transcripts/ (L1.5: 清理後對話歸檔，delta 游標)
        ↓
wiki/ (L2: 知識 Wiki)
        ↓ @wiki/hot.md
CLAUDE.md (L3: 啟動注入)
```

## 近期 Sessions

（尚未執行 `/kb-ingest`，這裡會顯示最近處理的 sessions）
