"""Personal data — defined by the format, restricted at publication.

SPEC-01 §2.4 defines `device_imei` and `sim_iccid` as real columns, and it is
right to: a telematics record legitimately carries them, and a format that
refused to name them would push every producer into an `x_` extra where nothing
could recognise them. Being able to name a thing is what makes it governable.

What must not happen is that they leave the building. SPEC-04 §5.1 says so in
prose, and until now nothing checked it: a dataset carrying a live IMEI and a
live SIM serial passed `tele validate --level strict` in silence. That is the
same defect this release fixes everywhere else — a rule the specification
asserts and the implementation does not enforce — except that this one leaks
third-party data, and a leak is the single thing a later version cannot undo.

An IMEI identifies a device, a device identifies a vehicle, and a vehicle with a
trajectory identifies a person. Four published positions are enough to
re-identify most individuals in a mobility dataset; the identifier just removes
the need to bother.

The rule this module enforces:

- a personal-data column carrying values is always **reported**, at every level,
  because a producer should never be surprised by what is in their own file;
- it becomes an **error** when the manifest itself says the dataset is going out
  — an open licence, or a source declared as open. That is the moment the
  intent to publish is on record, and the moment the check has the standing to
  refuse.

The fix is never to hash the IMEI in place. It is to drop the column and give
`device_id` an opaque value, which is what SPEC-01 §2.4 asks for: a hash of an
IMEI is still a per-device identifier, joinable against any other table holding
the same hash.
"""

from __future__ import annotations

import pandas as pd

__all__ = ["OPEN_LICENCE_PREFIXES", "PII_COLUMNS", "check_pii", "strip_pii"]

#: SPEC-01 §2.4. Defined by the format, restricted at publication.
PII_COLUMNS = ("device_imei", "sim_iccid")

#: Declaring one of these in the manifest is declaring an intent to publish.
OPEN_LICENCE_PREFIXES = ("CC-BY", "CC0", "CC-", "MIT", "APACHE", "BSD", "ODBL",
                         "ODC-", "PDDL", "GPL", "LGPL", "AGPL", "PUBLIC")


def _declares_publication(manifest: dict | None) -> str | None:
    """What in the manifest says this dataset is going out, if anything."""
    if not manifest:
        return None
    licence = str(manifest.get("license") or "").strip()
    if licence and licence.upper().startswith(OPEN_LICENCE_PREFIXES):
        return f"license: {licence}"
    source = manifest.get("source") or {}
    if source.get("type") == "open_external":
        return "source.type: open_external"
    if source.get("url") or source.get("doi"):
        return "source.doi/url is set"
    return None


def check_pii(df: pd.DataFrame,
              manifest: dict | None = None) -> tuple[list[str], list[str]]:
    """Look for personal data in a frame. Returns ``(errors, warnings)``.

    A column that is present but entirely null is not a leak: an adapter that
    creates the column and never fills it has done nothing wrong, and failing it
    would teach producers to avoid the standard name, which is the opposite of
    what §2.4 wants.
    """
    errors: list[str] = []
    warnings: list[str] = []

    carrying = [c for c in PII_COLUMNS
                if c in df.columns and df[c].notna().any()]
    if not carrying:
        return errors, warnings

    counts = ", ".join(f"{c} ({int(df[c].notna().sum())} rows)" for c in carrying)
    reason = _declares_publication(manifest)

    # Either it is a refusal or it is a heads-up, never both: the same fact
    # printed twice reads as two problems.
    if reason:
        errors.append(
            f"Personal data present in a dataset declared for publication "
            f"({reason}): {counts}. SPEC-01 §2.4 keeps these columns out of "
            f"published datasets. Drop them and give `device_id` an opaque "
            f"value — do not hash the IMEI in place, a hash is still a "
            f"per-device identifier and still joins")
    else:
        warnings.append(
            f"Personal data present: {counts}. Legitimate in an internal "
            f"dataset (SPEC-01 §2.4 defines these columns), but they MUST NOT "
            f"be published. `strip_pii` removes them")

    return errors, warnings


def strip_pii(df: pd.DataFrame, *, device_id: str | None = None) -> pd.DataFrame:
    """Return the frame without its personal-data columns.

    Parameters
    ----------
    device_id : str or None
        Replacement value for the `device_id` column. Supply an opaque
        identifier when the existing one is itself an IMEI, which is common:
        removing `device_imei` while `device_id` holds the same number achieves
        nothing.
    """
    out = df.drop(columns=[c for c in PII_COLUMNS if c in df.columns])
    if device_id is not None:
        out["device_id"] = device_id
    return out
