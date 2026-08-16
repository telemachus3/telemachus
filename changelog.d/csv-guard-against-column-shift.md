Added

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
