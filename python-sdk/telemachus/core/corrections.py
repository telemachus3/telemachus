"""Corrections — a corrected value coexisting with the measurement it corrects.

Correcting is legitimate. Destroying is not.

Nothing in the format previously stopped a producer with a better value for
`lat` from writing it into `lat`. Once they have, the measurement is gone, and
no later algorithm recovers it — which is the one loss this format exists to
prevent. SPEC-01 §2.13.1 states the convention that removes the temptation: the
source column keeps its measured values, the corrected value lives in
`<column>_adj`, its uncertainty in `<column>_sigma`, and the producer is
declared once in the manifest rather than repeated on every row.

The invariant is mechanically checkable, and that is the whole point of writing
it this way: **removing every declared `_adj` and `_sigma` column leaves exactly
the source file.** A format that claims to be lossless and cannot demonstrate it
is making a promise, not a guarantee. :func:`strip_corrections` performs the
removal and :func:`check_corrections` verifies the declaration.

Nothing here concerns *how* a corrected value is obtained. That is out of scope
by SPEC-04 §5.2, and the convention is built so a producer can ship corrected
data in an open format while its method stays its own: `produced_by` is an
opaque string this library never interprets.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

__all__ = [
    "ADJUSTED_SUFFIX",
    "UNCERTAINTY_SUFFIX",
    "Correction",
    "check_corrections",
    "resolve_corrections",
    "strip_corrections",
]

#: Reserved suffixes on standard column names (SPEC-01 §2.13.1). Not vendor
#: extras: their relationship to the source column is exactly what a consumer
#: relies on, so they do not take the `x_` prefix.
ADJUSTED_SUFFIX = "_adj"
UNCERTAINTY_SUFFIX = "_sigma"


@dataclass(frozen=True)
class Correction:
    """One declared correction: a source column and what was derived from it."""

    column: str
    adjusted: str
    uncertainty: str | None = None
    produced_by: str | None = None
    notes: str | None = None

    @property
    def derived_columns(self) -> tuple[str, ...]:
        return (self.adjusted,) + ((self.uncertainty,) if self.uncertainty else ())


def resolve_corrections(manifest: dict | None) -> list[Correction]:
    """Read the `corrections` block of a manifest (SPEC-02 §3.14)."""
    entries = (manifest or {}).get("corrections") or []
    if not isinstance(entries, list):
        raise ValueError("corrections must be a list")

    out: list[Correction] = []
    for i, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ValueError(f"corrections[{i}] must be a mapping")
        column, adjusted = raw.get("column"), raw.get("adjusted")
        if not column or not adjusted:
            raise ValueError(
                f"corrections[{i}] needs both 'column' (the source, kept "
                f"unmodified) and 'adjusted' (the corrected value)")
        out.append(Correction(
            column=str(column), adjusted=str(adjusted),
            uncertainty=(str(raw["uncertainty"]) if raw.get("uncertainty") else None),
            produced_by=raw.get("produced_by"), notes=raw.get("notes")))
    return out


def strip_corrections(df: pd.DataFrame, manifest: dict | None = None) -> pd.DataFrame:
    """Return the frame with every corrected column removed.

    With a manifest, removes exactly what it declares. Without one, falls back
    to the reserved suffixes, which is what a consumer holding only a parquet
    file can do.

    This is the operation SPEC-01 §2.13.1 defines losslessness against: what
    comes back is the measurement, and it must be the measurement unchanged.
    """
    if manifest is not None:
        derived = {c for corr in resolve_corrections(manifest)
                   for c in corr.derived_columns}
    else:
        derived = {c for c in df.columns
                   if c.endswith((ADJUSTED_SUFFIX, UNCERTAINTY_SUFFIX))}
    return df.drop(columns=[c for c in derived if c in df.columns])


def check_corrections(manifest: dict | None,
                      df: pd.DataFrame | None = None) -> tuple[list[str], list[str]]:
    """Validate the declaration against the data. Returns ``(errors, warnings)``."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        corrections = resolve_corrections(manifest)
    except ValueError as exc:
        return [str(exc)], []

    if df is None:
        return errors, warnings

    columns = set(df.columns)

    for i, corr in enumerate(corrections):
        if corr.column not in columns:
            errors.append(
                f"corrections[{i}] corrects {corr.column!r}, which is not in the "
                f"data. A correction with nothing to correct is not a correction "
                f"(SPEC-01 §2.13.1)")
        for name, role in ((corr.adjusted, "adjusted"),
                           (corr.uncertainty, "uncertainty")):
            if name and name not in columns:
                errors.append(
                    f"corrections[{i}] declares {role} column {name!r}, "
                    f"absent from the data")
        if not corr.produced_by:
            warnings.append(
                f"corrections[{i}] ({corr.column}) declares no 'produced_by'. "
                f"A corrected value whose producer is unrecorded cannot be "
                f"reproduced or superseded")

    # Undeclared derived columns: the situation the block exists to prevent.
    declared = {c for corr in corrections for c in corr.derived_columns}
    stray = sorted(c for c in columns
                   if c.endswith((ADJUSTED_SUFFIX, UNCERTAINTY_SUFFIX))
                   and c not in declared)
    if stray:
        errors.append(
            f"Undeclared corrected column(s) {stray}. `_adj` and `_sigma` are "
            f"reserved by SPEC-01 §2.13.1 and MUST be declared in the manifest "
            f"`corrections` block: a correction nobody can trace is what §3.14 "
            f"exists to prevent")

    return errors, warnings
