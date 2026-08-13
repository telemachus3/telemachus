# Changelog — Telemachus (monorepo)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.9] — 2026-08-13

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
  - `session_profile` — size and duration of each delivery unit, which tells
    whether a sample cap or a time window shapes the feed;
  - `path_length_m`, `epoch_s` — supporting primitives.
- **`telemachus.metrics.trips`** — trip reconstruction, pluggable. Cutting a
  stream into trips is a decision, not a property of the data, and nearly
  everything downstream is priced per trip:
  - `by_gap` — cut where the stream goes silent (a transport property);
  - `by_stop` — cut where the vehicle stands still (usually what an operator
    means by a trip);
  - `TripSegmenter` protocol — any conforming callable can be passed to
    `segment_trips`, so domain-specific logic drops in without a fork. Neither
    built-in attempts to *qualify* a stop; that needs more than a threshold;
  - `trip_profile` — per-trip samples, duration, distance, stationary share.
- **`telemachus.metrics.describe.stream_summary`** — one-call characterisation
  of an unfamiliar feed: volume, coverage, cadence, trip count with its
  threshold, motion, travelled distance, geographic extent, positioning
  quality. Absent measurements are `NaN` rather than omitted, so summaries of
  different streams stay comparable.
- 34 tests covering these, including timestamp-resolution independence
  (`ns`/`us`/`s`, tz-aware and naive), monotonicity of decimation loss, the
  index-alignment contract of segmenters on out-of-order frames, and the
  divergence between `by_gap` and `by_stop` on a parked but still-reporting
  vehicle.

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
