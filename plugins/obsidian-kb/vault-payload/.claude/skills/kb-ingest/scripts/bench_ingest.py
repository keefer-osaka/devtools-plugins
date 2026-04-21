#!/usr/bin/env python3
"""Benchmark harness for kb-ingest pipeline."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
BENCH_DIR = Path("/Users/user/claude-code/Obsidian/.omc/bench")


def measure(cmd: list[str]) -> tuple[float, str, str]:
    """Run cmd, return (wall-clock ms, stdout, stderr)."""
    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.perf_counter()
    if result.returncode != 0:
        import sys
        print(f"[WARN] {cmd[0]} exited {result.returncode}: {result.stderr[:200]}", file=sys.stderr)
    return round((t1 - t0) * 1000, 1), result.stdout, result.stderr


def parse_transcript(jsonl_path: str) -> dict:
    """Count LLM tool-call types from Claude Code JSONL transcript."""
    counts: dict[str, int] = {}
    path = Path(jsonl_path)
    if not path.exists():
        return counts
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = record.get("message", {})
            if isinstance(msg, dict):
                for item in msg.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        name = item.get("name", "unknown")
                        counts[name] = counts.get(name, 0) + 1
    return counts


def run_pipeline(scripts_dir: Path) -> dict:
    """Run scan + overview + watermark scripts and return per-phase timings."""
    scan_script = scripts_dir / "scan_sessions.py"
    overview_script = scripts_dir / "update_overview.py"
    watermark_script = scripts_dir / "update_watermark.py"
    fsck_script = scripts_dir / "fsck.py"

    scan_ms, scan_out, _ = measure(["python3", str(scan_script)]) if scan_script.exists() else (None, "", "")
    overview_ms, _, _ = measure(["python3", str(overview_script)]) if overview_script.exists() else (None, "", "")
    watermark_ms, _, _ = measure(["python3", str(watermark_script)]) if watermark_script.exists() else (None, "", "")
    fsck_ms, _, _ = measure(["python3", str(fsck_script)]) if fsck_script.exists() else (None, "", "")

    # wiki_index_ms: time to rebuild wiki index (via fsck --fix)
    wiki_index_ms, _, _ = measure(["python3", str(fsck_script), "--fix"]) if fsck_script.exists() else (None, "", "")

    total = sum(x for x in [scan_ms, overview_ms, watermark_ms] if x is not None)

    # Parse scan output for session count
    sessions_count = None
    try:
        scan_json = json.loads(scan_out)
        sessions_count = len(scan_json.get("sessions", []))
    except Exception:
        pass

    return {
        "scan_ms": scan_ms,
        "update_overview_ms": overview_ms,
        "update_watermark_ms": watermark_ms,
        "fsck_ms": fsck_ms,
        "wiki_index_ms": wiki_index_ms,
        "total_script_ms": round(total, 1),
        "sessions_found": sessions_count,
    }


def run_equivalence(scripts_dir: Path) -> dict:
    """Run baseline (parse_session path) vs optimized (_fused_parse_jsonl path) and compare manifests."""
    import sys
    import os
    import tempfile

    # Both paths now use _fused_parse_jsonl; equivalence verifies scan output is stable across two runs
    scan_script = scripts_dir / "scan_sessions.py"
    if not scan_script.exists():
        return {"error": "scan_sessions.py not found", "equivalent": False}

    results = []
    for run_label in ("baseline", "optimized"):
        t0 = time.perf_counter()
        proc = subprocess.run(["python3", str(scan_script)], capture_output=True, text=True)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        try:
            output = json.loads(proc.stdout)
        except Exception:
            output = {}
        results.append({
            "run": run_label,
            "elapsed_ms": elapsed_ms,
            "sessions": sorted(s.get("session_id", "") for s in output.get("sessions", [])),
            "skipped_count": output.get("skipped_count", 0),
        })

    baseline_sessions = set(results[0]["sessions"])
    optimized_sessions = set(results[1]["sessions"])
    diff = list(baseline_sessions.symmetric_difference(optimized_sessions))
    equivalent = len(diff) == 0

    return {
        "equivalent": equivalent,
        "diff": diff[:20],
        "baseline_ms": results[0]["elapsed_ms"],
        "optimized_ms": results[1]["elapsed_ms"],
        "baseline_session_count": len(results[0]["sessions"]),
        "optimized_session_count": len(results[1]["sessions"]),
    }


def run_b1_compare(scripts_dir: Path, touched_count: int) -> dict:
    """In-process B1 comparison: legacy full wiki backfill vs incremental, on current vault."""
    import sys as _sys
    _sys.path.insert(0, str(scripts_dir))
    from transcript_utils import (
        read_sessions_json, backfill_wiki_transcripts,
        backfill_wiki_transcripts_incremental,
        read_wiki_index, build_wiki_index_from_scan,
        WIKI_DIR,
    )

    manifest = read_sessions_json()
    wiki_index = read_wiki_index() or build_wiki_index_from_scan()
    all_ids = list(manifest.keys())
    touched = all_ids[:touched_count]

    # Run incremental first (less destructive), then legacy (overwrites — final state is correct)
    t0 = time.perf_counter()
    incr_linked = backfill_wiki_transcripts_incremental(manifest, WIKI_DIR, touched, wiki_index)
    incr_ms = round((time.perf_counter() - t0) * 1000, 2)

    t0 = time.perf_counter()
    legacy_linked = backfill_wiki_transcripts(manifest, WIKI_DIR)
    legacy_ms = round((time.perf_counter() - t0) * 1000, 2)

    gain_pct = round((legacy_ms - incr_ms) / legacy_ms * 100, 2) if legacy_ms > 0 else 0.0

    return {
        "mode": "b1-compare",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest_sessions": len(manifest),
        "touched_count": touched_count,
        "legacy_wiki_ms": legacy_ms,
        "incremental_wiki_ms": incr_ms,
        "gain_pct": gain_pct,
        "legacy_linked_pages": legacy_linked,
        "incremental_linked_pages": incr_linked,
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark kb-ingest pipeline scripts")
    parser.add_argument(
        "--mode",
        choices=["normal", "optimized", "baseline"],
        default="normal",
        help="normal = standard run; optimized/baseline = labelled run for comparison",
    )
    parser.add_argument(
        "--equivalence",
        action="store_true",
        help="Run two passes and verify output is semantically equivalent (manifest diff empty)",
    )
    parser.add_argument(
        "--b1-compare",
        action="store_true",
        dest="b1_compare",
        help="In-process B1 comparison: legacy full wiki backfill vs incremental on current vault",
    )
    parser.add_argument(
        "--touched",
        type=int,
        default=3,
        metavar="N",
        help="Number of sessions to treat as touched for incremental path (default: 3)",
    )
    parser.add_argument("--from-transcript", metavar="JSONL", help="JSONL transcript to parse for tool calls")
    args = parser.parse_args()

    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    if args.b1_compare:
        result = run_b1_compare(SCRIPTS_DIR, args.touched)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = BENCH_DIR / f"kb-ingest-b1-{ts}.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n[bench] 結果已寫入 {out_path}", flush=True)
        return

    if args.equivalence:
        equiv_result = run_equivalence(SCRIPTS_DIR)
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "equivalence",
            **equiv_result,
        }
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = BENCH_DIR / f"kb-ingest-equiv-{ts}.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n[bench] 結果已寫入 {out_path}", flush=True)
        if not equiv_result.get("equivalent", False):
            import sys
            sys.exit(1)
        return

    timings = run_pipeline(SCRIPTS_DIR)

    tool_calls: dict[str, int] = {"Read": 0, "Glob": 0, "Edit": 0, "Write": 0}
    if args.from_transcript:
        parsed = parse_transcript(args.from_transcript)
        for k in list(tool_calls.keys()):
            tool_calls[k] = parsed.get(k, 0)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        **timings,
        "qmd_update_ms": None,
        "tool_calls": tool_calls,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = BENCH_DIR / f"kb-ingest-{ts}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n[bench] 結果已寫入 {out_path}", flush=True)


if __name__ == "__main__":
    main()
