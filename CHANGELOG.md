# Changelog — Telemachus (monorepo)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Fixed

- **`csv_mapping`: `device_id` and `trip_id` can name a column.** A source that
  holds several entities in one file names the entity in a column, not in the
  mapping. Any fleet export has that shape, and so does every Movebank export:
  one file, thirty animals, one column telling them apart.

  The mapping form `device_id: {column: ...}` was accepted and then written to
  the frame as the dict itself, which the dtype coercion turned into an
  all-null column. That was worse than a refusal, because the column existed,
  so `drop_duplicate_ts` keyed on it — and a null key is the same as no key at
  all, which is a global dedup on `ts`.

  Measured on a real export: 1 269 952 rows in, 459 243 out, 810 709 counted as
  `duplicate_ts`, one animal surviving out of thirty. Validation reported PASS
  with no warning; the row accounting of SPEC-02 §3.5.1 did record the loss.

  Declaring `device_id` under `columns:` always worked. The two spellings now
  behave the same, and a `{column: ...}` naming a column the source does not
  have raises `MappingError` instead of passing silently.

## [1.0.0a1] — 2026-08-15

First stable-numbered release, published as a pre-release: `pip` does not
install it by default, which puts the import break below out in the open before
the stability commitment of SPEC-04 §2.2 binds.

The major number is not justified by a count of features. Until now SPEC-02
§3.5 required a row accounting the reference implementation did not produce,
and SPEC-04 asserted a perimeter that had never been written down. **1.0 is the
end of that gap**, not an addition to it — no convenience function was added to
pad the milestone.

### Added

- **Format adapters** — the three that shipped before target one named research
  dataset each, which helps reproduce a result and does not help anyone convert
  what they already have.
  - `adapters.csv_mapping` — any CSV, driven by a **declarative mapping**
    (SPEC-03 §3.0.1). Column and unit are declared as data, and **`unit` is
    required on every column that carries one**, including when the source is
    already canonical. This is what kills the wrong-unit class of bug at the
    source rather than warning about it afterwards: the question is asked at the
    moment the column is named, in front of the source's documentation. Errors
    name the closest standard column and list the file's own headers.
  - `adapters.gpx` — GPX 1.0/1.1. Track segments become trips. `speed_mps` is
    present and NaN: GPX has no speed field, and deriving one would put a
    computed value in a measurement column (SPEC-04 §5.2).
  - `adapters.nmea` — NMEA 0183 RMC/GGA/VTG, merged into one row per fix epoch,
    with checksum verification. A log with GGA and no RMC is refused unless the
    caller supplies a date, rather than being dated by guess.
  - `tele mapping-template <file.csv>` prints a skeleton listing the source's
    own columns, with the units left blank. It does not guess the mapping: a
    guess would be right often enough to be trusted and wrong often enough to
    matter, and the unit cannot be guessed at all.
- **Row accounting** (`RowAccount`, `check_row_accounting`, `drop_duplicate_ts`)
  — SPEC-02 §3.5, which the specification had required since 0.8 and no code
  produced. A validator only ever sees the output file, so this block is its
  only evidence about what an adapter discarded on the way in. It must balance
  (`rows_out + raw_rows_dropped == raw_rows_in`), its reasons must sum, and
  `gnss_valid_false` is **refused by name** as a drop reason (SPEC-01 §2.5).
  `tele convert` fills it in and prints it.
- **Personal data** (`check_pii`, `strip_pii`, SPEC-01 §2.4) — a dataset carrying
  a live IMEI and SIM serial passed `--level strict` in silence. The columns are
  defined by the format and rightly so, but SPEC-04 §5.1 restricts them at
  publication and nothing enforced it. They are now reported at every level, and
  refused outright once the manifest declares the dataset is going out — an open
  licence, an open source type, a DOI. The advice is to drop the column, not to
  hash it: a hashed IMEI is still a per-device identifier and still joins.
- **Unit plausibility** (`check_units`, SPEC-03 §4.6) — run inside `validate()`.
  A cross-check against the speed the positions imply names the wrong unit from
  its ratio (3.6 km/h, 1.94 knots, 2.24 mph) and is an error; magnitude checks
  on gyroscope, magnetometer and altitude warn. The accelerometer check is
  frame-aware and, with no AccPeriod declared, says so instead of guessing —
  a median |a| of 1.0 m/s² is both a raw signal left in g and a correct
  compensated frame. The speed cross-check likewise refuses to report a pass it
  has no grounds to give: a `speed_mps` derived from the positions it is about
  to be compared against agrees with them exactly, and the validator says it
  cannot verify the column rather than falling silent. A wrong unit is still
  named whatever the provenance.
- **`merge_multirate`** (SPEC-01 §2.11) — promoted from a pattern rewritten by
  hand in 42 files across the projects consuming this format, of which one
  handled the case that matters. A GNSS fix falling in a hole in the
  accelerometer stream has no row to attach to and vanishes from a file that
  still validates; the merge is over the **union** of both time axes, so orphan
  fixes come back as rows of their own with the accelerometer columns NaN. On a
  dense stream the result is identical to the naive join.
  `tolerance_ms` is **required, with no default**: the right value is a property
  of the hardware, and a library-wide default would encode one deployment's
  field knowledge as everyone's.
- `core.units` — SPEC-01 §5 as an executable table, with exact constants
  (`9.80665`, never `9.81`) and naive timestamps read as UTC.
- **`carrier_profile`** (SPEC-02 §3.8) — the manifest was the one part of the
  format that was not neutral about what carries the device. Position,
  accelerometer, AccPeriods and the multi-rate convention all pass unchanged
  onto a collar or a bicycle; the five-state vehicle taxonomy, whose detection
  tree tests a battery voltage, did not. One level of indirection fixes it, and
  **the invariant is the declaration, not the vocabulary**: every profile must
  say which of its states an analysis may use (`analysable` / `optional` /
  `excluded`). `vehicle` is registered with exactly the states and meanings it
  already had and is the default, so an existing manifest is unchanged and keeps
  validating. **No animal, pedestrian or bicycle profile is registered** — the
  mechanism is what 1.0 owes, a profile ships when a dataset carries one.
- **`acquisition_breaks`** (SPEC-02 §3.9) — the third leg of the acquisition
  context, alongside the accelerometer frame and the carrier. A file with no
  rows between two instants is ambiguous, and the readings are incompatible:
  parked underground, device rebooted, network dropped and the frames arrive
  three days later, GNSS lost fix while the IMU kept running. Every consumer
  guesses, and they guess differently. `late_delivery` is a kind of its own
  rather than a `data_gap`, because a gap is final and a late delivery is
  transient — treating the second as the first diagnoses a delivery delay as
  data loss. `data_gap` is the one claim the data can contradict, and `full`
  validation checks it.
- **Corrections** (SPEC-01 §2.13.1, SPEC-02 §3.14) — nothing previously stopped
  a producer with a better `lat` from writing it into `lat`, after which the
  measurement is gone. Correcting is legitimate, destroying is not: the source
  column keeps its values, the corrected one goes in `<column>_adj`, its
  uncertainty in `<column>_sigma`, and the producer is declared once per column
  in the manifest rather than repeated on every row. The invariant is
  mechanically checkable and `strip_corrections` performs it: **removing every
  declared `_adj` and `_sigma` column leaves exactly the source file**.
  `produced_by` is an opaque string this specification never interprets, so a
  pipeline can publish corrected data in an open format without publishing how
  it corrects.
- `core.schemas.coerce_schema_dtypes` — SPEC-01 §3 rule 9 applies to *every*
  present column, not only the mandatory ones.

### Changed — licensing

- **The Python SDK and CLI move from AGPL-3.0-only to Apache-2.0.** The
  specification, schemas and documentation stay MIT; datasets keep their
  per-file licences.

  A format's reference implementation is how everyone reads and writes the
  format. Copyleft on it taxes the one thing the project is trying to spread,
  and it protects nothing valuable: the value is in the format being adopted
  and in the reconstruction engines above it, not in the I/O layer. Lossless
  audio settled this two decades ago — its reference library went permissive
  so that closed players could read the format, and the format won because of
  it.

  It also removed a contradiction inside 1.0 itself. SPEC-04 §5.2.1 and the
  `corrections` block are built so a proprietary pipeline can publish in an
  open format while its methods stay its own; under AGPL, using the SDK to
  write that file would have pulled the pipeline into the licence. The door was
  specified and locked at the same time.

  Apache-2.0 rather than MIT for the code: it grants a patent licence over what
  is in the SDK and terminates it for anyone who sues over patents, which is
  what lets a legal department approve it without a review cycle. Nothing is
  granted about methods that are not in the SDK. The specification stays MIT —
  silent on patents — and by construction describes no reconstruction method,
  since §5.2.1 keeps them out of scope.

### Changed — breaking

- **The library is in two tiers, and the tier is in the import path**
  (SPEC-04 §5.3). `telemachus.metrics` is normative: everything in it fills a
  manifest field or serves a validation rule, and it moves with the spec.
  `telemachus.analysis` is the convenience tier: maintained, outside the
  specified perimeter, free to evolve. Moved there: `by_gap`, `by_stop`,
  `segment_trips`, `trip_profile`, `TripSegmenter`, `stops`, `decimation_loss`,
  `session_profile`, `session_contiguity`, `stream_summary`, `compute_dt`,
  `speed_from_pos`. Importing a moved name from `telemachus.metrics` raises an
  `AttributeError` naming the new import.
- `speed_from_pos` reads `ts`/`lat`/`lon` (SPEC-01 names) instead of a
  hard-coded `timestamp` column, which no conformant file has.
- `tele validate` runs the **current** validator. It ran the v0.1 one, and on
  the four datasets this project publishes it reported seven schema errors, all
  of them defects in the validator. The old path survives behind `--legacy`.
  It also now accepts a directory, a manifest or a parquet file, with `--level`.

### Fixed

- `validate_manifest` rejected all four published datasets. Every cause was in
  the validator, not the data: `dataset_id` forced lowercase where SPEC-02 §3.2
  specifies an ISO 3166-1 alpha-2 prefix (uppercase); unquoted YAML timestamps
  arriving as `datetime` objects against `type: string`; a field explicitly set
  to `null` treated as a type error rather than as "declared, does not apply";
  `data_files[].format` restricted to a narrower enum than the spec.
- `frame: partial` no longer requires `residual_g`. SPEC-02 §5 rule 4 calls it
  OPTIONAL — an off-board descriptive hint, never a conformance target — and
  the implementation contradicted its own specification. It is now a warning.
- `validate_manifest` now enforces SPEC-02 §5.1, which requires
  `schema_version` and `source` and which nothing checked.
- Removed `telemachus.dataset`, which shipped in 0.9 importing a module that
  does not exist and raised `ModuleNotFoundError` on import.

### Deprecated

- Eleven modules implementing the superseded v0.1 three-table schema
  (`trajectory`/`imu`/`events` keyed on `timestamp_ns`): `io`, `io_import`,
  `io_export`, `models`, `core.models`, `core.dataset`, `core.semantics`,
  `core.validate_tables`, `pandas.*`, `_validate_legacy`, and the legacy schema
  aliases in `core.schemas`. Kept for the one minor release SPEC-04 §2.2
  promises, scheduled for removal in 1.1. No new work targets them.

### Specification

SPEC-01, SPEC-02, SPEC-03 and SPEC-04 move to **1.0**.

- SPEC-01 §2.11 states the **completeness rule**: the row set is the union of
  the sensor time axes, and every native measurement has a row.
- SPEC-01 §5 states that units are declared, not inferred, and that constants
  are exact.
- SPEC-02 §3.5.1 makes the row accounting normative, with the balance identity
  and the forbidden reasons. §5 gains rules 8 and 9.
- SPEC-03 §3.0 specifies the three format adapters; §4.6 specifies unit
  plausibility.
- SPEC-04 §5.2.1 fixes where the IP boundary falls, layer by layer: **D0 and
  D0.5 are specified in full, D1 and above are not** — except the coexistence
  contract for corrected values, which says a correction must sit beside its
  source and be removable, and nothing about what a reconstruction contains or
  how it is obtained. D0.5 is in because it states what happened to the
  *instrument*, which is unrecoverable after the fact and meaningless to
  compute; D1 is out because every value in it is an estimator's output, and
  publishing its column schema would publish the shape of the estimator.
- SPEC-04 §5.3 writes the scope rule, with the inventory of the 0.9 surface it
  was tested against before publication.
- A release test refuses any public docstring or published SPEC that names a
  private module, repository, method or internal document.

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
