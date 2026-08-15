"""Declared-unit conversion (SPEC-01 §5)."""

import numpy as np
import pandas as pd
import pytest

from telemachus.core.units import (
    G0,
    UnknownUnitError,
    canonical_unit,
    convert,
    convert_column,
    known_units,
    quantity_of,
)


def test_spec01_table_is_implemented():
    """Every conversion SPEC-01 §5 tabulates."""
    assert convert([36.0], "speed", "km/h").iloc[0] == pytest.approx(10.0)
    assert convert([1.0], "acceleration", "g").iloc[0] == pytest.approx(G0)
    assert convert([180.0], "angular_rate", "deg/s").iloc[0] == pytest.approx(np.pi)
    assert convert([4919.8], "latlon", "nmea").iloc[0] == pytest.approx(49.33, abs=1e-4)
    assert convert([1.0], "length", "km").iloc[0] == pytest.approx(1000.0)


def test_standard_gravity_is_exact():
    """9.80665, not 9.81 — the 0.07% difference is a real bug in the wild."""
    assert convert([1.0], "acceleration", "g").iloc[0] == 9.80665


def test_unit_spelling_is_forgiving():
    for spelling in ("km/h", "KM/H", "kmh", "kph", " km / h "):
        assert convert([36.0], "speed", spelling).iloc[0] == pytest.approx(10.0)


def test_nmea_sign_is_preserved():
    assert convert([-4919.8], "latlon", "nmea").iloc[0] == pytest.approx(-49.33, abs=1e-4)


def test_epoch_and_iso_timestamps():
    iso = convert(["2026-03-01T08:00:00Z"], "time", "iso8601").iloc[0]
    for unit, value in (("epoch_s", 1772352000), ("epoch_ms", 1772352000_000),
                        ("epoch_ns", 1772352000_000_000_000)):
        assert convert([value], "time", unit).iloc[0] == iso


def test_naive_timestamps_are_read_as_utc_not_local():
    ts = convert(["2026-03-01 08:00:00"], "time", "iso8601").iloc[0]
    assert ts == pd.Timestamp("2026-03-01T08:00:00Z")


def test_unknown_unit_lists_what_is_accepted():
    with pytest.raises(UnknownUnitError) as exc:
        convert([1.0], "speed", "furlongs/fortnight")
    assert "km/h" in str(exc.value)


def test_unparseable_values_become_nan_rather_than_raising():
    out = convert(["12.5", "not a number", ""], "speed", "m/s")
    assert out.iloc[0] == 12.5
    assert out.iloc[1:].isna().all()


def test_column_names_carry_their_quantity():
    assert quantity_of("speed_mps") == "speed"
    assert quantity_of("gx_rad_s") == "angular_rate"
    assert quantity_of("hdop") is None
    assert canonical_unit("magnetic_field") == "uT"
    assert "deg/s" in known_units("angular_rate")


def test_declaring_a_unit_on_a_unitless_column_is_refused():
    with pytest.raises(UnknownUnitError):
        convert_column([9], "n_satellites", "count")


def test_gauss_and_g_do_not_collide():
    """`g` means gravity for an accelerometer and gauss for a magnetometer."""
    assert convert([1.0], "acceleration", "g").iloc[0] == pytest.approx(G0)
    assert convert([1.0], "magnetic_field", "g").iloc[0] == pytest.approx(100.0)
