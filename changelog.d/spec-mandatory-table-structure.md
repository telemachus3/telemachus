Fixed

- **`speed_mps` moves out of the "All profiles" mandatory table into its own
  conditional one** (SPEC-01 §2.3). Version 1.0.0a3 relaxed the column in prose
  — §2.3.1 said plainly that it MAY be absent — while the table still listed it
  under **All profiles**, carrying the conditionality only in a note inside its
  Description cell. The implementation followed the table, and on the reference
  corpus the release changed nothing at all: the same 388 datasets converted,
  the same 273 refused for the absence of `speed_mps` alone, not one more than
  the version before it.

  What makes it worth recording is how it survived review. A human reads the
  note and concludes the matter is settled; a parser reads the structure and
  concludes the opposite; the code followed the structure. Two readers of the
  same table came away with different rules and both were reading correctly.
  The specification was not ambiguous to people — it was ambiguous *between*
  people and machines.

  §2.3.2 now states the constraint that follows: a column's obligation is
  expressed by the heading it sits under, never by prose inside a cell. A cell
  may explain; it may not qualify. That makes the section machine-comparable
  against the table the validator consults, so the two can be held to each
  other by a test instead of by attention.

- **The specification and the validator are now compared by a test.** Nothing
  compared them before, which is how they spent a release disagreeing while
  every test was green. The check reads §2.3 structurally — which table a row
  sits under, not a word inside a cell — and covers the conditional set as well
  as the mandatory ones, since dropping a column from `CONDITIONAL_CORE` leaves
  both mandatory sets untouched.

  Its canary is the part that matters. It does not assert that rows were found,
  which stays true while a parser silently ignores a table it does not
  recognise; it asserts that every table in §2.3 was accounted for. A table
  nobody reads is a rule nobody enforces.

  Not mechanised, and said plainly so it is not mistaken for mechanised: the
  prose of §2.3.1 can still drift from the table. What the restructuring buys
  is that the table is now the only structural statement of the rule, which is
  what makes a table-to-code check sufficient.
