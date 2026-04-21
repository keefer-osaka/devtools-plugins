import sys
import os
import json
import io

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import pytest
import transcript_utils as tu
import upsert_transcripts as ut


def _setup_vault(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "transcripts").mkdir(parents=True)
    (vault / "wiki").mkdir()
    (vault / "_schema").mkdir()
    (vault / "_schema" / "sessions.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(tu, "VAULT_DIR", str(vault))
    monkeypatch.setattr(tu, "TRANSCRIPTS_DIR", str(vault / "transcripts"))
    monkeypatch.setattr(tu, "WIKI_DIR", str(vault / "wiki"))
    monkeypatch.setattr(tu, "SESSIONS_JSON_PATH", str(vault / "_schema" / "sessions.json"))
    monkeypatch.setattr(ut, "VAULT_DIR", str(vault))
    monkeypatch.setattr(ut, "TRANSCRIPTS_DIR", str(vault / "transcripts"))
    monkeypatch.setattr(ut, "WIKI_DIR", str(vault / "wiki"))
    return vault


def _run_main(sessions, monkeypatch=None, extra_argv=None, env=None):
    import sys as _sys
    orig_argv = _sys.argv[:]
    _sys.argv = ["upsert_transcripts.py"] + (extra_argv or [])

    if env and monkeypatch:
        for k, v in env.items():
            monkeypatch.setenv(k, v)

    stdin_bak = _sys.stdin
    _sys.stdin = io.StringIO(json.dumps(sessions))
    try:
        ut.main()
    except SystemExit:
        pass
    finally:
        _sys.stdin = stdin_bak
        _sys.argv = orig_argv


_base_session = {
    "session_id": "testsession001",
    "delta": False,
    "title": "Test Session",
    "cwd": "/tmp",
    "date": "2026-04-21",
    "first_ts": "2026-04-21T00:00:00Z",
    "last_ts": "2026-04-21T01:00:00Z",
    "models": ["claude-3"],
    "messages": [{"role": "user", "text": "hello", "timestamp": "2026-04-21T00:00:00Z"}],
    "last_processed_msg_uuid": "uuid-001",
    "new_derived_pages": [],
}


def test_wiki_index_created_on_first_run(tmp_path, monkeypatch):
    """If wiki_index.json doesn't exist, upsert creates it (eager migration)."""
    vault = _setup_vault(tmp_path, monkeypatch)
    _run_main([_base_session])
    assert (vault / "_schema" / "wiki_index.json").exists()
    data = json.loads((vault / "_schema" / "wiki_index.json").read_text())
    assert data["schema_version"] == 1


def test_force_full_scan_flag_uses_legacy_backfill(tmp_path, monkeypatch):
    """--force-full-scan calls legacy backfill_wiki_transcripts, not incremental."""
    vault = _setup_vault(tmp_path, monkeypatch)
    calls = {"full": 0, "incremental": 0}

    monkeypatch.setattr(ut, "backfill_wiki_transcripts", lambda m, d: calls.__setitem__("full", calls["full"] + 1) or 0)
    monkeypatch.setattr(ut, "backfill_wiki_transcripts_incremental", lambda *a, **kw: calls.__setitem__("incremental", calls["incremental"] + 1) or 0)
    monkeypatch.setattr(ut, "build_wiki_index_from_scan", lambda wiki_dir=None, vault_dir=None: tu.write_wiki_index({"schema_version": 1, "session_to_wiki": {}}, vault_dir or str(vault)) or {"schema_version": 1, "session_to_wiki": {}})
    monkeypatch.setattr(tu, "build_wiki_index_from_scan", lambda wiki_dir=None, vault_dir=None: {"schema_version": 1, "session_to_wiki": {}})

    _run_main([_base_session], monkeypatch=monkeypatch, extra_argv=["--force-full-scan"])

    assert calls["full"] == 1
    assert calls["incremental"] == 0


def test_env_var_full_scan_uses_legacy_backfill(tmp_path, monkeypatch):
    """KB_INGEST_FULL_SCAN=1 also triggers legacy full scan path."""
    vault = _setup_vault(tmp_path, monkeypatch)
    calls = {"full": 0, "incremental": 0}

    monkeypatch.setattr(ut, "backfill_wiki_transcripts", lambda m, d: calls.__setitem__("full", calls["full"] + 1) or 0)
    monkeypatch.setattr(ut, "backfill_wiki_transcripts_incremental", lambda *a, **kw: calls.__setitem__("incremental", calls["incremental"] + 1) or 0)
    monkeypatch.setattr(ut, "build_wiki_index_from_scan", lambda wiki_dir=None, vault_dir=None: tu.write_wiki_index({"schema_version": 1, "session_to_wiki": {}}, vault_dir or str(vault)) or {"schema_version": 1, "session_to_wiki": {}})
    monkeypatch.setattr(tu, "build_wiki_index_from_scan", lambda wiki_dir=None, vault_dir=None: {"schema_version": 1, "session_to_wiki": {}})

    monkeypatch.setenv("KB_INGEST_FULL_SCAN", "1")
    _run_main([_base_session], monkeypatch=monkeypatch)

    assert calls["full"] == 1
    assert calls["incremental"] == 0


def test_rebuild_index_skips_when_no_change(tmp_path, monkeypatch):
    """When created=updated=0, rebuild_transcripts_index_from_manifest is not called."""
    vault = _setup_vault(tmp_path, monkeypatch)

    # Pre-create wiki_index.json so eager migration doesn't run
    (vault / "_schema" / "wiki_index.json").write_text(
        '{"schema_version":1,"session_to_wiki":{}}', encoding="utf-8"
    )

    rebuild_calls = []
    monkeypatch.setattr(ut, "rebuild_transcripts_index_from_manifest", lambda m, d: rebuild_calls.append(1))

    # Empty sessions → created=0, updated=0
    _run_main([])

    assert rebuild_calls == [], "rebuild should not be called when no sessions processed"


def test_upsert_prefers_session_uuid_over_jsonl_read(tmp_path, monkeypatch):
    """When session dict carries last_processed_msg_uuid, get_last_message_uuid is NOT called."""
    vault = _setup_vault(tmp_path, monkeypatch)
    (vault / "_schema" / "wiki_index.json").write_text(
        '{"schema_version":1,"session_to_wiki":{}}', encoding="utf-8"
    )

    uuid_read_calls = []
    monkeypatch.setattr(ut, "get_last_message_uuid", lambda path: uuid_read_calls.append(path) or "should-not-be-used")

    session = {**_base_session, "last_processed_msg_uuid": "prebaked-uuid", "jsonl_path": str(tmp_path / "fake.jsonl")}
    _run_main([session])

    manifest = json.loads((vault / "_schema" / "sessions.json").read_text())
    assert manifest["testsession001"]["last_processed_msg_uuid"] == "prebaked-uuid"
    assert uuid_read_calls == [], f"get_last_message_uuid should not be called when uuid pre-supplied, got {uuid_read_calls}"


def test_upsert_falls_back_to_jsonl_read_when_session_missing_uuid(tmp_path, monkeypatch):
    """When session dict has no last_processed_msg_uuid, upsert falls back to get_last_message_uuid."""
    vault = _setup_vault(tmp_path, monkeypatch)
    (vault / "_schema" / "wiki_index.json").write_text(
        '{"schema_version":1,"session_to_wiki":{}}', encoding="utf-8"
    )

    fake_jsonl = tmp_path / "session.jsonl"
    fake_jsonl.write_text("", encoding="utf-8")

    monkeypatch.setattr(ut, "get_last_message_uuid", lambda path: "fallback-uuid")

    session = {
        **_base_session,
        "last_processed_msg_uuid": "",   # empty → triggers fallback
        "jsonl_path": str(fake_jsonl),
    }
    _run_main([session])

    manifest = json.loads((vault / "_schema" / "sessions.json").read_text())
    assert manifest["testsession001"]["last_processed_msg_uuid"] == "fallback-uuid"
