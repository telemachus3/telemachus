Added

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
