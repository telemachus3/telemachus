"""Tests for the changelog fragment tool.

The tool exists to stop a malformed `[Unreleased]` section reaching a release.
Its first implementation appended a fresh `### Added` under a section that
already had one, which is the exact defect it was written to prevent, and no
conflict or error reported it. So the merge behaviour is pinned here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "changelog_tool", Path(__file__).parent / "changelog.py")
changelog = importlib.util.module_from_spec(SPEC)
sys.modules["changelog_tool"] = changelog
SPEC.loader.exec_module(changelog)


EXISTING = """# Changelog

---

## [Unreleased]

### Added

- an entry that was already here

### Fixed

- a fix that was already here

---

## [1.0] — 2026-01-01

### Added

- the released one
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "CHANGELOG.md").write_text(EXISTING, encoding="utf-8")
    monkeypatch.setattr(changelog, "FRAGMENTS", tmp_path / "changelog.d")
    monkeypatch.setattr(changelog, "CHANGELOG", tmp_path / "CHANGELOG.md")
    return tmp_path


def fragment(repo, name, text):
    (repo / "changelog.d" / name).write_text(text, encoding="utf-8")


def sections(repo):
    """The `### ` headings of the [Unreleased] block, in order."""
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    start = text.index("## [Unreleased]")
    end = text.index("\n## [", start + 5)
    return [line[4:].strip()
            for line in text[start:end].splitlines() if line.startswith("### ")]


def test_a_fragment_merges_into_the_section_already_there(repo):
    fragment(repo, "b-branch.md", "Added\n\n- the new entry\n")
    assert changelog.cmd_assemble() == 0
    assert sections(repo) == ["Added", "Fixed"]      # not Added, Added, Fixed
    body = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "- an entry that was already here" in body
    assert "- the new entry" in body


def test_sections_come_out_in_keep_a_changelog_order(repo):
    fragment(repo, "a.md", "Fixed\n\n- f\n")
    fragment(repo, "b.md", "Changed\n\n- c\n")
    changelog.cmd_assemble()
    assert sections(repo) == ["Added", "Changed", "Fixed"]


def test_entries_of_one_section_are_ordered_by_filename(repo):
    fragment(repo, "z-last.md", "Changed\n\n- zzz\n")
    fragment(repo, "a-first.md", "Changed\n\n- aaa\n")
    changelog.cmd_assemble()
    body = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert body.index("- aaa") < body.index("- zzz")


def test_the_released_section_is_untouched(repo):
    fragment(repo, "x.md", "Added\n\n- new\n")
    changelog.cmd_assemble()
    body = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [1.0] — 2026-01-01" in body
    assert "- the released one" in body
    assert body.count("## [Unreleased]") == 1


def test_fragments_are_consumed(repo):
    fragment(repo, "x.md", "Added\n\n- new\n")
    changelog.cmd_assemble()
    assert list((repo / "changelog.d").glob("*.md")) == []


def test_an_unknown_section_is_refused_rather_than_invented(repo):
    fragment(repo, "x.md", "Improved\n\n- nope\n")
    assert changelog.cmd_assemble() == 1
    assert sections(repo) == ["Added", "Fixed"]      # file left alone


def test_assembling_twice_is_stable(repo):
    fragment(repo, "x.md", "Added\n\n- new\n")
    changelog.cmd_assemble()
    once = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog.cmd_assemble()                          # no fragment left
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == once
