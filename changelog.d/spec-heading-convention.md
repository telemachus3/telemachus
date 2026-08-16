Fixed

- **A heading on [-180, 180] is now diagnosed as a convention, not reported as
  corrupt data** (SPEC-01 §2.5). Movebank and many receivers use the signed
  range; this format requires [0, 360). Twenty-five public datasets fail on it,
  and the validator said only `heading_deg out of range [0, 360)` — which sends
  a producer hunting for bad data when `% 360` converts exactly.

  It needs no declaration, where a unit does, and the asymmetry is the point: a
  speed of `50` does not say whether it is m/s or km/h, but a negative heading
  can only be the signed convention, and where nothing is negative the two
  conventions give identical numbers. The convention is self-evident in exactly
  the case where it matters.

  One negative sign has three readings and **only one may be normalised**. A
  file whose headings reach 350 and also carry a few `-1` is not signed — it is
  using `-1` for "unknown", and `% 360` would turn every one into 359, due
  north. A signed column never exceeds 180, which is what tells them apart. The
  validator now names which of the three it is seeing.

  `unit: deg_signed` is available for a producer who prefers to be explicit.
