import sys
import os
import json

_base = os.path.dirname(__file__)
# bench_ingest.run_b1_compare only exists in the Obsidian (updated) version
SCRIPTS_DIR_REAL = os.path.abspath(
    os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts')
)
OBSIDIAN_SCRIPTS_DIR = os.path.abspath(
    "/Users/user/claude-code/Obsidian/.claude/skills/kb-ingest/scripts"
)
sys.path.insert(0, SCRIPTS_DIR_REAL)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import pytest
from pathlib import Path
import transcript_utils as tu

# bench_ingest imports from its own SCRIPTS_DIR at runtime; load Obsidian version which has run_b1_compare
sys.path.insert(0, OBSIDIAN_SCRIPTS_DIR)
import bench_ingest as bi


def test_b1_compare_returns_required_keys(tmp_path, monkeypatch):
    """run_b1_compare returns a dict with all required keys."""
    (tmp_path / "wiki").mkdir()

    monkeypatch.setattr(tu, "read_sessions_json", lambda: {"session1": {}, "session2": {}})
    monkeypatch.setattr(tu, "backfill_wiki_transcripts", lambda manifest, wiki_dir: 0)
    monkeypatch.setattr(tu, "backfill_wiki_transcripts_incremental", lambda *a, **kw: 0)
    monkeypatch.setattr(tu, "read_wiki_index", lambda *a, **kw: {})
    monkeypatch.setattr(tu, "build_wiki_index_from_scan", lambda *a, **kw: {})
    monkeypatch.setattr(tu, "WIKI_DIR", str(tmp_path / "wiki"))

    result = bi.run_b1_compare(scripts_dir=Path(OBSIDIAN_SCRIPTS_DIR), touched_count=1)

    required_keys = {"legacy_wiki_ms", "incremental_wiki_ms", "gain_pct", "touched_count", "manifest_sessions"}
    assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"


def test_b1_compare_empty_manifest_no_exception(tmp_path, monkeypatch):
    """run_b1_compare handles empty manifest without raising and returns gain_pct == 0.0."""
    (tmp_path / "wiki").mkdir()

    monkeypatch.setattr(tu, "read_sessions_json", lambda: {})
    monkeypatch.setattr(tu, "backfill_wiki_transcripts", lambda manifest, wiki_dir: 0)
    monkeypatch.setattr(tu, "backfill_wiki_transcripts_incremental", lambda *a, **kw: 0)
    monkeypatch.setattr(tu, "read_wiki_index", lambda *a, **kw: {})
    monkeypatch.setattr(tu, "build_wiki_index_from_scan", lambda *a, **kw: {})
    monkeypatch.setattr(tu, "WIKI_DIR", str(tmp_path / "wiki"))

    result = bi.run_b1_compare(scripts_dir=Path(OBSIDIAN_SCRIPTS_DIR), touched_count=1)

    assert result["gain_pct"] == 0.0
