import sys
import os
import json

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import pytest
import transcript_utils as tu
from fsck import run_fsck


def _make_wiki_page(wiki_dir, filename, session_id):
    content = (
        f"---\ntitle: {filename}\nsources:\n"
        f"  - session: {session_id}\n    date: 2026-04-21\n---\n# {filename}\n"
    )
    (wiki_dir / filename).write_text(content, encoding="utf-8")


@pytest.fixture
def fsck_vault(tmp_path):
    vault = tmp_path / "vault"
    (vault / "wiki").mkdir(parents=True)
    (vault / "_schema").mkdir()
    (vault / "_schema" / "sessions.json").write_text("{}", encoding="utf-8")
    return vault


def test_fsck_detects_missing_from_index(fsck_vault):
    """Wiki page exists but not in index → has_drift=True, session in missing_from_index."""
    wiki_dir = fsck_vault / "wiki"
    _make_wiki_page(wiki_dir, "p.md", "sid-new")
    tu.write_wiki_index({"schema_version": 1, "session_to_wiki": {}}, str(fsck_vault))

    has_drift, report = run_fsck(wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault))
    assert has_drift is True
    assert "sid-new" in report["missing_from_index"]


def test_fsck_detects_manually_edited_sources(fsck_vault):
    """User edits wiki frontmatter → drift detected; --fix → no more drift."""
    wiki_dir = fsck_vault / "wiki"
    _make_wiki_page(wiki_dir, "p.md", "sid-orig")
    tu.write_wiki_index(
        {"schema_version": 1, "session_to_wiki": {"sid-orig": ["wiki/p.md"]}},
        str(fsck_vault),
    )

    # User adds another session to frontmatter
    (wiki_dir / "p.md").write_text(
        "---\ntitle: p\nsources:\n  - session: sid-orig\n    date: 2026-04-21\n"
        "  - session: sid-added\n    date: 2026-04-21\n---\n# p\n",
        encoding="utf-8",
    )

    has_drift, _ = run_fsck(wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault))
    assert has_drift is True

    run_fsck(wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault), fix=True)

    has_drift_after, _ = run_fsck(wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault))
    assert has_drift_after is False


def test_fsck_verify_cross_detects_dangling(fsck_vault):
    """Index references deleted wiki page → verify_cross reports dangling."""
    wiki_dir = fsck_vault / "wiki"
    tu.write_wiki_index(
        {"schema_version": 1, "session_to_wiki": {"sid-ghost": ["wiki/gone.md"]}},
        str(fsck_vault),
    )

    has_drift, report = run_fsck(
        wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault), verify_cross=True
    )
    assert has_drift is True
    assert any("dangling" in issue for issue in report.get("cross_issues", []))


def test_fsck_no_drift_when_synced(fsck_vault):
    """Index matches wiki → no drift."""
    wiki_dir = fsck_vault / "wiki"
    _make_wiki_page(wiki_dir, "p.md", "sid-ok")
    tu.write_wiki_index(
        {"schema_version": 1, "session_to_wiki": {"sid-ok": ["wiki/p.md"]}},
        str(fsck_vault),
    )

    has_drift, report = run_fsck(wiki_dir=str(wiki_dir), vault_dir=str(fsck_vault))
    assert has_drift is False
    assert report["drift_count"] == 0
