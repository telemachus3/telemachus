Fixed

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
