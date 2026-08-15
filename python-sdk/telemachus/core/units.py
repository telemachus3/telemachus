"""Declared-unit conversion to Telemachus canonical units.

SPEC-01 §5 states which unit each column carries and how to reach it from the
units devices actually emit. This module is that table, executable.

The point is not to save a multiplication. It is to move the unit from the
adapter's code, where it is a constant nobody re-reads, to the adapter's
declaration, where it is data a reviewer can check against the source
documentation. An adapter that declares ``speed: {column: v, unit: km/h}``
cannot silently ship km/h in a column named ``speed_mps``; an adapter that
writes ``df["speed_mps"] = df["v"] / 3.6`` can, and the mistake survives every
schema check because the column name and the type are both right.

Conversions are exact ratios, never fitted: ``9.80665`` is the standard gravity
of the SI brochure, not ``9.81``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np
import pandas as pd

__all__ = [
    "QUANTITY_BY_COLUMN",
    "UnknownUnitError",
    "canonical_unit",
    "convert",
    "known_units",
    "quantity_of",
]

# Standard gravity (SI brochure, 9th ed.) and the degree, both exact.
G0 = 9.80665
DEG2RAD = np.pi / 180.0


class UnknownUnitError(ValueError):
    """A declared unit is not one this version knows how to convert."""


# ---------------------------------------------------------------------------
# Which physical quantity each Telemachus column carries
# ---------------------------------------------------------------------------
# Only columns whose value depends on a unit appear here. Counts, flags and
# identifiers are converted by type, not by factor, and are handled by the
# caller.

QUANTITY_BY_COLUMN: dict[str, str] = {
    "ts": "time",
    "ts_received_ms": "time",
    "lat": "latlon",
    "lon": "latlon",
    "speed_mps": "speed",
    "speed_obd_mps": "speed",
    "heading_deg": "angle",
    "altitude_gps_m": "length",
    "h_accuracy_m": "length",
    "odometer_m": "length",
    "segment_distance_m": "length",
    "ax_mps2": "acceleration",
    "ay_mps2": "acceleration",
    "az_mps2": "acceleration",
    "gx_rad_s": "angular_rate",
    "gy_rad_s": "angular_rate",
    "gz_rad_s": "angular_rate",
    "mx_uT": "magnetic_field",
    "my_uT": "magnetic_field",
    "mz_uT": "magnetic_field",
    "vehicle_voltage_v": "voltage",
    "battery_voltage_v": "voltage",
    "battery_current_a": "current",
}


def quantity_of(column: str) -> str | None:
    """Physical quantity carried by a Telemachus column, or None if unitless."""
    return QUANTITY_BY_COLUMN.get(column)


# ---------------------------------------------------------------------------
# Unit tables, one per quantity
# ---------------------------------------------------------------------------
# Each entry maps every spelling this library accepts to a multiplicative
# factor towards the canonical unit. Spellings are matched after lowercasing
# and removing spaces and underscores, so "km/h", "KM/H" and "km / h" are one
# unit and only one has to be written down.

_SCALES: dict[str, dict[str, float]] = {
    "speed": {
        "m/s": 1.0, "mps": 1.0, "ms-1": 1.0,
        "km/h": 1 / 3.6, "kmh": 1 / 3.6, "kph": 1 / 3.6,
        "mph": 0.44704, "mi/h": 0.44704,
        "kn": 0.514444, "kt": 0.514444, "knot": 0.514444, "knots": 0.514444,
        "ft/s": 0.3048, "fps": 0.3048,
        "cm/s": 0.01,
    },
    "acceleration": {
        "m/s2": 1.0, "m/s^2": 1.0, "mps2": 1.0, "ms-2": 1.0,
        "g": G0, "g-force": G0, "gforce": G0,
        "mg": G0 / 1000.0, "milli-g": G0 / 1000.0, "millig": G0 / 1000.0,
        "cm/s2": 0.01, "cm/s^2": 0.01, "gal": 0.01,
    },
    "angular_rate": {
        "rad/s": 1.0, "rads": 1.0, "rps": 1.0,
        "deg/s": DEG2RAD, "degs": DEG2RAD, "dps": DEG2RAD, "°/s": DEG2RAD,
        "mdeg/s": DEG2RAD / 1000.0,
        "rev/min": 2 * np.pi / 60.0, "rpm": 2 * np.pi / 60.0,
    },
    "magnetic_field": {
        "ut": 1.0, "µt": 1.0, "microtesla": 1.0,
        "nt": 1e-3, "nanotesla": 1e-3,
        "mt": 1e3, "millitesla": 1e3,
        "t": 1e6, "tesla": 1e6,
        "g": 100.0, "gauss": 100.0,
        "mgauss": 0.1, "milligauss": 0.1,
    },
    "length": {
        "m": 1.0, "metre": 1.0, "meter": 1.0,
        "km": 1000.0, "kilometre": 1000.0, "kilometer": 1000.0,
        "cm": 0.01, "mm": 0.001,
        "ft": 0.3048, "feet": 0.3048, "foot": 0.3048,
        "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
        "nmi": 1852.0,
    },
    "angle": {
        "deg": 1.0, "degree": 1.0, "degrees": 1.0, "°": 1.0,
        "rad": 1 / DEG2RAD, "radian": 1 / DEG2RAD, "radians": 1 / DEG2RAD,
    },
    "voltage": {
        "v": 1.0, "volt": 1.0, "volts": 1.0,
        "mv": 1e-3, "millivolt": 1e-3,
    },
    "current": {
        "a": 1.0, "amp": 1.0, "ampere": 1.0, "amperes": 1.0,
        "ma": 1e-3, "milliamp": 1e-3, "milliampere": 1e-3,
    },
}

CANONICAL: dict[str, str] = {
    "speed": "m/s",
    "acceleration": "m/s^2",
    "angular_rate": "rad/s",
    "magnetic_field": "uT",
    "length": "m",
    "angle": "deg",
    "voltage": "V",
    "current": "A",
    "latlon": "deg",
    "time": "datetime64[ns, UTC]",
}


def _key(unit: str) -> str:
    return str(unit).strip().lower().replace(" ", "").replace("_", "")


# ---------------------------------------------------------------------------
# Latitude / longitude — the one quantity that is not a scale factor
# ---------------------------------------------------------------------------

def _nmea_to_decimal(v: pd.Series) -> pd.Series:
    """NMEA ``DDDMM.MMMM`` to decimal degrees, sign preserved.

    The hemisphere letter that NMEA carries in a separate field is not visible
    here; a source that encodes South and West as letters must have applied the
    sign before this point, which is what :mod:`telemachus.adapters.nmea` does.
    """
    sign = np.sign(v)
    a = v.abs()
    degrees = np.floor(a / 100.0)
    minutes = a - degrees * 100.0
    return sign * (degrees + minutes / 60.0)


_LATLON: dict[str, Callable[[pd.Series], pd.Series]] = {
    "deg": lambda s: s,
    "degree": lambda s: s,
    "degrees": lambda s: s,
    "dd": lambda s: s,
    "decimal": lambda s: s,
    "decimaldegrees": lambda s: s,
    "rad": lambda s: s / DEG2RAD,
    "radian": lambda s: s / DEG2RAD,
    "radians": lambda s: s / DEG2RAD,
    "nmea": _nmea_to_decimal,
    "ddmm.mmmm": _nmea_to_decimal,
    "ddmm": _nmea_to_decimal,
    "semicircles": lambda s: s * (180.0 / 2**31),
}


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------

_EPOCH_UNITS = {
    "epochs": "s", "epochsec": "s", "epochseconds": "s", "unix": "s", "s": "s",
    "epochms": "ms", "epochmilliseconds": "ms", "unixms": "ms", "ms": "ms",
    "epochus": "us", "epochmicroseconds": "us", "us": "us",
    "epochns": "ns", "epochnanoseconds": "ns", "ns": "ns",
}


def _to_utc(values: pd.Series, unit: str, *, fmt: str | None = None) -> pd.Series:
    k = _key(unit)
    if k in _EPOCH_UNITS:
        ts = pd.to_datetime(pd.to_numeric(values, errors="coerce"),
                            unit=_EPOCH_UNITS[k], utc=True, errors="coerce")
    elif k in ("iso8601", "iso", "rfc3339", "datetime", "string", "str"):
        ts = pd.to_datetime(values, utc=True, errors="coerce", format=fmt)
    else:
        raise UnknownUnitError(
            f"Unknown time unit {unit!r}. Expected one of "
            f"{sorted(set(_EPOCH_UNITS) | {'iso8601'})}"
        )
    # A naive source is read as UTC rather than as local time: guessing an
    # offset from a filename or a hostname is how datasets acquire a silent
    # one-hour bias that no validator can see.
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC")
    return ts


# ---------------------------------------------------------------------------
# Public conversion entry point
# ---------------------------------------------------------------------------

def known_units(quantity: str) -> list[str]:
    """Accepted spellings for a quantity, for error messages and documentation."""
    if quantity == "latlon":
        return sorted(_LATLON)
    if quantity == "time":
        return sorted(set(_EPOCH_UNITS) | {"iso8601"})
    return sorted(_SCALES.get(quantity, {}))


def canonical_unit(quantity: str) -> str:
    """Telemachus unit for a quantity, as written in SPEC-01 §5."""
    return CANONICAL[quantity]


def convert(values, quantity: str, unit: str, *, fmt: str | None = None) -> pd.Series:
    """Convert a column of declared unit to the Telemachus canonical unit.

    Parameters
    ----------
    values : array-like
        Raw column, as read from the source.
    quantity : str
        One of the keys of :data:`CANONICAL`.
    unit : str
        Unit the source is declared to carry. Matching ignores case, spaces
        and underscores.
    fmt : str or None
        ``strftime`` pattern, for a timestamp column whose text form pandas
        cannot infer.

    Returns
    -------
    pd.Series
        Values in the canonical unit. Unparseable entries become NaN (or NaT)
        rather than raising: a single malformed row must not cost the file, and
        the row accounting downstream will report it.
    """
    s = values if isinstance(values, pd.Series) else pd.Series(values)

    if quantity == "time":
        return _to_utc(s, unit, fmt=fmt)

    numeric = pd.to_numeric(s, errors="coerce")

    if quantity == "latlon":
        fn = _LATLON.get(_key(unit))
        if fn is None:
            raise UnknownUnitError(
                f"Unknown lat/lon unit {unit!r}. Expected one of {known_units('latlon')}"
            )
        return fn(numeric)

    table = _SCALES.get(quantity)
    if table is None:
        raise UnknownUnitError(f"No unit table for quantity {quantity!r}")
    factor = table.get(_key(unit))
    if factor is None:
        raise UnknownUnitError(
            f"Unknown {quantity} unit {unit!r}. Expected one of {known_units(quantity)}"
        )
    return numeric if factor == 1.0 else numeric * factor


def convert_column(values, column: str, unit: str, *, fmt: str | None = None) -> pd.Series:
    """Convert towards the unit implied by a Telemachus *column name*.

    Raises ``UnknownUnitError`` if the column carries no unit — declaring one
    for ``hdop`` or ``n_satellites`` is a sign the mapping is confused about
    what the column holds.
    """
    quantity = quantity_of(column)
    if quantity is None:
        raise UnknownUnitError(
            f"Column {column!r} is unitless; remove the 'unit' key from its mapping"
        )
    return convert(values, quantity, unit, fmt=fmt)


def describe_units() -> Mapping[str, list[str]]:
    """Every quantity and the unit spellings it accepts."""
    return {q: known_units(q) for q in CANONICAL}
