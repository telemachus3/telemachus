Fixed

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
