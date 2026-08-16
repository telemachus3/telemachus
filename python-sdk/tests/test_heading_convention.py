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
    assert "turns -1 into 359" in f.message


def test_a_far_negative_sentinel_is_named_as_one_and_not_as_garbage():
    """Changed deliberately from "outside both", which was true and useless.

    A signed column carrying -999 has two defects, and the old message named
    neither: it reported a span and left the producer to work out that -999 is
    a sentinel and that `% 360` — the fix the signed convention needs — would
    silently turn it into a heading of 81.
    """
    f = _h(np.r_[np.linspace(-179, 179, 195), [-999.0] * 5])
    assert f and f.severity == "error"
    assert "sentinels" in f.message
    assert "turns -999 into 81" in f.message
    # And the second defect, so the producer is not sent round twice.
    assert "still needs `% 360`" in f.message


def test_a_column_out_of_any_angular_scale_is_still_reported_as_such():
    """Nine of the reference datasets. Negatives present or not, a column
    running to 32 515 is not a file with a few sentinels in it, and the scale
    is the headline."""
    for values in ([10.0, 90.0, 32515.0], [-5.0, 90.0, 32515.0]):
        f = _h(np.array(values))
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


# ---------------------------------------------------------------------------
# Two populations the reference corpus showed and the first version missed
# ---------------------------------------------------------------------------


def test_a_constant_column_is_not_diagnosed_as_a_convention():
    """The regression this file exists to prevent from coming back.

    One dataset carries -1 on every row. The first version answered the
    convention question anyway — "this is course over ground on [-180, 180]...
    converts exactly with `heading_deg % 360`" — and a producer following that
    advice turns a file whose heading is unknown everywhere into one pointing
    due north everywhere.

    A heading identifies its convention by *varying*. A column that does not
    vary carries no evidence either way, and the only honest answer says what
    is known and stops.
    """
    f = _h(np.full(100, -1.0))
    assert f and f.severity == "error"
    assert "never varies" in f.message
    assert "sentinel" in f.message
    # It must not assert a convention, nor recommend the conversion.
    assert "Movebank" not in f.message
    assert "converts exactly" not in f.message


def test_the_constant_rule_does_not_depend_on_the_sentinel_being_negative():
    """-1 and -999 are conventions of habit, not a rule. The rule is variance."""
    for sentinel in (-1.0, -999.0, 999.0):
        f = _h(np.full(50, sentinel))
        assert f and "never varies" in f.message, sentinel


def test_a_stationary_vehicle_with_a_valid_constant_heading_is_left_alone():
    """The check runs only on a column already outside [0, 360), so a parked
    device reporting the same valid heading all day is never touched by it."""
    assert _h(np.full(100, 90.0)) is None


def test_the_closed_interval_is_told_apart_from_out_of_scale():
    """Twelve of the twenty-five reference datasets, previously reported as
    "outside both the canonical range and the signed convention" — technically
    true, and misleading: 360 and 0 are the same bearing, and the source is not
    using a different convention, it is using the closed interval."""
    f = _h(np.array([0.0, 90.0, 180.0, 270.0, 360.0]))
    assert f and f.severity == "error"
    assert "closed interval [0, 360]" in f.message
    assert "1 row(s) carry exactly 360" in f.message
    assert "outside both" not in f.message


def test_the_closed_interval_names_the_conversion_and_denies_it_is_a_correction():
    """SPEC-01 §2.13.1 exists for values that were changed. 360 -> 0 changes
    the spelling of a bearing, not the bearing, so it needs no `_adj` — and a
    producer who is not told that will either invent a column or leave the
    file non-conformant."""
    f = _h(np.array([0.0, 90.0, 360.0]))
    assert "`heading_deg % 360`" in f.message
    assert "no `_adj`" in f.message


def test_a_single_360_in_a_million_rows_is_still_reported():
    """The smallest real case: six values out of 422 596. Reporting it is the
    point — SPEC-01 §2.5 requires the half-open range, and a rule nothing
    verifies is the defect this project just spent a release removing."""
    values = np.concatenate([np.random.default_rng(0).uniform(0, 360, 10_000), [360.0]])
    f = _h(values)
    assert f and "1 row(s) carry exactly 360" in f.message
