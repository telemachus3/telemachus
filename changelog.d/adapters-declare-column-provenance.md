Added

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
