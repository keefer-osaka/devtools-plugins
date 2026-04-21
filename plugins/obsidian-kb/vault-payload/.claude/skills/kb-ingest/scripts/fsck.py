#!/usr/bin/env python3
"""
fsck.py — kb-ingest consistency check / repair tool.

Usage:
  python3 fsck.py                    # dry-run: print drift report, exit 1 if drift
  python3 fsck.py --fix              # fix wiki_index.json, exit 0
  python3 fsck.py --verify-cross     # check cross-file invariants
  python3 fsck.py --fix --verify-cross
"""
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from transcript_utils import (
    VAULT_DIR, WIKI_DIR, SESSIONS_JSON_PATH,
    read_sessions_json, read_wiki_index, write_wiki_index,
    scan_wiki_sources, build_wiki_index_from_scan,
)


def run_fsck(wiki_dir=None, sessions_json_path=None, vault_dir=None, fix=False, verify_cross=False):
    """
    Returns (has_drift: bool, report: dict)
    """
    wiki_dir = wiki_dir or WIKI_DIR
    vault_dir = vault_dir or VAULT_DIR
    sessions_json_path = sessions_json_path or SESSIONS_JSON_PATH

    # 1. Ground truth：從 wiki/ 全量掃描
    expected_map = scan_wiki_sources(wiki_dir)

    # 2. Current index
    index = read_wiki_index(vault_dir)
    current_map = (index or {}).get("session_to_wiki", {})

    # 3. Diff
    all_sids = set(expected_map) | set(current_map)
    missing = []
    extra = []
    mismatch = []

    for sid in all_sids:
        exp = set(expected_map.get(sid, []))
        cur = set(current_map.get(sid, []))
        if exp and not cur:
            missing.append(sid)
        elif cur and not exp:
            extra.append(sid)
        elif exp != cur:
            mismatch.append(sid)

    has_drift = bool(missing or extra or mismatch)

    report = {
        "missing_from_index": missing[:20],
        "extra_in_index": extra[:20],
        "mismatched": mismatch[:20],
        "drift_count": len(missing) + len(extra) + len(mismatch),
    }

    cross_issues = []
    if verify_cross:
        sessions = read_sessions_json()
        for sid in current_map:
            if sid not in sessions:
                cross_issues.append(f"session {sid[:8]} in index but not in sessions.json")
            for rel_path in current_map[sid]:
                abs_path = os.path.join(vault_dir, rel_path)
                if not os.path.exists(abs_path):
                    cross_issues.append(f"dangling: {rel_path} (session {sid[:8]})")
        report["cross_issues"] = cross_issues[:20]
        if cross_issues:
            has_drift = True

    if fix:
        new_index = build_wiki_index_from_scan(wiki_dir, vault_dir)
        if verify_cross and cross_issues:
            clean_map = {
                sid: [p for p in paths if os.path.exists(os.path.join(vault_dir, p))]
                for sid, paths in new_index["session_to_wiki"].items()
            }
            new_index["session_to_wiki"] = clean_map
            write_wiki_index(new_index, vault_dir)
        report["fixed"] = True

    return has_drift, report


def main():
    fix = "--fix" in sys.argv
    verify_cross = "--verify-cross" in sys.argv

    has_drift, report = run_fsck(fix=fix, verify_cross=verify_cross)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if fix:
        sys.exit(0)
    sys.exit(1 if has_drift else 0)


if __name__ == "__main__":
    main()
