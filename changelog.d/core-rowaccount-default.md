Changed

- **`RowAccount(raw_rows_in=...)` now defaults to zero.** The common case is an
  adapter that counts as it reads and sets the field itself, so callers were
  writing `RowAccount(raw_rows_in=0)` purely to have it overwritten three lines
  later — noise at every call site, reported by two consumers independently.

  The default is safe rather than merely convenient: a zero left in place by
  mistake cannot pass unnoticed, because `finish()` refuses a tally where
  `rows_out + raw_rows_dropped` does not equal `raw_rows_in`. An adapter that
  forgets gets an error naming the discrepancy, not a manifest quietly claiming
  it read nothing. A test locks that property.
