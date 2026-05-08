import sys
import os

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import json
from datetime import timezone, timedelta

import pytest
import transcript_utils as tu
import migrate_transcript_filenames as mtf
import wiki_utils as wu
from transcript_utils import make_transcript_filename


def test_midway_crash_leaves_no_partial_state(tmp_path, monkeypatch):
    """
    If os.replace crashes after writing .tmp, wiki_index.json must not exist.
    Verifies atomic write guarantee via tmp + os.replace pattern.
    """
    vault = tmp_path / "vault"
    (vault / "_schema").mkdir(parents=True)

    wiki_index_path = vault / "_schema" / "wiki_index.json"
    assert not wiki_index_path.exists()

    original_replace = os.replace

    def crash_on_replace(src, dst):
        if dst.endswith("wiki_index.json"):
            raise RuntimeError("simulated crash after tmp write")
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", crash_on_replace)

    with pytest.raises(RuntimeError, match="simulated crash"):
        tu.write_wiki_index({"schema_version": 1, "session_to_wiki": {}}, str(vault))

    assert not wiki_index_path.exists(), "wiki_index.json must not exist after crash (atomic write)"


# ── Fixtures / helpers for TestPlanRenames & TestApplyRenames ─────────────────

@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "transcripts").mkdir(parents=True)
    (v / "_schema").mkdir()
    return v


@pytest.fixture
def fixed_tz(monkeypatch):
    """鎖定 VAULT_TZ 為 UTC+8，讓 make_transcript_filename 在所有 CI host 上輸出穩定。

    NOTE: patch 必須打在 wiki_utils 而非 transcript_utils。
    make_transcript_filename 透過 format_tw_date 呼叫 astimezone(VAULT_TZ)，
    format_tw_date 定義在 wiki_utils.py，其內部的 VAULT_TZ 解析到
    wiki_utils 模組的 global，看不到 tu.VAULT_TZ 的別名修改。
    """
    monkeypatch.setattr(wu, "VAULT_TZ", timezone(timedelta(hours=8)))


def _write_transcript(vault, fname, *, first_ts="", session_id="", title=""):
    """寫一個含 frontmatter 的空 transcript 到 vault/transcripts/<fname>。"""
    fm_lines = []
    if first_ts:
        fm_lines.append(f"first_ts: {first_ts}")
    if session_id:
        fm_lines.append(f"session_id: {session_id}")
    if title:
        fm_lines.append(f"title: {title}")
    fm = "---\n" + "\n".join(fm_lines) + "\n---\n" if fm_lines else ""
    (vault / "transcripts" / fname).write_text(fm + "body\n", encoding="utf-8")


def _ensure_sessions_json(vault, manifest):
    (vault / "_schema" / "sessions.json").write_text(
        json.dumps({"sessions": manifest}, ensure_ascii=False), encoding="utf-8"
    )


# ── TestPlanRenames ───────────────────────────────────────────────────────────

class TestPlanRenames:
    def test_empty_path(self, vault, fixed_tz):
        manifest = {"sid1": {"transcript_path": ""}}
        plan = mtf.plan_renames(manifest, vault)
        assert len(plan) == 1
        assert plan[0]["status"] == "empty_path"
        assert plan[0]["sid"] == "sid1"

    def test_missing_file(self, vault, fixed_tz):
        manifest = {"sid1": {"transcript_path": "transcripts/ghost.md"}}
        plan = mtf.plan_renames(manifest, vault)
        assert len(plan) == 1
        assert plan[0]["status"] == "missing_file"
        assert plan[0]["sid"] == "sid1"

    def test_idempotent_skip(self, vault, fixed_tz):
        sid = "abcdef123456"
        first_ts = "2026-01-15T10:00:00+08:00"
        title = "hello world"
        good_fname = make_transcript_filename(first_ts, sid, title)
        _write_transcript(vault, good_fname, first_ts=first_ts, session_id=sid, title=title)
        manifest = {sid: {"transcript_path": f"transcripts/{good_fname}"}}
        plan = mtf.plan_renames(manifest, vault)
        assert len(plan) == 1
        assert plan[0]["status"] == "idempotent_skip"

    def test_rename(self, vault, fixed_tz):
        sid = "abcdef123456"
        first_ts = "2026-01-15T10:00:00+08:00"
        title = "hello world"
        expected_new_fname = make_transcript_filename(first_ts, sid, title)
        _write_transcript(vault, "broken.md", first_ts=first_ts, session_id=sid, title=title)
        manifest = {sid: {"transcript_path": "transcripts/broken.md"}}
        plan = mtf.plan_renames(manifest, vault)
        assert len(plan) == 1
        item = plan[0]
        assert item["status"] == "rename"
        assert item["old_stem"] == "broken"
        assert item["new_fname"] == expected_new_fname
        assert item["sid"] == sid

    def test_collision(self, vault, fixed_tz):
        sid = "abcdef123456"
        first_ts = "2026-01-15T10:00:00+08:00"
        title = "hello world"
        expected_new_fname = make_transcript_filename(first_ts, sid, title)
        _write_transcript(vault, "broken.md", first_ts=first_ts, session_id=sid, title=title)
        _write_transcript(vault, expected_new_fname, first_ts=first_ts, session_id=sid, title=title)
        manifest = {sid: {"transcript_path": "transcripts/broken.md"}}
        plan = mtf.plan_renames(manifest, vault)
        assert len(plan) == 1
        item = plan[0]
        assert item["status"] == "collision"
        assert item["new_fname"] == expected_new_fname
        assert "collision_path" in item


# ── TestApplyRenames ──────────────────────────────────────────────────────────

class TestApplyRenames:
    def test_apply_renames_success(self, vault, fixed_tz, monkeypatch):
        """1 entry rename：驗證檔案系統 + bak + capture write_sessions_json payload。"""
        sid = "abcdef123456"
        first_ts = "2026-01-15T10:00:00+08:00"
        title = "hello world"
        new_fname = make_transcript_filename(first_ts, sid, title)
        _write_transcript(vault, "broken.md", first_ts=first_ts, session_id=sid, title=title)
        manifest = {sid: {"transcript_path": "transcripts/broken.md"}}
        _ensure_sessions_json(vault, manifest)

        plan = [{
            "sid": sid,
            "status": "rename",
            "old_path": "transcripts/broken.md",
            "old_stem": "broken",
            "new_fname": new_fname,
        }]

        captured = {}
        def fake_write(m):
            captured["manifest"] = dict(m)
        monkeypatch.setattr(mtf, "write_sessions_json", fake_write)
        monkeypatch.setattr(mtf, "rebuild_transcripts_index_from_manifest", lambda m, d: None)

        result = mtf.apply_renames(plan, manifest, vault, backup_ts="20260101T000000Z")

        assert not (vault / "transcripts" / "broken.md").exists()
        assert (vault / "transcripts" / new_fname).exists()
        assert (vault / "_schema" / "sessions.json.bak.20260101T000000Z").exists()
        assert result == {"renamed": 1, "backup": "sessions.json.bak.20260101T000000Z"}
        assert captured.get("manifest", {}).get(sid, {}).get("transcript_path") == f"transcripts/{new_fname}"

    def test_apply_renames_two_entries_success(self, vault, fixed_tz, monkeypatch):
        """2 entries 都成功 rename：驗證 batch happy path。"""
        sid_a = "aaaaaa111111"
        sid_b = "bbbbbb222222"
        first_ts_a = "2026-01-15T10:00:00+08:00"
        first_ts_b = "2026-01-16T10:00:00+08:00"
        new_fname_a = make_transcript_filename(first_ts_a, sid_a, "alpha")
        new_fname_b = make_transcript_filename(first_ts_b, sid_b, "beta")
        _write_transcript(vault, "broken_a.md", first_ts=first_ts_a, session_id=sid_a, title="alpha")
        _write_transcript(vault, "broken_b.md", first_ts=first_ts_b, session_id=sid_b, title="beta")
        manifest = {
            sid_a: {"transcript_path": "transcripts/broken_a.md"},
            sid_b: {"transcript_path": "transcripts/broken_b.md"},
        }
        _ensure_sessions_json(vault, manifest)

        plan = [
            {"sid": sid_a, "status": "rename", "old_path": "transcripts/broken_a.md",
             "old_stem": "broken_a", "new_fname": new_fname_a},
            {"sid": sid_b, "status": "rename", "old_path": "transcripts/broken_b.md",
             "old_stem": "broken_b", "new_fname": new_fname_b},
        ]

        captured = {}
        def fake_write(m):
            captured["manifest"] = dict(m)
        monkeypatch.setattr(mtf, "write_sessions_json", fake_write)
        monkeypatch.setattr(mtf, "rebuild_transcripts_index_from_manifest", lambda m, d: None)

        result = mtf.apply_renames(plan, manifest, vault, backup_ts="20260101T000000Z")

        assert not (vault / "transcripts" / "broken_a.md").exists()
        assert not (vault / "transcripts" / "broken_b.md").exists()
        assert (vault / "transcripts" / new_fname_a).exists()
        assert (vault / "transcripts" / new_fname_b).exists()
        assert result == {"renamed": 2, "backup": "sessions.json.bak.20260101T000000Z"}
        assert captured["manifest"][sid_a]["transcript_path"] == f"transcripts/{new_fname_a}"
        assert captured["manifest"][sid_b]["transcript_path"] == f"transcripts/{new_fname_b}"

    def test_apply_renames_rollback_on_rename_failure(self, vault, fixed_tz, monkeypatch):
        """
        2 entries，第 2 個 os.rename 失敗：驗證 A 被 rollback、B 未動、bak 殘留、SystemExit。

        NOTE: 此測試僅覆蓋 os.rename 階段失敗（migrate_transcript_filenames.py line 154）。
        若失敗發生在 line 158 的 write_sessions_json，manifest dict 已在 line 156-157
        被 mutated，_rollback() 不會還原 dict — 此 limitation 見 Open Questions。
        """
        sid_a = "aaaaaa111111"
        sid_b = "bbbbbb222222"
        first_ts_a = "2026-01-15T10:00:00+08:00"
        first_ts_b = "2026-01-16T10:00:00+08:00"
        new_fname_a = make_transcript_filename(first_ts_a, sid_a, "alpha")
        new_fname_b = make_transcript_filename(first_ts_b, sid_b, "beta")
        _write_transcript(vault, "broken_a.md", first_ts=first_ts_a, session_id=sid_a, title="alpha")
        _write_transcript(vault, "broken_b.md", first_ts=first_ts_b, session_id=sid_b, title="beta")
        manifest = {
            sid_a: {"transcript_path": "transcripts/broken_a.md"},
            sid_b: {"transcript_path": "transcripts/broken_b.md"},
        }
        _ensure_sessions_json(vault, manifest)

        plan = [
            {"sid": sid_a, "status": "rename", "old_path": "transcripts/broken_a.md",
             "old_stem": "broken_a", "new_fname": new_fname_a},
            {"sid": sid_b, "status": "rename", "old_path": "transcripts/broken_b.md",
             "old_stem": "broken_b", "new_fname": new_fname_b},
        ]

        # fake_rename 只在 call_count == 2 raise；若 always-raise，_rollback() 內的
        # os.rename(new_path, old_path) 也會失敗，遮蔽 rollback 行為。
        real_rename = os.rename
        call_count = {"n": 0}
        def fake_rename(src, dst):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise OSError("simulated failure on B")
            return real_rename(src, dst)
        monkeypatch.setattr(os, "rename", fake_rename)
        monkeypatch.setattr(mtf, "write_sessions_json", lambda m: None)
        monkeypatch.setattr(mtf, "rebuild_transcripts_index_from_manifest", lambda m, d: None)

        with pytest.raises(SystemExit, match=r"\[FATAL\] apply failed:.*rolled back 1 renames"):
            mtf.apply_renames(plan, manifest, vault, backup_ts="20260101T000000Z")

        assert (vault / "transcripts" / "broken_a.md").exists()
        assert not (vault / "transcripts" / new_fname_a).exists()
        assert (vault / "transcripts" / "broken_b.md").exists()
        assert not (vault / "transcripts" / new_fname_b).exists()
        # bak 在 try block 外建立，rollback 不刪它（known acceptable）
        assert (vault / "_schema" / "sessions.json.bak.20260101T000000Z").exists()
        # 不 assert manifest dict 狀態 — 只在 os.rename 階段失敗才保證未 mutate
