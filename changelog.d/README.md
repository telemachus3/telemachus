# Changelog fragments

One file per change. Branches write here, never in `CHANGELOG.md`.

## Why

`CHANGELOG.md` is the one file every change touches, so it is the one file
every parallel branch collides on. Two branches each adding an entry at the top
of `[Unreleased]` conflict by construction, however unrelated their work.

The failure that actually cost us was quieter than a conflict. Two branches
each appended their own `### Fixed` and `### Added` under `[Unreleased]`. Both
merges succeeded, git reported nothing, and the section ended up carrying five
subheadings for three categories. A conflict is loud and gets resolved; a
duplicated heading is discovered weeks later in published release notes, since
`release.yml` extracts its notes from this file by regex and falls back
silently on `See CHANGELOG.md for <tag>.`

Fragments remove the shared state. Two branches never touch the same path, so
concurrent appends cannot interfere.

## Writing one

Create `changelog.d/<branch-name>.md`. First line names the section, the rest
is the entry as it should appear:

```markdown
Fixed

- **`gpx`: a repeated timestamp is judged per track.** The adapter filled
  `device_id` with the GPX `creator`, so the dedup key collapsed to `ts` alone.
```

Sections follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):
`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Anything else
is refused rather than filed under an invented heading.

Name the file after the branch. It is the one string guaranteed unique across
concurrent work, and it says who to ask when an entry is unclear.

## Releasing

```sh
python3 tools/changelog.py check      # what is waiting, and under which section
python3 tools/changelog.py assemble   # fold into CHANGELOG.md, delete fragments
```

`assemble` writes under `## [Unreleased]`, groups by section in Keep a
Changelog order, and orders entries within a section by filename, so two runs
on the same fragments produce the same text.

**Run it before tagging.** `release.yml` reads the assembled `CHANGELOG.md` to
build its release notes, and it looks for `## [<version>]`. So the release
sequence is: `assemble`, rename `[Unreleased]` to the version being cut, commit,
then tag. Tagging first yields notes that say `See CHANGELOG.md for <tag>.`
without reporting an error.
