Fixed

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
