# Changelog — Telemachus (monorepo)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

---

## [1.0.0a5] — 2026-08-17

### Fixed

- **A time column named `_ms` carried the source's resolution, not
  milliseconds.** Affects **1.0.0a1 through 1.0.0a4**, every alpha published so
  far. `ts_received_ms` came out of `csv_mapping` a thousand or a million times
  too large, with no error, no warning, and a value that is still a plausible
  integer:

  ```python
  df = csv_mapping.load(csv, mapping=m)     # ts_received_ms: {unit: iso8601}
  # 1.0.0a4 -> 1786960801000000    16 digits, microseconds
  # 1.0.0a5 -> 1786960801000       13 digits, milliseconds
  ```

  The defect was not a missing ×1000. `units.QUANTITY_BY_COLUMN` classes
  `ts_received_ms` as `time`, exactly like `ts`, so `convert()` routed it to the
  timestamp conversion and returned a datetime; `coerce_schema_dtypes` then cast
  that datetime to the int64 the schema declares, and published *whatever
  resolution the datetime happened to carry*. Nothing in that path ever read the
  suffix. So the column came back in the resolution of the **source**:

  | declared source unit | 1.0.0a4 | expected |
  |---|---|---|
  | `iso8601` | 1786960801000000 | 1786960801000 |
  | `epoch_s` | 1786960801 | " |
  | `epoch_ms` | 1786960801000 ✓ | " |
  | `epoch_us` | 1786960801000000 | " |
  | `epoch_ns` | 1786960801000000000 | " |

  `epoch_ms` was right by coincidence, which is the worst of the five: it is the
  case that makes the defect look absent. And the factor was not even constant
  across environments — the resolution `pd.to_datetime` chooses for ISO text is
  nanoseconds on pandas 2.1 and microseconds on pandas 3, so the same file
  converted on two machines was wrong by a million on one and by a thousand on
  the other.

  **The suffix is now read.** `EPOCH_UNIT_BY_SUFFIX` and `units.epoch_unit_of()`
  state the rule for any unit suffix — `_s`, `_ms`, `_us`, `_ns` — rather than
  special-casing the one column that exposed it, and `convert()` takes the
  target column so it can honour it. Adapters should call `convert_column()`,
  which cannot forget to pass it. The rule reads the *quantity* first and the
  suffix second, which is what keeps `gx_rad_s` an angular rate rather than an
  instant. The second door is closed too: `coerce_schema_dtypes` reduces a
  datetime reaching an integer epoch column at the resolution the name promises,
  instead of asking pandas for its own.

- **The validator now checks that an integer instant is at the resolution its
  name promises** (`check_epoch_columns`, rule 12c, error severity). The
  conversion above repairs what this library produces; this catches what arrived
  from somewhere else, which for a pivot format is most of the files it will ever
  see. The bounds are those of rule 12b and are not thresholds anyone chose: read
  as the name promises, the values must land between the start of GPS time and
  two days from now. Read at 13 digits a 2026 millisecond timestamp does; at 16
  it lands in the year 58 000, and the message then names the resolution that
  *would* be plausible and the divisor that fixes it.

  This half matters more than the first, because of how the defect surfaced. It
  was caught downstream only because the latency it produced came out at 1.78e12
  seconds, absurd enough to notice. At a factor of a thousand instead of a
  million the same defect yields a latency in hours: plausible, wrong, and
  nobody's bug report.

  Magnitude only. A datetime found in an integer column is a type question,
  which SPEC-01 §3 rule 9 owns, and reporting it here would say the same thing
  twice in the language of the wrong rule.

  The comparison is made on the integers, against bounds expressed in ticks,
  and never by decoding the values first. Decoding is the obvious
  implementation and it is a trap: 1.79e15 milliseconds is a date pandas cannot
  represent before version 3, so `to_datetime` answers `NaT`, every comparison
  against `NaT` is False, and the check reports a clean file. A guard that goes
  quiet on the *largest* errors is worse than no guard. It took running the
  suite at the dependency floor this package declares — pandas 2.1 — to see it,
  which is now part of the pre-flight rather than a matrix CI does not have.

- **No published dataset is affected, and nothing needs to be withdrawn.**
  Verified rather than assumed, on 2 631 Parquet files carrying a `ts_*_<unit>`
  column across the consuming pipeline's local and server stores: 2 603 non-empty,
  all 13 digits, none outside \[1980, today\] when read as milliseconds. The
  reason is structural and not luck — that pipeline fills `ts_received_ms`
  straight from a field already in milliseconds and never routes it through
  `convert()`. The defect only fires on the conversion path. The datasets this
  repository publishes carry no `ts_*_<unit>` column at all.

  A consumer pinned to `>=1.0.0a1` should reinstall after this release even
  though its data is intact, because rule 12c is new and its files must now pass
  it.

---

## [1.0.0a4] — 2026-08-16

### Added

- **`guards` in a CSV mapping, against a silent column shift.** A wrong unit is
  the failure this adapter's docstring already argues about. A wrong *position*
  is the same failure and worse: a wrong unit usually produces implausible
  values, which eventually get noticed, whereas a shifted column produces
  plausible values in plausible columns. Observed on a real headerless export —
  one field removed mid-file, `lat` reading 7.79 which is the longitude, and a
  speed of 133 km/h which is the heading. Nothing raised, and no range check
  helps, because 7.79 is a perfectly valid latitude.

  Positional addressing is what this adapter introduces in its own right: it is
  what lets someone map a headerless CSV without writing Python. The exposure
  comes with the feature, so the guard belongs here.

  ```yaml
  guards:
    expected_fields: 16          # at least N; a surplus must be empty
    always_empty: [5, 6, 11, 13] # fields empty in every extract so far
    range: {lat: [-90, 90]}      # per-target bounds
  ```

  `always_empty` is the one that earns its place. In the observed case the
  field count stayed correct and only the order moved, so counting fields saw
  nothing; what caught it was four columns, empty across every extract received
  since April, starting to carry values. That does not prove a shift, but it is
  the only signal that arrives before the numbers are wrong.

  A guard reports and does not refuse. A column may legitimately start being
  filled one day, and blocking a conversion on that would cost more than it
  saves. Findings reach the caller through `load(..., anomalies=[])`, the
  console through `tele convert`, and the manifest under `source.guards`, which
  records both what was declared and what it found.

  A caller who passes nothing still gets told: the findings are raised as a
  `GuardWarning` rather than dropped, and the manifest then records
  `findings: null`. An empty list there would read as "checked, nothing found"
  when it means "checked, result not kept", and a manifest that asserts a clean
  result it never saw is worse than one that admits it does not know.

  Checks run on the first 500 rows: a shift is structural, and re-reading a
  whole export for it would double the load time of a large source for nothing.
  A trailing separator — an export acquiring a 17th empty field without
  shifting anything — is tolerated rather than reported, because a guard that
  cries wolf is a guard someone switches off.

Fixed

- **`_suggest` crashed on a mapping addressed by index.** A headerless source
  names its columns by integer, `difflib` works on sequences, and the
  `TypeError` it raised replaced the clear "source has no such column" message
  with a traceback from inside the standard library. This happened in exactly
  the case where the message matters most: a positional mapping whose file just
  lost a field. There is no useful spelling suggestion for an index, so none is
  offered.

### Fixed

- **The speed cross-check raised a false alarm on any frame carrying more than
  one device.** It differences consecutive rows, and on a time-sorted
  multi-device export the rows interleave, so every step jumped between
  vehicles. Measured on two devices forty kilometres apart: the implied speed
  explodes, the median ratio collapses to `0.00x`, and a checker built to catch
  wrong units reports sound data as wrong. It now groups by `device_id`.

  Found by writing the generic test below rather than by a report, which is the
  argument for the test: this was the **fourth** occurrence of one pattern
  during 1.0, after a null key in `csv_mapping`, a constant key in `gpx`, and
  no key at all in `speed_from_pos`.

Added

- **A generic test for the entity-boundary invariant**
  (`test_entity_boundary_invariant.py`). Any function that differences two
  consecutive rows must say what it does when those rows belong to different
  devices — group by the entity, or state that it does not. The test
  interleaves two entities and requires each one's answer to match what it
  would have been alone, across the whole family at once rather than one
  function at a time.

  It carries a test of itself: a case that models the ungrouped form and fails
  if it does not produce an absurd result. A suite that cannot fail proves
  nothing.

- **`speed_mps` is conditional in the validator, not only in the text.**
  SPEC-01 §2.3.1 was written to say a receiver that measures no speed may omit
  the column. `MANDATORY_CORE` in `core/schemas.py` was never touched, so
  1.0.0a3 shipped a specification saying a column may be absent next to a
  validator that refused every file without it.

  Measured on the public Movebank corpus: 388 datasets converted through the
  shipped adapter, 274 of the 309 non-conformities caused by this single
  column, and **not one dataset changed status between 1.0.0a2 and 1.0.0a3**.
  The relaxation was announced and never applied.

  The cause was one list serving two purposes. `GNSS_MANDATORY_FIELDS` built
  both the arrow schema and the mandatory set, so a column could not belong to
  a profile without being required by it. Split into `GNSS_CORE_FIELDS`, which
  says what a `core` file may contain, and `CONDITIONAL_CORE`, which says what
  it need not.

Added

- **A test that the specification and the validator agree** (`tests/
  test_spec_matches_code.py`). It parses the tables of SPEC-01 §2.3 out of the
  markdown and compares them to `MANDATORY_BY_PROFILE`, treating a row marked
  conditional as not mandatory.

  This exists because the failure above survived two careful readings. The
  normative text was changed deliberately, reviewed, and four inconsistencies
  inside it were corrected — and nobody looked at the Python set the validator
  reads. A prose specification and a Python set are two encodings of one
  decision, and nothing tied them together.

  Deliberately narrow: it checks one table, the one whose disagreement with the
  code silently invalidates every conformance claim the project makes.

  It recognises a conditional row by the word "conditional" in its description
  cell, which is prose and therefore fragile: reword it and the parser would
  read every column as mandatory and pass by comparing everything to
  everything. So it carries canaries that fail when it stops measuring — one if
  a table parses as empty, one if no row is marked conditional any more. A test
  that can no longer fail has to say so.

  This is a stopgap. The durable fix is to restructure §2.3 so conditionality
  is a property of the table rather than of a sentence, and to key the
  invariant on that structure; this file is written to be replaced by it, not
  composed with.

- **A `heading_deg` column that never varies is no longer diagnosed as a
  convention** (SPEC-01 §2.5). One dataset of the reference campaign carries
  `-1` on every row. The previous release answered the convention question
  anyway — "this is course over ground on [-180, 180]... converts exactly with
  `heading_deg % 360`" — and a producer following that instruction turns a file
  whose heading is unknown *everywhere* into one pointing due north
  *everywhere*.

  The discriminant that failed was "negatives beside values above 180", which
  assumes the sentinel keeps company with real headings. Alone, it has no
  company, and the case fell through to the confident answer.

  A heading identifies its convention only by varying, so variance is now
  checked before convention is inferred, and a constant column gets a message
  that says what is known and stops. The rule is the variance and not the
  value: `-1` and `-999` are conventions of habit, and a column constant at
  `999` is diagnosed the same way. A stationary vehicle reporting a valid
  constant heading is untouched, because the check runs only on columns already
  outside [0, 360).

  This was a regression against 1.0.0a2, whose "out of range" was less useful
  and misled nobody. **A wrong message costs more than an absent one.**

- **A sentinel below -180 is named as one instead of reported as a span.** A
  signed column carrying `-999` has two defects and the previous message named
  neither, leaving the producer to discover that `% 360` — the fix the signed
  convention genuinely needs — silently turns `-999` into a heading of 81. Both
  defects are now stated in one message, so nobody is sent round twice. A
  column running to 32 515 is still reported by its scale: that is not a file
  with a few sentinels in it.

- **The closed interval [0, 360] is told apart from data out of any angular
  scale** (SPEC-01 §2.5). Twelve of the twenty-five heading datasets in the
  reference campaign write `360` for north — as few as 6 rows in 422 596. They
  were reported as "outside both the canonical range and the signed
  convention", which is technically true and misleading: 360 and 0 are the same
  bearing, and the source is not using another convention.

  The canonical range stays half-open and the finding stays an error, because
  north having one spelling is what spares every consumer a test for two, and a
  rule nothing verifies is the defect this project has just spent a release
  removing. What changes is that the message names the deviation, counts the
  rows, and states the one-line fix — including that `360 -> 0` is a
  canonicalisation and not a correction, so the source column needs no `_adj`
  (§2.13.1). Adapters SHOULD normalise at ingestion; the conformance check
  reports what reaches it unnormalised.

- **`speed_mps` moves out of the "All profiles" mandatory table into its own
  conditional one** (SPEC-01 §2.3). Version 1.0.0a3 relaxed the column in prose
  — §2.3.1 said plainly that it MAY be absent — while the table still listed it
  under **All profiles**, carrying the conditionality only in a note inside its
  Description cell. The implementation followed the table, and on the reference
  corpus the release changed nothing at all: the same 388 datasets converted,
  the same 273 refused for the absence of `speed_mps` alone, not one more than
  the version before it.

  What makes it worth recording is how it survived review. A human reads the
  note and concludes the matter is settled; a parser reads the structure and
  concludes the opposite; the code followed the structure. Two readers of the
  same table came away with different rules and both were reading correctly.
  The specification was not ambiguous to people — it was ambiguous *between*
  people and machines.

  §2.3.2 now states the constraint that follows: a column's obligation is
  expressed by the heading it sits under, never by prose inside a cell. A cell
  may explain; it may not qualify. That makes the section machine-comparable
  against the table the validator consults, so the two can be held to each
  other by a test instead of by attention.

- **The specification and the validator are now compared by a test.** Nothing
  compared them before, which is how they spent a release disagreeing while
  every test was green. The check reads §2.3 structurally — which table a row
  sits under, not a word inside a cell — and covers the conditional set as well
  as the mandatory ones, since dropping a column from `CONDITIONAL_CORE` leaves
  both mandatory sets untouched.

  Its canary is the part that matters. It does not assert that rows were found,
  which stays true while a parser silently ignores a table it does not
  recognise; it asserts that every table in §2.3 was accounted for. A table
  nobody reads is a rule nobody enforces.

  Not mechanised, and said plainly so it is not mistaken for mechanised: the
  prose of §2.3.1 can still drift from the table. What the restructuring buys
  is that the table is now the only structural statement of the rule, which is
  what makes a table-to-code check sufficient.

---

## [1.0.0a3] — 2026-08-16

### Added

- **`gpx` and `nmea` declare `column_provenance`** (SPEC-01 §2.3.1, §2.14).
  The rule shipped with the specification and no adapter applied it, so every
  converted dataset was of undetermined origin.

  A bare GPX has no speed field, so `speed_mps` is declared `absent` rather
  than left as a silent all-NaN column a consumer may read as a vehicle that
  never moved. NMEA declares it `measured`: the value is the receiver's own
  solution, independent of the position error, which is the property an
  analysis leans on when it selects stationary samples by speed and then
  measures position scatter. Both adapters inspect the file rather than assume
  a shape, so a GGA-only log declares `absent` and says why.

  Still to do: `aegis`, `pvs`, `stride` and `csv_mapping` declare nothing yet.

- **SPEC-01 §2.14 / SPEC-02 §3.15 — column provenance.** A dataset declares,
  per column, whether a value was `measured` by the sensor, `derived` by the
  adapter from other columns, or is `absent`. Declared in the manifest, not
  per row: provenance is a property of the acquisition chain, not of the
  sample.

  Motivation, from a real dataset: selecting stationary samples by a Doppler
  speed and then measuring position scatter yields the receiver noise. Doing
  the same with a position-derived speed is circular and returns a plausible
  number that means nothing. Nothing in a file distinguished the two cases.

  Complementary to §2.13, which excludes columns enriched from *external*
  sources. §2.14 covers columns computed from the dataset's own columns, which
  legitimately stay in the record and now say so.

- `column_provenance` in the manifest JSON Schema.

- **Column provenance in the four adapters that did not declare it** —
  `csv_mapping`, and the AEGIS, PVS and STRIDE dataset manifests. SPEC-01
  §2.14 defines the declaration; until now only `gpx` and `nmea` emitted it.

  `csv_mapping` derives it from the mapping: a column read from the file
  defaults to `measured`, a constant to `derived`, and a column the mapping
  does not name is stated `absent` rather than left to inference. The adapter
  cannot know whether the *source* computed a column before writing it — a
  fleet API that differentiates two positions and calls the result a speed
  produces a file no adapter can tell from a Doppler one — so a mapping may
  declare `provenance:` per column, next to its unit. An unknown value is
  refused.

- **AEGIS declares `speed_mps: derived`.** The adapter computes it by haversine
  on successive positions; the export carries no Doppler speed. It is a
  function of the position error, not an independent measurement, and an
  analysis that selects stationary samples by it is circular. Nothing said so
  before.

  Measured on the public Movebank corpus, 388 datasets converted through the
  shipped adapter: of the 110 that carry a `speed_mps`, the validator judges 47
  of them derived from their own positions — 43 %. Almost one declared speed in
  two is not a measurement.

- **Changelog fragments** (`changelog.d/`, `tools/changelog.py`). Branches drop
  one file per change instead of editing `CHANGELOG.md`, and the release folds
  them in. Two branches never touch the same path, so concurrent appends cannot
  interfere.

  The motivation is not the merge conflict, which git reports and a human
  resolves in seconds. It is the quieter failure observed on this repository:
  two branches each appended their own `### Fixed` and `### Added` under
  `[Unreleased]`, both merges succeeded, nothing was reported, and the section
  ended up with five subheadings for three categories. `release.yml` reads this
  file by regex and falls back silently, so a malformed section surfaces in
  published release notes rather than in CI.

- **`column_provenance` becomes an input to the validator, not just metadata**
  (SPEC-02 §3.15.1). The dispersion check of SPEC-03 §4.6 could already tell a
  measured speed from a computed one, and on its own it could only ever hedge:
  *tracks its positions exactly* has an innocent reading, since a constant speed
  on a straight road is indistinguishable from a derivation.

  Beside a declaration the same measurement becomes a check **on the
  declaration**. A column declared `measured` that tracks its own positions
  exactly is now an **error** — two sensors do not agree to that precision, so
  either the column was computed and the manifest is false, or it was measured
  and something overwrote it. A column declared `derived` is expected to agree,
  so the checker falls silent: declaring buys the quiet. A wrong unit still
  outranks everything, because km/h is km/h whatever its provenance.

  Also enforces the declaration itself: an unknown value, a column declared
  `absent` that carries values, and the `core`-profile warning SPEC-02 §3.15
  already asked for and nothing implemented.

### Changed

- **SPEC-01 §2.2 / §2.3.1 — `speed_mps` is now conditional in profile `core`.**
  A Doppler solution costs energy, and many low-power receivers emit position
  without ever emitting speed. The previous wording left such a device two ways
  out and both were bad: declare itself non-conformant, or fill the column by
  differentiating two positions. The second silently turns an independent
  measurement into a function of the position error.

- **`RowAccount(raw_rows_in=...)` now defaults to zero.** The common case is an
  adapter that counts as it reads and sets the field itself, so callers were
  writing `RowAccount(raw_rows_in=0)` purely to have it overwritten three lines
  later — noise at every call site, reported by two consumers independently.

  The default is safe rather than merely convenient: a zero left in place by
  mistake cannot pass unnoticed, because `finish()` refuses a tally where
  `rows_out + raw_rows_dropped` does not equal `raw_rows_in`. An adapter that
  forgets gets an error naming the discrepancy, not a manifest quietly claiming
  it read nothing. A test locks that property.

### Fixed

- **`gpx`: a repeated timestamp is judged per track, not per file.** The
  adapter fills `device_id` with the GPX `creator`, which names the software
  that wrote the file. Every track inside carries the same string, so the
  `[device_id, ts]` dedup key of `drop_duplicate_ts` collapsed to `ts` alone
  and two recordings sharing a second lost one of them. A `trkseg` is the unit
  of one recording, and it is now the unit the dedup keys on.

  Measured on the public OSM traces over Rouen, 167 files and 794 508 track
  points: **7 618 of 178 436 timestamped points were being destroyed**, and the
  row accounting counted them as `duplicate_ts`, which was exact in volume and
  wrong in reason. Same mechanism as the `csv_mapping` defect fixed in 1.0.0a2,
  reached by the other road: there the key was null, here it is constant, and a
  constant key is the same as no key at all.

  `load()` now states in its own docstring that `creator` names software rather
  than a receiver, since everything downstream defaults to grouping by
  `device_id`.

- **`gpx`: the manifest read the file instead of assuming it.** `ingestion` was
  hard-coded to `GPX 1.1` and reported that for a 1.0 file, which is a false
  provenance statement in the block whose job is provenance. The version now
  comes from the root attribute.

- **SPEC-01 — four leftovers from the wording that preceded §2.3.1.** Making
  `speed_mps` conditional changed one section and left four places still
  asserting the opposite, which is how an implementer ends up following the
  rule the specification no longer states:

  - the §2.7 note and its diagram both called `speed_mps` mandatory;
  - the diagram pointed at §2.2 for it, and at §2.6 for `speed_obd_mps`, which
    is Extended IMU Fields. The OBD section is §2.7;
  - validation rule 1 required every mandatory column of the declared profile,
    with no exception for a receiver that does not measure speed. A `core` file
    that §2.3.1 allows would have been rejected by the rule next to it;
  - §2.3.1 defined an all-NaN column as *absent*, then required a provenance
    declaration for a column that is *present*. Both sentences applied to the
    same column and gave opposite answers. An all-NaN column now declares
    `absent` explicitly, and §2.3.1 says outright that it raises the SHOULD of
    §2.14 to a MUST for this column.

- **20 stale cross-references in `docs/`.** The April consolidation moved
  SPEC-01's column definitions from §3 to §2 and the documentation was never
  followed through, so ten pages pointed readers at sections that had held
  something else for four months. Every reference was re-read against the
  current text rather than remapped by arithmetic, because the right target
  depends on what each sentence claims:

  - mandatory columns: §3.1 → §2.3, but *`device_id` and `trip_id` are
    declared*: §3.1 → §2.4. Same old number, two different destinations
  - the AccPeriod default: §3.6 → §2.12
  - the CarrierState decision tree: SPEC-01 §3.7 → **SPEC-02** §3.8. A
    different document, not a different number
  - the multi-rate convention: §3.5 → §2.11
  - gyro absent-or-all-NaN: §3.3 → §2.6, which carries the sentence about
    never zero-filling. Validation rule 10 only covers the partial group
  - enriched and events-layer contracts: §4 → §2.13. §4 is Hardware Mapping
  - column names and units: §3 → §2 and §5. §3 defines neither
  - the columns a signal parquet may hold: §3 → §2

  The four surviving bare `§3` and `§4` references are correct and were left
  alone: they do point at Validation Rules and Hardware Mapping.

- **`decimation_loss` reported a negative loss on a varying cadence.** It kept
  the samples whose timestamp was a multiple of the step, then summed only the
  pairs exactly `step` apart. Both filters select a *different subset of the
  trace for each step*, so the steps did not measure the same ground and their
  totals were never comparable. Down-sampling appeared to lengthen the path.

  Measured on the public OSM traces over Rouen, where the dominant cadence
  covers only 62 % of samples: decimating to 2 s reported 840 km against
  764 km native, a **loss of -9.9 %**, and the native step itself reported
  764 km where `path_length_m` reported 2 846 km on the same frame.

  The contiguity split is now computed **once, on the native signal**, and
  every step decimates inside those same stretches, keeping the last sample of
  each so the path is not shortened by truncating its end. The reference is the
  native path rather than the first step, so each row answers one question:
  what fraction of the travelled distance survives this cadence. On the same
  corpus the losses are now 0.13 %, 0.58 %, 1.39 %, 4.11 % and 7.30 % at 2, 5,
  10, 30 and 60 s, and the native step agrees with `path_length_m` to the
  metre.

  `max_gap_s` is now accepted, as on `path_length_m`, so a real hole is not
  crossed by a chord.

- **`speed_from_pos` differenced across entity boundaries.** It had no `by=`
  parameter, unlike `stops` and `path_length_m`, so on a frame sorted by
  `(device_id, ts)` it also computed a speed between one device's last fix and
  the next device's first. At that row time runs backwards, `dt` is negative,
  and the speed comes out **signed**: values from -81 to +204 m/s were measured
  on a 120-badge export.

  A threshold applied to a quantity assumed positive then reports either every
  row as a stop or none of them, depending on which way the comparison runs.
  The first measurement on that export returned zero stops, which was absurd
  enough to be noticed. With less extreme values it would have been plausible
  and wrong.

  `by=` now defaults to `device_id`, and each entity starts at NaN rather than
  only the first row of the frame — the old `v[0] = nan` left every later
  boundary carrying a wrong value even when the caller grouped upstream.
  `compute_dt` takes a Series and cannot group, which its docstring now says.

  Neither function had a test. They have seven.

  Same family as the `csv_mapping` defect of 1.0.0a2 and the `gpx` one that
  followed: a function mixing entities in silence. There the dedup key was null
  or constant; here the function could not group at all.

- **A heading on [-180, 180] is now diagnosed as a convention, not reported as
  corrupt data** (SPEC-01 §2.5). Movebank and many receivers use the signed
  range; this format requires [0, 360). Twenty-five public datasets fail on it,
  and the validator said only `heading_deg out of range [0, 360)` — which sends
  a producer hunting for bad data when `% 360` converts exactly.

  It needs no declaration, where a unit does, and the asymmetry is the point: a
  speed of `50` does not say whether it is m/s or km/h, but a negative heading
  can only be the signed convention, and where nothing is negative the two
  conventions give identical numbers. The convention is self-evident in exactly
  the case where it matters.

  One negative sign has three readings and **only one may be normalised**. A
  file whose headings reach 350 and also carry a few `-1` is not signed — it is
  using `-1` for "unknown", and `% 360` would turn every one into 359, due
  north. A signed column never exceeds 180, which is what tells them apart. The
  validator now names which of the three it is seeing.

  `unit: deg_signed` is available for a producer who prefers to be explicit.

---

## [1.0.0a2] — 2026-08-16

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

## [Monorepo consolidation] — 2026-04-15

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
