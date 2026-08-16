Fixed

- **20 stale cross-references in `docs/`.** The April consolidation moved
  SPEC-01's column definitions from §3 to §2 and the documentation was never
  followed through, so ten pages pointed readers at sections that had held
  something else for four months. Every reference was re-read against the
  current text rather than remapped by arithmetic, because the right target
  depends on what each sentence claims:

  - mandatory columns: §3.1 → §2.3, but *`device_id` and `trip_id` are
    declared*: §3.1 → §2.4. Same old number, two different destinations
  - the AccPeriod default: §3.6 → §2.12
  - the CarrierState decision tree: SPEC-01 §3.7 → **SPEC-02** §3.8. A
    different document, not a different number
  - the multi-rate convention: §3.5 → §2.11
  - gyro absent-or-all-NaN: §3.3 → §2.6, which carries the sentence about
    never zero-filling. Validation rule 10 only covers the partial group
  - enriched and events-layer contracts: §4 → §2.13. §4 is Hardware Mapping
  - column names and units: §3 → §2 and §5. §3 defines neither
  - the columns a signal parquet may hold: §3 → §2

  The four surviving bare `§3` and `§4` references are correct and were left
  alone: they do point at Validation Rules and Hardware Mapping.
