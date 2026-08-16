"""Temporal plausibility (SPEC-03 §4.7) — instants that cannot be instants.

Every rule in SPEC-01 §3 accepts a row dated 1970 without a word. The
descriptive layer downstream then reports a three-minute drive as spanning
fifty-six years, and nothing in between says anything.
"""

import pandas as pd
import pytest

import telemachus as tele
from telemachus.core.plausibility import GPS_EPOCH, check_timestamps

NOW = pd.Timestamp("2026-08-16T12:00:00Z")


def _frame(timestamps):
    """Build a frame WITHOUT re-converting: a list of far-future Timestamps
    passed back through pd.to_datetime wraps into 1970, which would make the
    fixture test something other than what it claims."""
    ts = timestamps if isinstance(timestamps, pd.Series) else pd.Series(timestamps)
    return pd.DataFrame({"ts": ts, "lat": 49.33, "lon": 1.38, "speed_mps": 12.0})


def _clean(n=50, start="2026-03-01T08:00:00Z"):
    return pd.Series(pd.date_range(start, periods=n, freq="1s", tz="UTC"))


def test_a_plausible_trace_is_silent():
    assert check_timestamps(_frame(_clean()), now=NOW) == []


def test_an_uninitialised_clock_is_refused():
    """The case measured in the wild: four rows at the Unix epoch."""
    ts = pd.Series([pd.Timestamp("1970-01-01T00:00:00Z")] * 4 + list(_clean(46)))
    findings = check_timestamps(_frame(ts.sort_values()), now=NOW)
    assert findings and findings[0].severity == "error"
    assert "4 row(s)" in findings[0].message
    assert "before GPS time began" in findings[0].message


def test_the_message_offers_both_readings_of_a_1970_date():
    """Uninitialised RTC and epoch-seconds-as-milliseconds are indistinguishable
    once the frame is built, so the message must not pick one."""
    ts = pd.Series([pd.Timestamp("1970-01-01T00:00:00Z")] * 3 + list(_clean(47)))
    msg = check_timestamps(_frame(ts.sort_values()), now=NOW)[0].message
    assert "restarted at the Unix epoch" in msg
    assert "seconds read as milliseconds" in msg


def test_epoch_seconds_read_as_milliseconds():
    ts = pd.to_datetime([1786000000 + i for i in range(50)], unit="ms", utc=True)
    findings = check_timestamps(_frame(pd.Series(ts)), now=NOW)
    assert findings[0].severity == "error"
    assert "before GPS time began" in findings[0].message


def test_the_future_is_refused_at_a_representable_date():
    """Year 2200 fits in every datetime64 resolution, so this holds on any
    supported pandas."""
    ts = pd.Series(pd.date_range("2200-01-01T00:00:00Z", periods=5, freq="1s"))
    findings = check_timestamps(_frame(ts), now=NOW)
    assert findings and findings[0].severity == "error"
    assert "in the future" in findings[0].message


def _far_future_or_skip():
    """Year 58566, or a skip.

    Whether a timestamp beyond year 2262 can exist in a column is a property of
    pandas, not of this library: with non-nanosecond resolution it is an
    ordinary value, with nanoseconds only it cannot be represented and the
    conversion raises. The check's behaviour is worth testing where the case can
    occur; asserting it everywhere would test pandas.
    """
    try:
        return pd.Series(pd.to_datetime([1786000000000 + i for i in range(50)],
                                        unit="s", utc=True))
    except Exception:                                    # OutOfBoundsDatetime
        pytest.skip("this pandas cannot represent a date beyond year 2262, so "
                    "epoch milliseconds read as seconds raises at construction "
                    "and never reaches a validator")


def test_epoch_milliseconds_read_as_seconds_names_the_unit():
    findings = check_timestamps(_frame(_far_future_or_skip()), now=NOW)
    assert findings[0].severity == "error"
    assert "milliseconds read as seconds" in findings[0].message


def test_a_clock_three_days_ahead_is_refused():
    """Just past the tolerance, the everyday case: a device clock that ran away."""
    findings = check_timestamps(_frame(_clean(start="2026-08-19T00:00:00Z")), now=NOW)
    assert findings and "in the future" in findings[0].message


def test_ordinary_clock_drift_is_tolerated():
    """A device clock drifts and a gateway stamps on receipt. Hours are not an
    error; days are."""
    assert check_timestamps(_frame(_clean(start="2026-08-16T18:00:00Z")), now=NOW) == []


def test_a_decade_long_file_warns_rather_than_fails():
    ts = pd.Series(pd.to_datetime(["2014-01-01T00:00:00Z", "2026-01-01T00:00:00Z"]))
    findings = check_timestamps(_frame(ts), now=NOW)
    assert findings and findings[0].severity == "warning"
    assert "12 years" in findings[0].message


def test_the_span_warning_stays_quiet_when_a_bound_already_fired():
    """A 1970 row makes the span absurd by construction. Saying both restates
    one fault as two."""
    ts = pd.Series([pd.Timestamp("1970-01-01T00:00:00Z")] + list(_clean(49)))
    findings = check_timestamps(_frame(ts.sort_values()), now=NOW)
    assert len(findings) == 1


def test_now_is_injectable_so_the_verdict_is_reproducible():
    """A validator whose answer depends on the day it runs cannot be tested."""
    future = _frame(_clean(start="2027-01-01T00:00:00Z"))
    assert check_timestamps(future, now=NOW)
    assert check_timestamps(future, now=pd.Timestamp("2027-06-01T00:00:00Z")) == []


def test_the_gps_epoch_is_the_floor_and_not_an_arbitrary_year():
    assert GPS_EPOCH == pd.Timestamp("1980-01-06T00:00:00Z")


def test_an_empty_or_column_less_frame_says_nothing():
    assert check_timestamps(pd.DataFrame({"lat": [49.0]})) == []
    assert check_timestamps(pd.DataFrame({"ts": []})) == []


def test_validate_surfaces_it():
    ts = pd.Series([pd.Timestamp("1970-01-01T00:00:00Z")] * 4 + list(_clean(46)))
    report = tele.validate(_frame(ts.sort_values()))
    assert not report.ok
    assert any("GPS time began" in e for e in report.errors)
