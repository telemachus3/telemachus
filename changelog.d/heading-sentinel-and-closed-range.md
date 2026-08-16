Fixed

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
