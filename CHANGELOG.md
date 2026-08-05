# Changelog — Telemachus (monorepo)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-08-05

### Added
- **`telemachus.metrics.sampling`** — sampling-cadence metrics, for streams whose
  effective rate differs from the documented one, or which reach a consumer
  already decimated:
  - `gap_profile` — the cadence actually present, counted on gaps;
  - `sampling_populations` — dominant cadence per device, with a `min_gaps`
    guard: below it an entity is flagged `enough=False` rather than credited
    with a rate, which is what stops short observation windows from
    manufacturing populations that do not exist;
  - `decimation_loss` — travelled distance retained per down-sampling step,
    summing strictly contiguous segments only so the curve stays monotonic;
  - `stops` — stop detection by minimum still-duration, designed to be run at
    several cadences to measure what down-sampling destroys;
  - `session_contiguity` — whether packets, bursts or files of a feed abut or
    only cover isolated windows;
  - `path_length_m`, `epoch_s` — supporting primitives.
- 15 tests covering these, including timestamp-resolution independence
  (`ns`/`us`/`s`, tz-aware and naive) and monotonicity of decimation loss.

### Notes
- `epoch_s` exists because dividing a raw int64 timestamp view by a hard-coded
  constant is resolution-dependent: query engines commonly return `us` where
  pandas returns `ns`, and the failure is silent — decimation keeps almost
  nothing and losses read as 100 %.

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
