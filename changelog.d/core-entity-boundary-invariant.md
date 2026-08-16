Fixed

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
