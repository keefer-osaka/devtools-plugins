#!/usr/bin/env python3
"""
remap_wiki_transcript_link.py — 重寫 wiki 頁面中指向舊 transcript stem 的 wikilink。

使用流程：
  1. python3 migrate_transcript_filenames.py --json > /tmp/plan.json
  2. python3 migrate_transcript_filenames.py --apply
  3. python3 remap_wiki_transcript_link.py --plan /tmp/plan.json           # dry-run
  4. python3 remap_wiki_transcript_link.py --plan /tmp/plan.json --apply   # 實際重寫

CLI:
  python3 remap_wiki_transcript_link.py --plan PATH          # dry-run（預設）
  python3 remap_wiki_transcript_link.py --plan PATH --apply  # 實際重寫（備份原檔）
  python3 remap_wiki_transcript_link.py --plan PATH --json   # JSON 輸出
  python3 remap_wiki_transcript_link.py --plan PATH --vault PATH
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from transcript_utils import VAULT_DIR

WIKI_DIR_NAME = "wiki"
_LINK_RE = re.compile(r'\[\[([^\]\|#]+)((?:[\|#][^\]]*)?)\]\]')


# ── Stem map ──────────────────────────────────────────────────────────────────

def build_stem_map_from_plan(plan_data: dict) -> dict[str, str]:
    """從 migrate 計畫 JSON 建立 {old_stem: new_stem} map。"""
    stem_map: dict[str, str] = {}
    for item in plan_data.get("plan", []):
        if item.get("status") != "rename":
            continue
        old_stem = item.get("old_stem", "")
        new_stem = item.get("new_stem", "")
        if old_stem and new_stem and old_stem != new_stem:
            stem_map[old_stem] = new_stem
    return stem_map


# ── Link rewriting ────────────────────────────────────────────────────────────

def rewrite_links(text: str, stem_map: dict[str, str]) -> tuple[str, int]:
    """Replace wikilinks whose target stem matches stem_map. Returns (new_text, count)."""
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        target = m.group(1).strip()
        if target in stem_map:
            n += 1
            return f"[[{stem_map[target]}{m.group(2)}]]"
        return m.group(0)

    return _LINK_RE.sub(sub, text), n


# ── Vault processing ──────────────────────────────────────────────────────────

def process_vault(
    vault: Path,
    stem_map: dict[str, str],
    *,
    apply: bool,
    backup_ts: str,
) -> list[dict]:
    """Scan wiki/**/*.md, rewrite links. Returns list of per-file result dicts."""
    wiki_dir = vault / WIKI_DIR_NAME
    results = []
    for md_path in sorted(wiki_dir.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        new_text, count = rewrite_links(text, stem_map)
        if count == 0:
            continue
        rel = str(md_path.relative_to(vault))
        if apply:
            bak = md_path.with_name(f"{md_path.name}.bak.{backup_ts}")
            bak.write_text(text, encoding="utf-8")
            md_path.write_text(new_text, encoding="utf-8")
        results.append({"file": rel, "rewrites": count, "applied": apply})
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="remap_wiki_transcript_link — 重寫 wiki 中舊 transcript wikilink。"
    )
    p.add_argument("--plan", required=True, help="migrate --json 輸出的計畫檔路徑")
    p.add_argument("--apply", action="store_true", help="實際重寫（預設 dry-run）")
    p.add_argument("--json", dest="as_json", action="store_true", help="JSON 輸出")
    p.add_argument("--vault", default=None, help="vault root path（預設 VAULT_DIR）")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    vault = Path(args.vault).resolve() if args.vault else Path(VAULT_DIR)

    try:
        plan_data = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERROR] 無法讀取計畫檔 {args.plan}: {e}", file=sys.stderr)
        return 1

    stem_map = build_stem_map_from_plan(plan_data)
    if not stem_map:
        print("[WARN] 計畫中無任何 rename 項目，stem_map 為空", file=sys.stderr)

    backup_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_results = process_vault(vault, stem_map, apply=args.apply, backup_ts=backup_ts)

    total_rewrites = sum(r["rewrites"] for r in file_results)
    total_files = len(file_results)

    if args.as_json:
        print(json.dumps({
            "stem_map_size": len(stem_map),
            "files_touched": total_files,
            "total_rewrites": total_rewrites,
            "results": file_results,
        }, ensure_ascii=False, indent=2))
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"remap_wiki_transcript_link [{mode}]")
        print(f"  stem_map entries: {len(stem_map)}")
        print(f"  files touched:    {total_files}")
        print(f"  total rewrites:   {total_rewrites}")
        if file_results:
            print()
            for r in file_results:
                print(f"  {r['file']} ({r['rewrites']} rewrites)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
