# kb-ingest Performance Notes

## Identified Bottlenecks & Solutions

### B1: O(N wiki) Full Scan on Every Run

**Problem:** Every pipeline run called `scan_wiki_sources()` which globbed and parsed all wiki `*.md`
files to find `session_id → wiki_page` mappings. O(pages) cost regardless of how many sessions changed.

**Solution:** `wiki_index.json` (stored in `_schema/`) caches the `session_id → [wiki_page_rel_path]`
mapping. `backfill_wiki_transcripts_incremental()` rebuilds only entries for touched sessions.
`fsck.py` provides drift detection (`--dry-run`) and repair (`--fix`).

**Status:** Implemented in `transcript_utils.py`.
- `read_wiki_index()` / `write_wiki_index()` / `build_wiki_index_from_scan()`
- `backfill_wiki_transcripts_incremental()`
- `fsck.py` — standalone drift detection tool

**Observed impact:** Primarily relevant at scale (100+ wiki pages). In sub-100-page vaults,
total script time remains sub-second; the improvement shows up as slower growth with vault size.

### B2: O(N transcripts) Full Index Rebuild on Every Run

**Problem:** `rebuild_transcripts_index()` globbed and re-parsed every transcript's frontmatter
on every upsert, even when only 1–2 transcripts changed.

**Solution:** `rebuild_transcripts_index_from_manifest()` reads transcript metadata from the
in-memory manifest dict (no filesystem glob). Called only when `created + updated > 0`.

**Status:** Implemented in `transcript_utils.py` and used by `upsert_transcripts.py`.

### B3: Double JSONL Read in Delta Branch

**Problem:** For every delta session, `scan_sessions.py` read the JSONL file twice —
once via `parse_session()` for metadata and once via `_read_jsonl_messages()` for
message content with UUIDs. Two sequential opens on the same file per delta candidate.

**Solution:** `_fused_parse_jsonl()` in `scan_sessions.py` performs a single sequential scan
that collects both metadata (title, cwd, models, timestamps, token counts, tool counts) and
messages (with UUID) in one pass. Both the delta branch and new-session branch use this function.
`parse_session()` and `_read_jsonl_messages()` are kept as backward-compat wrappers.

**Status:** Implemented in `scan_sessions.py`.

**Known limitation:** `get_last_message_uuid()` is retained in `transcript_utils.py` for external callers. `backfill_transcripts.py` has been updated to use `_fused_parse_jsonl()` directly and no longer calls `get_last_message_uuid()` — each session's JSONL is read exactly once.

**Observed impact:** Eliminates one full JSONL read per delta session. At sub-second total
script time, the difference is not measurable without at least ~100 sessions per run.

### B4: `get_last_message_uuid` File Re-read in `upsert_transcripts.py`

**Problem:** `upsert_transcripts.py` called `get_last_message_uuid(jsonl_path)` for every
session to obtain the last UUID, re-reading the entire JSONL even though `scan_sessions.py`
had already computed it during `_fused_parse_jsonl`.

**Solution:** `scan_sessions.py` now includes `last_processed_msg_uuid` in every session dict
it outputs. `upsert_transcripts.py` uses:
```python
uuid = session.get("last_processed_msg_uuid", "") or (
    get_last_message_uuid(jsonl_path) if jsonl_path else ""
)
```
Prefers the pre-computed value; falls back to file read for callers that don't supply the field
(e.g., `backfill_transcripts.py`, external drivers).

**Status:** Implemented in `upsert_transcripts.py` (both delta and new-session paths).

---

## Optimization Summary

| Bottleneck | Change | Condition for measurable gain |
|------------|--------|-------------------------------|
| B1 | `wiki_index.json` incremental cache | 100+ wiki pages in vault |
| B2 | Manifest-driven transcript index, skip-if-no-change | 200+ transcripts |
| B3 | `_fused_parse_jsonl` single-pass (no double-read) | 100+ sessions/run with large JSONL files |
| B4 | Scan-provided UUID; eliminates upsert re-read | 100+ sessions/run |

All four optimizations are implemented. Script-layer timing remains sub-second on typical vaults
(<50 sessions/run, <100 wiki pages). The optimizations are most visible during `--all` bulk
backfill runs or when vault size grows to hundreds of pages/transcripts.

---

## wiki_index.json Schema

```json
{
  "schema_version": 1,
  "generated_at": "<iso8601>",
  "session_to_wiki": {
    "<session_id>": ["wiki/rel/path.md", ...]
  }
}
```

**Why session-keyed:** Primary lookup is "given a session, which wiki pages reference it?"
Session-keyed makes this O(1) instead of O(pages).

**Why vault-relative paths:** Portability — vault can be moved without invalidating the index.

**Invalidation:** `fsck.py --fix` rebuilds from scratch. Incremental updates via
`backfill_wiki_transcripts_incremental()`.

---

## bench_ingest.py

`bench_ingest.py` measures per-phase script timing:
- `scan_ms` — scan_sessions.py wall-clock
- `fsck_ms` — fsck.py dry-run
- `wiki_index_ms` — fsck.py --fix
- `update_overview_ms` / `update_watermark_ms`
- `total_script_ms` — sum of core phases

`--equivalence` mode: runs scan_sessions.py twice and verifies the session-id sets are identical.
Use after any scan logic change to confirm output stability.

`--b1-compare [--touched N]` mode: in-process benchmark comparing legacy `backfill_wiki_transcripts()` vs incremental `backfill_wiki_transcripts_incremental()` on the current vault's manifest. The `--touched N` parameter (default: 3) controls how many session IDs are passed to the incremental path, simulating a typical delta run. Results are written to `.omc/bench/kb-ingest-b1-<ts>.json`.

Baseline measurement (manifest_sessions=198, touched=3): legacy=4.42ms, incremental=0.07ms, gain=98.42%.
