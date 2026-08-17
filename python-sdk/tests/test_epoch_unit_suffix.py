"""The unit a column *name* announces, for the one quantity that can hide it.

`speed_mps` cannot ship km/h without the numbers saying so, and
`telemachus.core.plausibility` says so. `ts_received_ms` could ship microseconds
in complete silence up to 1.0.0a4: the column was named right, typed int64 as
SPEC-01 requires, and carried a positive integer of an entirely plausible order
of magnitude for a timestamp. The only way to see it was to subtract it from
something, and even then only if the result was absurd enough — the occurrence
that surfaced it produced a latency of 1.78e12 seconds. At a factor of a
thousand instead of a million it would have produced a latency in hours, which
is plausible, wrong, and nobody's bug report.

Two things are tested here, because the fix has two halves that do different
work. The conversion repairs what this library produces. The validator check
repairs nothing and catches what someone else's code produced, which for a pivot
format is most of the files it will ever see.
"""

import pandas as pd
import pytest

from telemachus.core.plausibility import check_epoch_columns
from telemachus.core.schemas import ALL_KNOWN_COLUMNS, coerce_schema_dtypes
from telemachus.core.units import (
    EPOCH_UNIT_BY_SUFFIX,
    convert,
    convert_column,
    epoch_unit_of,
    quantity_of,
    to_epoch,
)

NOW = pd.Timestamp("2026-08-17T12:00:00Z")

#: 2026-08-17T10:00:01Z, the instant of the report that opened this file.
RECV_ISO = "2026-08-17T10:00:01Z"
RECV_MS = 1786960801000


def _csv(tmp_path, recv: str) -> str:
    p = tmp_path / "source.csv"
    p.write_text(f"when,recv,lat,lon\n2026-08-17T10:00:00Z,{recv},48.0,2.0\n")
    return p


def _mapping(unit: str) -> dict:
    return {"dataset_id": "t", "device_id": "d1", "columns": {
        "ts": {"column": "when", "unit": "iso8601"},
        "ts_received_ms": {"column": "recv", "unit": unit},
        "lat": {"column": "lat", "unit": "deg"},
        "lon": {"column": "lon", "unit": "deg"}}}


# ---------------------------------------------------------------------------
# The conversion
# ---------------------------------------------------------------------------

def test_a_ms_column_arrives_in_milliseconds(tmp_path):
    """The reported case, verbatim. Thirteen digits, not sixteen."""
    from telemachus.adapters import csv_mapping

    df = csv_mapping.load(_csv(tmp_path, RECV_ISO), mapping=_mapping("iso8601"))
    assert int(df["ts_received_ms"].iloc[0]) == RECV_MS
    assert str(df["ts_received_ms"].dtype) == "Int64"


@pytest.mark.parametrize("unit,value", [
    ("iso8601", RECV_ISO),
    ("epoch_s", "1786960801"),
    ("epoch_ms", "1786960801000"),
    ("epoch_us", "1786960801000000"),
    ("epoch_ns", "1786960801000000000"),
])
def test_the_result_does_not_follow_the_source_s_resolution(tmp_path, unit, value):
    """The shape of the defect, and the reason it was not a single missing ×1000.

    Up to 1.0.0a4 the column came back in whatever resolution the *source* was
    declared in — seconds for `epoch_s`, nanoseconds for `epoch_ns` — because the
    conversion produced a datetime and the integer cast published its underlying
    ticks. `epoch_ms` was correct by coincidence, which is the worst of the five
    cases: it is the one that makes the bug look absent.
    """
    from telemachus.adapters import csv_mapping

    df = csv_mapping.load(_csv(tmp_path, value), mapping=_mapping(unit))
    assert int(df["ts_received_ms"].iloc[0]) == RECV_MS


def test_ts_itself_stays_a_datetime(tmp_path):
    """The suffix rule must not reach the column that has no suffix."""
    from telemachus.adapters import csv_mapping

    df = csv_mapping.load(_csv(tmp_path, RECV_ISO), mapping=_mapping("iso8601"))
    assert pd.api.types.is_datetime64_any_dtype(df["ts"])
    assert df["ts"].iloc[0] == pd.Timestamp("2026-08-17T10:00:00Z")


def test_the_target_column_decides_the_form_of_a_timestamp():
    """Same quantity, same unit, two forms — the routing this fix introduces."""
    naive = convert([RECV_ISO], "time", "iso8601")
    routed = convert([RECV_ISO], "time", "iso8601", column="ts_received_ms")
    assert pd.api.types.is_datetime64_any_dtype(naive)
    assert int(routed.iloc[0]) == RECV_MS


def test_convert_column_cannot_forget_the_suffix():
    assert int(convert_column([RECV_ISO], "ts_received_ms", "iso8601").iloc[0]) == RECV_MS
    assert pd.api.types.is_datetime64_any_dtype(convert_column([RECV_ISO], "ts", "iso8601"))


def test_an_angular_rate_ending_in_s_is_not_an_instant():
    """`gx_rad_s` ends in `_s`. The quantity is what makes the suffix readable."""
    assert epoch_unit_of("gx_rad_s") is None
    assert epoch_unit_of("ts") is None
    assert epoch_unit_of("ts_received_ms") == "ms"
    assert quantity_of("gx_rad_s") == "angular_rate"


def test_a_missing_instant_stays_missing():
    """NaT cast blindly to int64 is a date in 1677, and it looks like data."""
    out = convert_column([RECV_ISO, "", "not a date"], "ts_received_ms", "iso8601")
    assert int(out.iloc[0]) == RECV_MS
    assert out.iloc[1:].isna().all()


def test_to_epoch_refuses_to_guess_a_resolution():
    """An integer carries none, and inventing one here is the original defect."""
    with pytest.raises(TypeError):
        to_epoch(pd.Series([RECV_MS]), "ms")


def test_the_type_coercion_reduces_a_datetime_at_the_promised_resolution():
    """The second door. `coerce_schema_dtypes` is where the resolution was lost,
    so a frame that reaches it with a datetime in an int64 column must come out
    in milliseconds rather than in pandas' own resolution."""
    df = pd.DataFrame({"ts": [pd.Timestamp("2026-08-17T10:00:00Z")],
                       "ts_received_ms": [pd.Timestamp(RECV_ISO)]})
    out = coerce_schema_dtypes(df)
    assert int(out["ts_received_ms"].iloc[0]) == RECV_MS


# ---------------------------------------------------------------------------
# The validator check
# ---------------------------------------------------------------------------

def _frame(values, column="ts_received_ms") -> pd.DataFrame:
    return pd.DataFrame({"ts": pd.to_datetime(["2026-08-17T10:00:00Z"] * len(values),
                                              utc=True),
                         column: values})


def test_genuine_milliseconds_raise_nothing():
    assert check_epoch_columns(_frame([RECV_MS, RECV_MS + 500]), now=NOW) == []


def test_a_float_column_of_milliseconds_raises_nothing():
    """What the consuming pipeline actually writes: float64, not int64. The type
    is a matter for SPEC-01 §3 rule 9; this check is about the magnitude, and
    must not report the same file twice under the wrong rule."""
    assert check_epoch_columns(_frame([float(RECV_MS)]), now=NOW) == []


def test_microseconds_in_a_ms_column_are_refused_and_named():
    findings = check_epoch_columns(_frame([RECV_MS * 1000]), now=NOW)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "error"
    assert f.column == "ts_received_ms"
    assert "microseconds" in f.message
    assert "// 1000" in f.message


def test_seconds_in_a_ms_column_are_refused_and_repaired_the_other_way():
    """The other direction, and it is not symmetric.

    A column carrying microseconds is divided; one carrying seconds is
    multiplied. Naming the divisor in both cases is how the message came to
    offer `// 0` to anyone whose source was in seconds — which the first version
    of this test did not catch, because it only asserted the word "seconds".
    """
    findings = check_epoch_columns(_frame([RECV_MS // 1000]), now=NOW)
    assert len(findings) == 1
    message = findings[0].message
    assert "carries seconds" in message
    assert "* 1000" in message


@pytest.mark.parametrize("values", [
    [RECV_MS * 1000],           # microseconds
    [RECV_MS * 1000_000],       # nanoseconds
    [RECV_MS // 1000],          # seconds
    [17, 42],                   # no resolution at all
])
def test_no_message_ever_advises_dividing_by_zero(values):
    """The repair offered has to be arithmetic that runs."""
    for finding in check_epoch_columns(_frame(values), now=NOW):
        assert "// 0" not in finding.message
        assert "* 0" not in finding.message


def test_values_that_are_no_resolution_at_all_are_not_blamed_on_a_unit():
    findings = check_epoch_columns(_frame([17, 42]), now=NOW)
    assert len(findings) == 1
    assert "never instants" in findings[0].message


def test_a_datetime_in_the_column_is_left_to_the_type_rule():
    """Reporting a type mismatch here would say the same thing twice, in the
    language of a rule this check does not own."""
    assert check_epoch_columns(_frame([pd.Timestamp(RECV_ISO)]), now=NOW) == []


def test_an_empty_or_absent_column_is_not_a_finding():
    assert check_epoch_columns(pd.DataFrame({"ts": []}), now=NOW) == []
    assert check_epoch_columns(_frame([None, None]), now=NOW) == []


def test_the_check_reaches_the_validator():
    """A check nobody calls is a rule nobody enforces."""
    import telemachus as tele

    df = pd.DataFrame({
        "ts": pd.date_range("2026-08-17T10:00:00Z", periods=3, freq="1s"),
        "lat": [48.0, 48.0001, 48.0002],
        "lon": [2.0, 2.0001, 2.0002],
        "ts_received_ms": [RECV_MS * 1000] * 3,
    })
    report = tele.validate(df, profile="core", level="strict")
    assert not report.ok
    assert any("microseconds" in e for e in report.errors), report.errors


# ---------------------------------------------------------------------------
# The canary
# ---------------------------------------------------------------------------

def _time_columns() -> dict[str, object]:
    return {name: field.type for name, field in ALL_KNOWN_COLUMNS.items()
            if quantity_of(name) == "time"}


def test_every_time_column_in_the_schema_resolves_to_a_unit():
    """The canary, and deliberately not "does ts_received_ms convert correctly".

    A test suite pinned to one column name proves that one column works. Add
    `ts_sent_us` to the provenance group tomorrow and every assertion above
    stays green while the new column reproduces the defect exactly: its suffix
    is never read, its int64 is filled from whatever resolution pandas chose,
    and nothing anywhere goes red.

    So the assertion is about coverage of the *schema*. Every column this
    library classifies as time must be resolvable one way or the other — an
    integer one to a resolution, a datetime one to none — and a column that is
    neither is a column whose unit nobody enforces.
    """
    import pyarrow as pa

    columns = _time_columns()
    assert columns, (
        "no column is classified as time, so this file is measuring nothing")

    integer_columns = {n: t for n, t in columns.items() if pa.types.is_integer(t)}
    assert integer_columns, (
        "no time column is declared as an integer, so the suffix table is no "
        "longer reachable from the schema and this file is measuring nothing")

    unresolved = sorted(n for n in integer_columns if epoch_unit_of(n) is None)
    assert not unresolved, (
        f"integer time column(s) whose resolution nothing states: {unresolved}. "
        f"Their values are published at whatever resolution the producer "
        f"happened to hold — add the suffix to EPOCH_UNIT_BY_SUFFIX, or rename "
        f"the column so its name carries its unit (SPEC-01 §1.1)")

    misread = sorted(n for n, t in columns.items()
                     if pa.types.is_timestamp(t) and epoch_unit_of(n) is not None)
    assert not misread, (
        f"datetime column(s) the suffix table claims as integer epochs: "
        f"{misread}. One of the two declarations is wrong")


def test_the_unrouted_conversion_never_lands_on_milliseconds_by_itself():
    """The guard on the guard. A test that cannot fail proves nothing, so this
    models the defect and shows the assertions above are measuring the routing.

    Without a target column a timestamp comes back as a datetime whose
    resolution is pandas' own — nanoseconds on pandas 2.1, microseconds on
    pandas 3 — never the millisecond the column name promises. That is the whole
    of the a1..a4 defect, and the reason its factor was not even constant across
    environments: the same file converted on two machines was wrong by a
    thousand on one and by a million on the other.
    """
    naive = convert([RECV_ISO], "time", "iso8601")
    assert naive.dtype.unit != "ms", (
        "if a bare convert() ever returns milliseconds of its own accord, the "
        "assertions above stop proving that anything reads the suffix")


def test_the_suffix_table_and_the_resolutions_it_names_agree():
    """Each entry must be a resolution pandas understands, or the table names
    units it cannot deliver."""
    for suffix, unit in EPOCH_UNIT_BY_SUFFIX.items():
        stamped = to_epoch(pd.Series([pd.Timestamp(RECV_ISO)]), unit)
        assert stamped.notna().all(), suffix
        assert str(stamped.dtype) == "Int64", suffix
