"""Heading convention (SPEC-01 §2.5).

Movebank and many receivers express course over ground on [-180, 180];
Telemachus requires [0, 360). Twenty-five public datasets fail on it. Neither
side has a bug: it is an undeclared convention, and the two are the same
measurement.
"""

import numpy as np
import pandas as pd

import telemachus as tele
from telemachus.core.plausibility import check_heading_convention
from telemachus.core.units import convert


def _h(values):
    return check_heading_convention(np.asarray(values, dtype=float))


# ---------------------------------------------------------------------------
# The three readings a negative sign can have
# ---------------------------------------------------------------------------

def test_canonical_is_silent():
    assert _h(np.linspace(0, 359.9, 200)) is None


def test_the_signed_convention_is_named_and_the_fix_is_given():
    f = _h(np.linspace(-179, 179, 200))
    assert f and f.severity == "error"
    assert "[-180, 180]" in f.message
    assert "% 360" in f.message
    assert "not a correction" in f.message


def test_a_sentinel_is_not_a_convention_and_must_not_be_normalised():
    """The reading that makes this worth more than an inequality. A file whose
    headings reach 350 and also carry -1 is using -1 for "unknown"; `% 360`
    would turn every one into 359, due north."""
    f = _h(np.r_[np.linspace(0, 350, 195), [-1.0] * 5])
    assert f and f.severity == "error"
    assert "sentinel" in f.message
    assert "Do NOT take them modulo 360" in f.message
    assert "359, due north" in f.message


def test_values_outside_both_conventions_are_neither():
    f = _h(np.r_[np.linspace(-179, 179, 195), [-999.0] * 5])
    assert f and "outside both" in f.message


def test_a_signed_column_is_told_from_a_sentinel_by_its_positive_side():
    """A signed heading never exceeds 180. That is the whole discriminator."""
    signed = _h(np.linspace(-179, 179, 200))
    sentinel = _h(np.r_[np.linspace(0, 350, 195), [-1.0] * 5])
    assert "convention Movebank" in signed.message
    assert "sentinel" in sentinel.message


def test_where_the_convention_cannot_be_told_it_does_not_matter():
    """A vehicle that only ever headed east reads as canonical under both
    conventions, because the numbers are identical."""
    assert _h(np.linspace(60, 120, 200)) is None


def test_an_empty_column_says_nothing():
    assert _h([]) is None
    assert _h([np.nan, np.nan]) is None


# ---------------------------------------------------------------------------
# Declaring it, which is optional
# ---------------------------------------------------------------------------

def test_declaring_the_signed_convention_converts_exactly():
    assert float(convert([-90.0], "angle", "deg_signed").iloc[0]) == 270.0
    assert float(convert([179.0], "angle", "deg_signed").iloc[0]) == 179.0
    assert float(convert([0.0], "angle", "deg_signed").iloc[0]) == 0.0


def test_declaring_canonical_does_not_silently_repair_a_false_declaration():
    """`deg` means "already canonical". If it is not, that is for the validator
    to report, not for the converter to hide."""
    assert float(convert([-90.0], "angle", "deg").iloc[0]) == -90.0


def test_the_spelling_is_discoverable():
    from telemachus.core.units import known_units
    assert "deg_signed" in known_units("angle")


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_validate_gives_the_conversion_rather_than_out_of_range():
    df = pd.DataFrame({
        "ts": pd.date_range("2026-03-01T08:00:00Z", periods=200, freq="1s"),
        "lat": 49.33, "lon": 1.38, "speed_mps": 12.0,
        "heading_deg": np.linspace(-179, 179, 200)})
    report = tele.validate(df)
    assert not report.ok
    assert any("% 360" in e for e in report.errors), report.errors


def test_the_normalised_file_passes():
    df = pd.DataFrame({
        "ts": pd.date_range("2026-03-01T08:00:00Z", periods=200, freq="1s"),
        "lat": 49.33, "lon": 1.38, "speed_mps": 12.0,
        "heading_deg": np.linspace(-179, 179, 200) % 360})
    assert not any("heading" in e for e in tele.validate(df).errors)
