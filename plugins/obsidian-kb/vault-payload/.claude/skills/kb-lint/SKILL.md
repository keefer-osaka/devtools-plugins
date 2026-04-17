---
name: kb-lint
description: 知識庫健康檢查。掃描 wiki/ 並輸出 lint-report.md，檢查 canonical drift、斷裂連結、孤立頁面、無來源、矛盾未解、索引缺漏、過時頁面、跨作者矛盾。
usage: /kb-lint
---

# kb-lint

執行知識庫健康檢查，輸出報告到 `wiki/meta/lint-report.md`。

## 執行方式

```bash
python3 __VAULT_DIR__/.claude/skills/kb-lint/scripts/lint_wiki.py
```

## 檢查項目

| # | 名稱 | 說明 |
|---|------|------|
| 1 | **Canonical Drift** | 有 `canonical_files` 的頁面，其中提到的具體值是否仍出現在對應檔案中 |
| 2 | 斷裂連結 | `[[wikilink]]` 指向不存在的頁面 |
| 3 | 孤立頁面 | 無任何 wikilink 指向的頁面 |
| 4 | 無來源 | `sources` 欄位為空 |
| 5 | 矛盾未解 | `status: contradicted` 超過 30 天 |
| 6 | 索引缺漏 | 存在於 `wiki/` 但未列入任何 `_index.md` |
| 7 | 過時頁面 | `status: stale` 或超過 90 天未更新 |
| 8 | 跨作者矛盾 | `status: contradicted` 且有 ≥2 位不同作者（硬）；或近 7 天多作者更新但仍為 `draft`（軟） |

## Canonical Drift 說明

適用於 frontmatter 中有 `canonical_files` 欄位的 wiki 頁面：

```yaml
canonical_files:
  - "~/.claude/settings.json"
  - "~/.claude/statusline-command.sh"
```

腳本會：
1. 讀取 `canonical_files` 中的每個檔案
2. 從 wiki 頁面 body 提取 quoted values、版本號、路徑
3. 檢查這些值是否仍出現在對應檔案中
4. 不符合的標記為潛在 drift，列入報告

> **注意**：自動比對採用啟發式規則，可能有誤報。報告中的 drift 需人工確認。

如需壓制已知誤報，在 frontmatter 加入：

```yaml
lint_ignore:
  - canonical_drift
```

## 輸出

- `wiki/meta/lint-report.md` — 完整報告
- stdout — 同上（供即時查看）
- exit code 0 = 無問題，1 = 有問題
