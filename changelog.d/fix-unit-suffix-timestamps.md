Fixed

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
