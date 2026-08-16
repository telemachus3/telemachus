"""Changelog fragments — one file per change, assembled at release time.

`CHANGELOG.md` is the one file every change touches, which makes it the one
file every parallel branch collides on. The collision is not incidental: two
branches that each add an entry at the top of `[Unreleased]` conflict by
construction, however unrelated their actual work. Observed on this repository
the moment a second branch stayed open for a day.

So branches stop writing to it. Each change drops a file under `changelog.d/`,
named after its branch, and nothing else. Two branches never touch the same
path, so the merge is always clean. `assemble` folds the fragments into
`[Unreleased]` and deletes them, and that runs once, on the release branch,
where there is nobody to collide with.

A fragment is a markdown file whose first line names the section:

    Fixed

    - **`gpx`: a repeated timestamp is judged per track.** ...

Sections follow Keep a Changelog: Added, Changed, Deprecated, Removed, Fixed,
Security. `release.yml` reads the assembled `CHANGELOG.md`, so the published
release notes are unaffected by any of this.

Usage::

    python3 tools/changelog.py check        # what is waiting, and for whom
    python3 tools/changelog.py assemble     # fold into CHANGELOG.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAGMENTS = ROOT / "changelog.d"
CHANGELOG = ROOT / "CHANGELOG.md"
UNRELEASED = "## [Unreleased]"

# Keep a Changelog order. A fragment naming anything else is refused rather
# than filed under a heading of its own invention.
SECTIONS = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


class FragmentError(ValueError):
    """A fragment cannot be read as one."""


def read_fragments() -> dict[str, list[tuple[str, str]]]:
    """Group fragment bodies by section, in filename order within a section."""
    found: dict[str, list[tuple[str, str]]] = {}
    for path in sorted(FRAGMENTS.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        head = next((line.strip() for line in lines if line.strip()), "")
        section = head.rstrip(":").strip()
        if section not in SECTIONS:
            raise FragmentError(
                f"{path.name}: first line is {head!r}, expected one of "
                f"{', '.join(SECTIONS)}")
        start = lines.index(head if head in lines else head + ":") + 1
        body = "\n".join(lines[start:]).strip("\n")
        if not body:
            raise FragmentError(f"{path.name}: no entry under {section}")
        found.setdefault(section, []).append((path.name, body))
    return found


def cmd_check() -> int:
    try:
        found = read_fragments()
    except FragmentError as exc:
        print(f"invalid fragment — {exc}", file=sys.stderr)
        return 1
    if not found:
        print("no fragment waiting")
        return 0
    total = sum(len(v) for v in found.values())
    print(f"{total} fragment(s) waiting:")
    for section in SECTIONS:
        for name, _ in found.get(section, []):
            print(f"  {section:<10} {name}")
    return 0


def split_sections(block: str) -> tuple[str, dict[str, list[str]]]:
    """Split an `[Unreleased]` block into its heading and its subsections.

    Returned as a mapping so an incoming fragment merges into the subsection
    already there instead of opening a second one beside it. Writing a fresh
    `### Added` under a section that has one is how the malformed changelog
    this tool exists to prevent came about in the first place, and appending
    without reading back would reproduce it here.
    """
    head, *parts = re.split(r"^### ", block, flags=re.M)
    groups: dict[str, list[str]] = {}
    for part in parts:
        name, _, body = part.partition("\n")
        body = body.strip("\n")
        if body:
            groups.setdefault(name.strip(), []).append(body)
    return head.rstrip("\n"), groups


def cmd_assemble() -> int:
    try:
        found = read_fragments()
    except FragmentError as exc:
        print(f"invalid fragment — {exc}", file=sys.stderr)
        return 1
    if not found:
        print("no fragment to assemble")
        return 0

    text = CHANGELOG.read_text(encoding="utf-8")
    if UNRELEASED not in text:
        print(f"{CHANGELOG.name}: no {UNRELEASED} heading to write under",
              file=sys.stderr)
        return 1

    start = text.index(UNRELEASED)
    nxt = text.find("\n## [", start + len(UNRELEASED))
    end = nxt if nxt != -1 else len(text)
    block, rest = text[start:end], text[end:]

    # A trailing horizontal rule belongs to the block's presentation, not to
    # its last entry, so it is set aside and put back after the rewrite.
    trailer = ""
    rule = re.search(r"\n+---\s*$", block)
    if rule:
        trailer, block = "\n\n---\n", block[:rule.start()]

    head, groups = split_sections(block)
    for section, entries in found.items():
        groups.setdefault(section, []).extend(body for _, body in entries)

    # Known sections in Keep a Changelog order; anything already in the file
    # under another heading is kept rather than dropped on the floor.
    ordered = SECTIONS + [s for s in groups if s not in SECTIONS]
    out = [head, ""]
    for section in ordered:
        if groups.get(section):
            out += [f"### {section}", "", "\n\n".join(groups[section]), ""]

    merged = "\n".join(out).rstrip("\n") + trailer
    CHANGELOG.write_text(text[:start] + merged + rest, encoding="utf-8")

    for path in sorted(FRAGMENTS.glob("*.md")):
        if path.name.lower() != "readme.md":
            path.unlink()

    total = sum(len(v) for v in found.values())
    print(f"{total} fragment(s) folded into {CHANGELOG.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["check", "assemble"])
    args = parser.parse_args()
    return cmd_check() if args.command == "check" else cmd_assemble()


if __name__ == "__main__":
    raise SystemExit(main())
