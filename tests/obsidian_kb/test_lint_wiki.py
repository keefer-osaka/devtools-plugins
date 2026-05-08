import sys
import os

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-lint/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

from datetime import date
from pathlib import Path

import pytest

import lint_wiki as lw


def _make_page(name="foo.md", text="", fm=None, body=""):
    return (Path(name), text, fm or {}, body)


# ── extract_code_values ───────────────────────────────────────────────────────

class TestExtractCodeValues:
    def test_value_in_fenced_block(self):
        body = "```\n\"my_setting_name\"\n```"
        assert "my_setting_name" in lw.extract_code_values(body)

    def test_value_in_backtick_span(self):
        body = "Use `my-flag` for this."
        assert "my-flag" in lw.extract_code_values(body)

    def test_skips_short_tokens(self):
        body = "Use `no` or `yes` or `md` or `json`."
        vals = lw.extract_code_values(body)
        assert "no" not in vals
        assert "json" not in vals

    def test_skips_non_ascii(self):
        body = "```\n\"主題包含\"\n```"
        vals = lw.extract_code_values(body)
        assert "主題包含" not in vals

    def test_version_pattern(self):
        body = "```\nversion v1.2.3 here\n```"
        vals = lw.extract_code_values(body)
        assert "v1.2.3" in vals


# ── _link_target_stem ─────────────────────────────────────────────────────────

class TestLinkTargetStem:
    def test_alias(self):
        assert lw._link_target_stem("page|alias") == "page"

    def test_heading(self):
        assert lw._link_target_stem("page#section") == "page"

    def test_spaces_to_dash(self):
        assert lw._link_target_stem("My Page") == "my-page"

    def test_lowercased(self):
        assert lw._link_target_stem("FooBar") == "foobar"


# ── _collect_wikilinks ────────────────────────────────────────────────────────

class TestCollectWikilinks:
    def test_fenced_block_ignored(self):
        text = "```\n[[inside]]\n```"
        assert lw._collect_wikilinks(text) == set()

    def test_code_span_ignored(self):
        text = "the `[[inside]]` token"
        assert lw._collect_wikilinks(text) == set()

    def test_prose_link_collected(self):
        text = "see [[hello-world]] for details"
        assert "hello-world" in lw._collect_wikilinks(text)

    def test_multiple(self):
        text = "[[a]] and [[B]] and [[c#x]]"
        assert lw._collect_wikilinks(text) == {"a", "b", "c"}


# ── check_missing_sources ─────────────────────────────────────────────────────

class TestCheckMissingSources:
    def test_empty_sources_flagged(self):
        pages = [_make_page("a.md", fm={"sources": []})]
        issues = lw.check_missing_sources(pages)
        assert len(issues) == 1

    def test_missing_key_flagged(self):
        pages = [_make_page("a.md", fm={})]
        issues = lw.check_missing_sources(pages)
        assert len(issues) == 1

    def test_with_sources_excluded(self):
        pages = [_make_page("a.md", fm={"sources": [{"session": "s1"}]})]
        issues = lw.check_missing_sources(pages)
        assert issues == []


# ── check_contradicted ────────────────────────────────────────────────────────

class TestCheckContradicted:
    def test_old_contradicted_flagged(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 1))
        pages = [_make_page(
            "a.md",
            fm={"status": "contradicted", "updated": "2025-11-01"},
        )]
        issues = lw.check_contradicted(pages)
        assert len(issues) == 1
        _, days = issues[0]
        assert days >= 30

    def test_recent_not_flagged(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 1))
        pages = [_make_page(
            "a.md",
            fm={"status": "contradicted", "updated": "2025-12-20"},
        )]
        assert lw.check_contradicted(pages) == []

    def test_non_contradicted_ignored(self):
        pages = [_make_page("a.md", fm={"status": "draft"})]
        assert lw.check_contradicted(pages) == []

    def test_bad_date_returns_minus_one(self):
        pages = [_make_page(
            "a.md", fm={"status": "contradicted", "updated": "not-a-date"},
        )]
        issues = lw.check_contradicted(pages)
        assert issues[0][1] == -1


# ── check_stale ───────────────────────────────────────────────────────────────

class TestCheckStale:
    def test_status_stale_flagged(self):
        pages = [_make_page("a.md", fm={"status": "stale"})]
        assert lw.check_stale(pages) == [Path("a.md")]

    def test_old_updated_flagged(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 1))
        pages = [_make_page("a.md", fm={"updated": "2025-09-01"})]
        assert lw.check_stale(pages) == [Path("a.md")]

    def test_recent_updated_not_flagged(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 1))
        pages = [_make_page("a.md", fm={"updated": "2025-11-01"})]
        assert lw.check_stale(pages) == []

    def test_lint_ignore_excludes(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 1))
        pages = [_make_page(
            "a.md",
            fm={"updated": "2025-01-01", "lint_ignore": ["stale"]},
        )]
        assert lw.check_stale(pages) == []


# ── check_cross_author_conflict ───────────────────────────────────────────────

class TestCheckCrossAuthorConflict:
    def test_hard_contradicted_multi_author(self):
        pages = [_make_page(
            "a.md",
            fm={"status": "contradicted", "authors": ["alice", "bob"]},
        )]
        issues = lw.check_cross_author_conflict(pages)
        assert len(issues) == 1
        _, kind, _ = issues[0]
        assert kind == "hard"

    def test_advisory_draft_multi_recent(self, monkeypatch):
        monkeypatch.setattr(lw, "TODAY", date(2026, 1, 10))
        pages = [_make_page(
            "a.md",
            fm={
                "status": "draft",
                "sources": [
                    {"author": "alice", "date": "2026-01-09"},
                    {"author": "bob",   "date": "2026-01-08"},
                ],
            },
        )]
        issues = lw.check_cross_author_conflict(pages)
        assert len(issues) == 1
        _, kind, _ = issues[0]
        assert kind == "advisory"

    def test_local_author_not_counted(self):
        pages = [_make_page(
            "a.md",
            fm={"status": "contradicted", "authors": ["__local__", "alice"]},
        )]
        assert lw.check_cross_author_conflict(pages) == []

    def test_author_comma_string(self):
        pages = [_make_page(
            "a.md",
            fm={"status": "contradicted", "authors": "alice, bob"},
        )]
        issues = lw.check_cross_author_conflict(pages)
        assert len(issues) == 1


# ── check_duplicate_fm_keys ───────────────────────────────────────────────────

class TestCheckDuplicateFmKeys:
    def test_duplicate_flagged(self):
        text = "---\ntype: a\ntype: b\n---\nbody"
        pages = [_make_page("a.md", text=text, fm={}, body="body")]
        issues = lw.check_duplicate_fm_keys(pages)
        assert len(issues) == 1
        assert "type" in issues[0][1]

    def test_clean_not_flagged(self):
        text = "---\ntype: a\nstatus: draft\n---\nbody"
        pages = [_make_page("a.md", text=text, fm={}, body="body")]
        assert lw.check_duplicate_fm_keys(pages) == []


# ── generate_report ───────────────────────────────────────────────────────────

class TestGenerateReport:
    def test_all_sections_present(self):
        empty_results = {key: [] for key, _, _ in lw.REPORT_SECTIONS}
        out = lw.generate_report(empty_results)
        for _, title, _ in lw.REPORT_SECTIONS:
            assert title in out

    def test_total_count(self):
        results = {key: [] for key, _, _ in lw.REPORT_SECTIONS}
        results["missing_sources"] = [Path("a.md"), Path("b.md")]
        out = lw.generate_report(results)
        assert "總計問題：2" in out

    def test_zero_total(self):
        results = {key: [] for key, _, _ in lw.REPORT_SECTIONS}
        out = lw.generate_report(results)
        assert "總計問題：0" in out


# ── TestCheckCanonicalDrift ───────────────────────────────────────────────────

class TestCheckCanonicalDrift:
    def test_no_canonical_files_no_issue(self, tmp_path):
        pages = [_make_page("a.md", body="```\n\"some_value\"\n```")]
        assert lw.check_canonical_drift(pages) == []

    def test_file_missing_flagged(self, tmp_path):
        pages = [_make_page("a.md", fm={"canonical_files": [str(tmp_path / "ghost.md")]}, body="")]
        issues = lw.check_canonical_drift(pages)
        assert len(issues) == 1
        assert issues[0]["type"] == "file_missing"

    def test_value_present_in_canonical_no_issue(self, tmp_path):
        cf = tmp_path / "canon.md"
        cf.write_text("my_setting_name lives here")
        pages = [_make_page("a.md", fm={"canonical_files": [str(cf)]},
                             body="```\n\"my_setting_name\"\n```")]
        assert lw.check_canonical_drift(pages) == []

    def test_value_absent_from_canonical_is_drift(self, tmp_path):
        cf = tmp_path / "canon.md"
        cf.write_text("nothing relevant here")
        pages = [_make_page("a.md", fm={"canonical_files": [str(cf)]},
                             body="```\n\"drifted_value\"\n```")]
        issues = lw.check_canonical_drift(pages)
        assert len(issues) == 1
        assert issues[0]["type"] == "value_drift"
        assert "drifted_value" in issues[0]["detail"]

    def test_lint_ignore_skips(self, tmp_path):
        cf = tmp_path / "canon.md"
        cf.write_text("nothing")
        pages = [_make_page("a.md",
                             fm={"canonical_files": [str(cf)], "lint_ignore": ["canonical_drift"]},
                             body="```\n\"drifted_value\"\n```")]
        assert lw.check_canonical_drift(pages) == []

    def test_canonical_basename_not_flagged(self, tmp_path):
        # lint_wiki.py:114-120 — candidate whose basename == canonical file's basename → filtered
        cf = tmp_path / "special_config.md"
        cf.write_text("content here")
        pages = [_make_page("a.md", fm={"canonical_files": [str(cf)]},
                             body="```\n\"special_config.md\"\n```")]
        assert lw.check_canonical_drift(pages) == []


# ── TestCheckBrokenLinks ──────────────────────────────────────────────────────

class TestCheckBrokenLinks:
    def test_existing_stem_not_issue(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "VAULT_DIR", tmp_path)
        pages = [
            _make_page("foo.md", text="see [[foo-bar]] here"),
            _make_page("foo-bar.md", text=""),
        ]
        assert lw.check_broken_links(pages) == []

    def test_missing_stem_is_issue(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "VAULT_DIR", tmp_path)
        pages = [_make_page("foo.md", text="see [[nonexistent]]")]
        issues = lw.check_broken_links(pages)
        assert len(issues) == 1
        assert issues[0][1] == "nonexistent"

    def test_transcript_stem_resolves(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "VAULT_DIR", tmp_path)
        trans_dir = tmp_path / "transcripts"
        trans_dir.mkdir()
        (trans_dir / "my-transcript.md").write_text("")
        pages = [_make_page("foo.md", text="see [[my-transcript]]")]
        assert lw.check_broken_links(pages) == []

    def test_link_in_code_fence_ignored(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "VAULT_DIR", tmp_path)
        pages = [_make_page("foo.md", text="```\n[[ghost]]\n```")]
        assert lw.check_broken_links(pages) == []


# ── TestCheckOrphanedPages ────────────────────────────────────────────────────

class TestCheckOrphanedPages:
    def test_referenced_page_not_orphaned(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        pages = [
            _make_page("a.md", text="[[b]]"),
            _make_page("b.md", text=""),
        ]
        orphans = lw.check_orphaned_pages(pages)
        assert Path("b.md") not in orphans

    def test_unreferenced_page_is_orphaned(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        pages = [_make_page("lonely.md", text="")]
        orphans = lw.check_orphaned_pages(pages)
        assert Path("lonely.md") in orphans

    def test_index_md_reference_exempts(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[[lonely]]")
        pages = [_make_page("lonely.md", text="")]
        orphans = lw.check_orphaned_pages(pages)
        assert Path("lonely.md") not in orphans


# ── TestCheckIndexMissing ─────────────────────────────────────────────────────

class TestCheckIndexMissing:
    def test_indexed_page_not_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[[alpha]]")
        pages = [_make_page("alpha.md")]
        assert lw.check_index_missing(pages) == []

    def test_unindexed_page_is_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[[other-thing]]")
        pages = [_make_page("beta.md")]
        missing = lw.check_index_missing(pages)
        assert Path("beta.md") in missing

    def test_markdown_link_in_index_counts(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[Title](gamma.md)")
        pages = [_make_page("gamma.md")]
        assert lw.check_index_missing(pages) == []


# ── TestFindAllWikiPages / TestFindAllIndexEntries ────────────────────────────

class TestFindAllWikiPages:
    def test_normal_page_found(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "hello.md").write_text("")
        pages = lw.find_all_wiki_pages()
        assert any(p.name == "hello.md" for p in pages)

    def test_underscore_prefix_skipped(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_private.md").write_text("")
        assert lw.find_all_wiki_pages() == []

    def test_meta_dir_skipped(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        meta = tmp_path / "meta"
        meta.mkdir()
        (meta / "notes.md").write_text("")
        assert lw.find_all_wiki_pages() == []

    def test_top_level_skip_excluded(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "overview.md").write_text("")
        assert lw.find_all_wiki_pages() == []


class TestFindAllIndexEntries:
    def test_wikilink_extracted(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[[My Page]]")
        assert "my-page" in lw.find_all_index_entries()

    def test_markdown_link_extracted(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        (tmp_path / "_index.md").write_text("[Title](my-doc.md)")
        assert "my-doc" in lw.find_all_index_entries()

    def test_empty_wiki_dir_returns_empty(self, monkeypatch, tmp_path):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        assert lw.find_all_index_entries() == set()


# ── TestCheckMissingTldr ──────────────────────────────────────────────────────

def _make_sources_page(wiki_dir, name="foo.md", body="", fm=None):
    """建立絕對路徑的 sources/ 頁面 tuple；不實際 touch 檔案（check_missing_tldr 不讀檔）。"""
    return (wiki_dir / "sources" / name, "", fm or {}, body)


class TestCheckMissingTldr:
    def test_non_sources_page_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = (tmp_path / "concepts" / "foo.md", "", {}, "just prose with no h2")
        issues = lw.check_missing_tldr([page])
        assert issues == []

    def test_missing_h2_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="just prose")
        issues = lw.check_missing_tldr([page])
        assert len(issues) == 1
        assert issues[0] == (page[0], "missing")

    def test_first_h2_not_tldr_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="## Summary\n\ntext")
        issues = lw.check_missing_tldr([page])
        assert len(issues) == 1
        assert issues[0] == (page[0], "first_h2_not_tldr:Summary")

    def test_empty_tldr_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="## TL;DR\n\n## Next")
        issues = lw.check_missing_tldr([page])
        assert len(issues) == 1
        assert issues[0] == (page[0], "empty")

    def test_placeholder_double_brace_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="## TL;DR\n{{summary}}\n")
        issues = lw.check_missing_tldr([page])
        assert len(issues) == 1
        assert issues[0] == (page[0], "placeholder")

    def test_placeholder_html_comment_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="## TL;DR\n<!-- TODO -->\n")
        issues = lw.check_missing_tldr([page])
        assert len(issues) == 1
        assert issues[0] == (page[0], "placeholder")

    def test_valid_tldr_clean(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lw, "WIKI_DIR", tmp_path)
        page = _make_sources_page(tmp_path, body="## TL;DR\n\n本頁主題說明...\n\n## Body")
        issues = lw.check_missing_tldr([page])
        assert issues == []
