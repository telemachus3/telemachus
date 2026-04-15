# Changelog — Telemachus (monorepo)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-04-15

### Added
- **Monorepo consolidation** : merged the four previous
  `telemachus-*` GitHub repositories into a single repo with full
  history preservation (via `git filter-repo --to-subdirectory-filter`).
  - `telemachus-spec` → `spec/`
  - `telemachus-py` → `python-sdk/`
  - `telemachus-cli` → `python-cli/`
  - `telemachus-datasets` → `datasets/`
- Unified root README + CHANGELOG + LICENSE + CITATION.

### Notes
- No code or spec content was changed during the consolidation — only
  directory layout and history topology.
- See per-subdirectory CHANGELOGs for component-level history.

---

## Component changelogs

- [Spec changelog](spec/CHANGELOG.md) — RFCs and schema versioning
- [Python SDK changelog](python-sdk/CHANGELOG.md) *(if present)*
- [CLI changelog](python-cli/CHANGELOG.md) *(if present)*
- [Datasets changelog](datasets/CHANGELOG.md) *(if present)*
