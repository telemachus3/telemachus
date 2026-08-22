Added

- **`analysis.phase_profile`: whether a cadence follows a clock or an interval.**
  Two feeds that both report "every two minutes" differ on whether devices are
  sampled at the same instants. Under an interval rule they never are, so
  anything comparing vehicles to each other has to interpolate — a constraint
  worth finding before the schema is written, not after.
