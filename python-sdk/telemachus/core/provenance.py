"""Column provenance — was this value measured, or did the adapter compute it?

`speed_mps` from a Doppler solution and `speed_mps` differentiated from two
positions carry the same name and are not the same quantity. The first is
independent of the position error; the second is made entirely of it. An
analysis that selects standstill instants by Doppler is sound precisely because
Doppler does not come from the positions; the same analysis on a derived column
is circular, and wrong in silence.

SPEC-02 §3.15 defines the declaration. This module reads it, and — more
usefully — hands it to the plausibility checks, which until now could only
*guess*.

**Why the pairing is worth more than either half.** The guess works by
dispersion: a real Doppler reading disagrees with its own positions sample by
sample, a derived column cannot. But the guess can only ever warn, because
"tracks its positions exactly" has an innocent explanation — a constant speed
on a straight road looks identical to a derivation. So on its own the heuristic
must hedge.

Put a declaration beside it and the same measurement becomes a **cross-check on
the declaration**:

===================  ==========================  ==========================
Declared             Dispersion says             Verdict
===================  ==========================  ==========================
``measured``         independent                 nothing to say
``measured``         tracks its own positions    **error** — one of the two is
                                                 false, and either way the
                                                 dataset is not what it claims
``derived``          tracks its own positions    silent: expected, and the
                                                 cross-check simply cannot run
``derived``          independent                 silent: derived from another
                                                 source, which is legitimate
``absent``           the column carries values   **error** — declared absent
not declared         tracks its own positions    warning, and ask for the
                                                 declaration
===================  ==========================  ==========================

Declaring is therefore rewarded — it removes the hedging — and misdeclaring is
caught. That asymmetry is the whole point: a field nobody fills is a field that
does not exist.
"""

from __future__ import annotations

import pandas as pd

__all__ = [
    "PROVENANCE_VALUES",
    "check_provenance_declaration",
    "resolve_column_provenance",
]

#: SPEC-02 §3.15.
PROVENANCE_VALUES = ("measured", "derived", "absent")

#: Columns an adapter commonly computes, and whose origin therefore has to be
#: stated. `lat` and `lon` are always measured; nobody needs to say so.
AMBIGUOUS_COLUMNS = ("speed_mps", "heading_deg")


def resolve_column_provenance(manifest: dict | None) -> dict[str, str]:
    """Read `column_provenance` from a manifest, lowercased and validated.

    Unknown values are dropped rather than raising: a consumer reading a
    dataset produced against a later revision should ignore what it does not
    understand, not refuse the file. :func:`check_provenance_declaration` is
    what reports them, and it is the validator that calls it.
    """
    declared = (manifest or {}).get("column_provenance") or {}
    if not isinstance(declared, dict):
        return {}
    return {str(k): str(v).strip().lower() for k, v in declared.items()
            if str(v).strip().lower() in PROVENANCE_VALUES}


def check_provenance_declaration(manifest: dict | None,
                                 df: pd.DataFrame | None = None,
                                 *, profile: str | None = None
                                 ) -> tuple[list[str], list[str]]:
    """Check the declaration itself, before anything is inferred from the data.

    Returns ``(errors, warnings)``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    raw = (manifest or {}).get("column_provenance")
    if raw is not None and not isinstance(raw, dict):
        return ["column_provenance must be a mapping of column to "
                f"{list(PROVENANCE_VALUES)}"], []

    declared_raw = raw or {}
    bad = {k: v for k, v in declared_raw.items()
           if str(v).strip().lower() not in PROVENANCE_VALUES}
    if bad:
        errors.append(
            f"column_provenance: {bad} — each value must be one of "
            f"{list(PROVENANCE_VALUES)} (SPEC-02 §3.15)")

    if df is None:
        return errors, warnings

    declared = resolve_column_provenance(manifest)
    columns = set(df.columns)

    for column, origin in declared.items():
        if origin == "absent":
            # `absent` is a statement about the sensor, not about the file. A
            # column present and empty is consistent with it; a column carrying
            # values is not.
            if column in columns and df[column].notna().any():
                n = int(df[column].notna().sum())
                errors.append(
                    f"column_provenance declares {column!r} absent, but the "
                    f"column carries {n} value(s). Either the sensor exists and "
                    f"the declaration is stale, or the values were invented")
        elif column not in columns:
            warnings.append(
                f"column_provenance declares {column!r} as {origin!r}, but the "
                f"column is not in the data")

    # SPEC-02 §3.15: the one case the specification asks a validator to raise.
    if profile == "core":
        for column in AMBIGUOUS_COLUMNS:
            if column in columns and df[column].notna().any() \
                    and column not in declared:
                warnings.append(
                    f"{column} carries values and its provenance is not "
                    f"declared. Adapters commonly compute it, and a computed "
                    f"value that passes for a measurement is the defect this "
                    f"format is least able to survive (SPEC-02 §3.15)")

    return errors, warnings
