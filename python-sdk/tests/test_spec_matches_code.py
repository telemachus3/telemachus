"""The normative text and the table the validator consults must agree.

This file exists because they did not. SPEC-01 §2.3.1 was written to make
`speed_mps` conditional, `MANDATORY_CORE` in `core/schemas.py` was not touched,
and version 1.0.0a3 shipped a specification saying a column may be absent next
to a validator that refused every file without it. Two people read the changed
text closely, one of them corrected four inconsistencies inside it, and neither
looked at the Python set the validator actually reads.

A prose specification and a Python set are two encodings of one decision, and
nothing tied them together. So the test parses the tables of §2.3 out of the
markdown and compares them to the code. It is deliberately narrow: it does not
check the whole specification, only the one table whose disagreement with the
code silently invalidates every conformance claim the project makes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from telemachus.core.schemas import (
    CONDITIONAL_CORE,
    MANDATORY_BY_PROFILE,
)

SPEC = Path(__file__).resolve().parents[2] / "spec" / "SPEC-01-record-format.md"

# The three tables of §2.3 and the profiles each one adds columns to.
TABLES = {
    "All profiles (core, imu, full):": ("core", "imu", "full"),
    "Profile `imu` and `full` add:": ("imu", "full"),
    "Profile `full` adds:": ("full",),
}


def _rows(intro: str) -> list[tuple[str, str]]:
    """The (column, description) pairs of the markdown table after ``intro``."""
    text = SPEC.read_text(encoding="utf-8")
    start = text.index(f"**{intro}**") + len(intro)
    chunk = text[start:].split("\n\n")[1]          # the table, up to the blank line
    out = []
    for line in chunk.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].startswith("`"):
            continue                               # header or separator row
        out.append((cells[0].strip("`"), cells[-1]))
    return out


def _declared() -> dict[str, set[str]]:
    """What §2.3 says is mandatory, per profile, conditional rows excluded."""
    declared: dict[str, set[str]] = {p: set() for p in ("core", "imu", "full")}
    for intro, profiles in TABLES.items():
        for column, description in _rows(intro):
            if "conditional" in description.lower():
                continue                           # §2.3.1 and its kind
            for profile in profiles:
                declared[profile].add(column)
    return declared


@pytest.mark.parametrize("profile", ["core", "imu", "full"])
def test_the_code_requires_exactly_what_the_spec_requires(profile):
    declared = _declared()[profile]
    # Canary. A parser that reads nothing compares nothing and passes, which
    # is the quietest way for this file to stop protecting anything.
    assert declared, (
        f"§2.3 parsed as empty for profile {profile!r}. Either the tables "
        f"moved or this parser stopped reading them; either way this file is "
        f"measuring nothing and must be fixed rather than trusted."
    )
    assert MANDATORY_BY_PROFILE[profile] == declared, (
        f"SPEC-01 §2.3 and MANDATORY_BY_PROFILE disagree on profile "
        f"{profile!r}. Only the spec says: {sorted(declared - MANDATORY_BY_PROFILE[profile])}. "
        f"Only the code says: {sorted(MANDATORY_BY_PROFILE[profile] - declared)}."
    )


def test_a_column_the_spec_calls_conditional_is_conditional_in_the_code():
    """The specific failure that produced this file."""
    conditional = {c for intro in TABLES for c, d in _rows(intro)
                   if "conditional" in d.lower()}
    # Canary, and the one that matters most here. This parser recognises a
    # conditional row by the word "conditional" in its description cell, which
    # is prose. Reword it to "optional when the receiver does not measure it"
    # and the set below goes empty, every column reads as mandatory, and the
    # test above starts comparing everything to everything — green, and blind.
    assert conditional, (
        "no row in the §2.3 tables is marked conditional any more. Either the "
        "spec changed its wording or this parser stopped reading it. Either "
        "way this file is measuring nothing."
    )
    assert conditional == CONDITIONAL_CORE, (
        f"§2.3 marks {sorted(conditional)} conditional, the code marks "
        f"{sorted(CONDITIONAL_CORE)}"
    )
    for profile, mandatory in MANDATORY_BY_PROFILE.items():
        assert not (conditional & mandatory), (
            f"profile {profile!r} requires {sorted(conditional & mandatory)}, "
            f"which §2.3 calls conditional"
        )
