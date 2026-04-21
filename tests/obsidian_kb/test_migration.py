import sys
import os

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import pytest
import transcript_utils as tu


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
