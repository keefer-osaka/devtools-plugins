#!/usr/bin/env python3
"""
migrate_transcript_filenames.py — 修正損壞的 transcript 檔名。

CLI:
  python3 migrate_transcript_filenames.py            # dry-run
  python3 migrate_transcript_filenames.py --apply    # 實際 rename（含 backup）
  python3 migrate_transcript_filenames.py --json     # JSON 輸出
  python3 migrate_transcript_filenames.py --vault PATH
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
from transcript_utils import (
    make_transcript_filename, read_sessions_json, write_sessions_json,
    rebuild_transcripts_index_from_manifest, VAULT_DIR,
)

# ── Regex constants ───────────────────────────────────────────────────────────

_DATE_ONLY_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_FM_LINE_RE = re.compile(r'^(\w+):[ \t]*(.*)$')


# ── Frontmatter helpers ───────────────────────────────────────────────────────

def _read_transcript_fm(path: Path) -> dict:
    """Inline frontmatter parser；回傳 key→value dict（字串值，未作型別轉換）。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        lm = _FM_LINE_RE.match(line)
        if lm:
            fm[lm.group(1)] = lm.group(2).strip()
    return fm


def _resolve_first_ts(fm: dict) -> str:
    """優先 fm['first_ts'] 非空；否則若 fm['date'] 符合 _DATE_ONLY_RE 則回傳；否則回傳 ''。"""
    first_ts = fm.get("first_ts", "").strip()
    if first_ts:
        return first_ts
    date_val = fm.get("date", "").strip()
    if _DATE_ONLY_RE.match(date_val):
        return date_val
    return ""


# ── Core logic ────────────────────────────────────────────────────────────────

def plan_renames(manifest: dict, vault: Path) -> list[dict]:
    """計算每個 manifest entry 的 rename 計畫，回傳 list[dict]。

    每個 dict 含 'sid' 與 'status'，依情況附帶其他欄位。
    Status 值：
      rename          — 需要改名
      idempotent_skip — 檔名已正確
      collision       — 新檔名已存在（需人工處理）
      missing_file    — transcript_path 指向的檔案不存在
      empty_path      — transcript_path 缺失或空
    """
    plan: list[dict] = []

    for sid, entry in manifest.items():
        tp = entry.get("transcript_path", "")

        # empty_path
        if not tp:
            plan.append({"sid": sid, "status": "empty_path"})
            continue

        abs_path = vault / tp

        # missing_file
        if not abs_path.exists():
            plan.append({"sid": sid, "status": "missing_file", "old_path": tp})
            continue

        fm = _read_transcript_fm(abs_path)
        first_ts = _resolve_first_ts(fm)
        fm_sid = fm.get("session_id", sid).strip() or sid
        title = fm.get("title", "").strip()

        new_fname = make_transcript_filename(first_ts, fm_sid, title)

        # idempotent_skip
        if new_fname == abs_path.name:
            plan.append({"sid": sid, "status": "idempotent_skip", "old_path": tp})
            continue

        new_path = abs_path.parent / new_fname

        # collision
        if new_path.exists():
            plan.append({
                "sid": sid,
                "status": "collision",
                "old_path": tp,
                "new_fname": new_fname,
                "collision_path": str(new_path),
            })
            continue

        # rename
        plan.append({
            "sid": sid,
            "status": "rename",
            "old_path": tp,
            "new_fname": new_fname,
            "old_stem": abs_path.stem,
            "new_stem": Path(new_fname).stem,
        })

    return plan


def apply_renames(plan, manifest, vault, *, backup_ts) -> dict:
    """執行 rename，更新 manifest，重建 index。失敗時 rollback。"""
    src_json = vault / '_schema' / 'sessions.json'
    bak = src_json.with_name(f'sessions.json.bak.{backup_ts}')
    bak.write_bytes(src_json.read_bytes())
    renamed = []

    def _rollback():
        for sid, new_fname in renamed:
            try:
                old_rel = next(it['old_path'] for it in plan if it['sid'] == sid)
                old_path = vault / old_rel
                new_path = old_path.parent / new_fname
                os.rename(new_path, old_path)
            except OSError:
                pass

    try:
        for item in plan:
            if item['status'] != 'rename':
                continue
            src = vault / item['old_path']
            dst = src.parent / item['new_fname']
            os.rename(src, dst)
            renamed.append((item['sid'], item['new_fname']))
        for sid, new_fname in renamed:
            manifest[sid]['transcript_path'] = f'transcripts/{new_fname}'
        write_sessions_json(manifest)
        rebuild_transcripts_index_from_manifest(manifest, str(vault / 'transcripts'))
    except Exception as e:
        _rollback()
        raise SystemExit(f'[FATAL] apply failed: {e}; rolled back {len(renamed)} renames')

    return {'renamed': len(renamed), 'backup': str(bak.name)}


# ── CLI helpers ───────────────────────────────────────────────────────────────

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="migrate_transcript_filenames — 修正損壞的 transcript 檔名。"
    )
    p.add_argument("--apply", dest="apply", action="store_true", help="實際 rename（含 backup）")
    p.add_argument("--json", dest="as_json", action="store_true", help="JSON 輸出")
    p.add_argument("--vault", default=None, help="vault root path（預設 VAULT_DIR）")
    return p.parse_args(argv)


def _iso_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def render_human(plan: list[dict], *, apply: bool, apply_result: dict | None = None) -> None:
    counts: dict[str, int] = {}
    for item in plan:
        counts[item["status"]] = counts.get(item["status"], 0) + 1

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"migrate_transcript_filenames [{mode}]")
    print(f"  rename:          {counts.get('rename', 0)}")
    print(f"  idempotent_skip: {counts.get('idempotent_skip', 0)}")
    print(f"  collision:       {counts.get('collision', 0)}")
    print(f"  missing_file:    {counts.get('missing_file', 0)}")
    print(f"  empty_path:      {counts.get('empty_path', 0)}")

    collisions = [it for it in plan if it["status"] == "collision"]
    if collisions:
        print()
        print(f"[WARN] {len(collisions)} collision(s) — 需人工處理：")
        for c in collisions:
            print(f"  sid:            {c['sid']}")
            print(f"  old_path:       {c['old_path']}")
            print(f"  new_fname:      {c['new_fname']}")
            print(f"  collision_path: {c['collision_path']}")
            print()

    if apply and apply_result:
        print(f"  backup: {apply_result['backup']}")


def main(argv=None) -> int:
    args = parse_args(argv)
    vault = Path(args.vault).resolve() if args.vault else Path(VAULT_DIR)

    manifest = read_sessions_json()
    if not manifest:
        print("[ERROR] sessions.json 不存在或為空", file=sys.stderr)
        return 1

    plan = plan_renames(manifest, vault)

    apply_result = None
    if args.apply:
        backup_ts = _iso_ts()
        apply_result = apply_renames(plan, manifest, vault, backup_ts=backup_ts)

    if args.as_json:
        out: dict = {"plan": plan}
        if apply_result:
            out["apply_result"] = apply_result
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        render_human(plan, apply=args.apply, apply_result=apply_result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
