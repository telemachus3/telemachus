"""Acquisition breaks (SPEC-02 §3.9) and corrections (SPEC-01 §2.13.1).

Between them these answer the two questions a file could not previously
answer: was the acquisition intact, and what happened to a value that was
corrected.
"""

import numpy as np
import pandas as pd
import pytest
import yaml

import telemachus as tele
from telemachus.core.breaks import (
    REGISTERED_KINDS,
    BreakError,
    check_acquisition_breaks,
    resolve_acquisition_breaks,
)
from telemachus.core.corrections import (
    check_corrections,
    resolve_corrections,
    strip_corrections,
)


# ---------------------------------------------------------------------------
# Acquisition breaks
# ---------------------------------------------------------------------------

BREAKS = {
    "acquisition_breaks": [
        {"start": "2026-05-21T14:03:11Z", "end": "2026-05-21T14:07:52Z",
         "kind": "gnss_outage", "scope": "gnss",
         "detection_method": "device-reported", "notes": "Underground car park"},
        {"start": "2026-06-02T08:11:00Z", "end": "2026-06-05T19:40:00Z",
         "kind": "late_delivery", "scope": "device"},
    ]
}


def test_absent_block_is_not_a_claim_that_nothing_happened():
    assert resolve_acquisition_breaks({}) == []


def test_breaks_resolve_sorted_and_utc():
    breaks = resolve_acquisition_breaks(BREAKS)
    assert [b.kind for b in breaks] == ["gnss_outage", "late_delivery"]
    assert str(breaks[0].start.tz) == "UTC"
    assert breaks[0].duration_s() == pytest.approx(281.0)


def test_a_break_knows_which_instants_it_covers():
    b = resolve_acquisition_breaks(BREAKS)[0]
    assert b.covers("2026-05-21T14:05:00Z")
    assert b.covers("2026-05-21T14:03:11Z")          # bounds included
    assert not b.covers("2026-05-21T14:08:00Z")


def test_an_open_interval_has_no_end():
    b = resolve_acquisition_breaks({"acquisition_breaks": [
        {"start": "2026-06-01T00:00:00Z", "end": "present", "kind": "sensor_frozen"}]})[0]
    assert b.open_ended and b.covers("2030-01-01T00:00:00Z")
    assert np.isnan(b.duration_s())


def test_late_delivery_is_its_own_kind():
    """A gap is final; a late delivery is transient. Opposite reactions."""
    assert "late_delivery" in REGISTERED_KINDS
    assert "data_gap" in REGISTERED_KINDS


def test_an_interval_that_ends_before_it_starts_is_refused():
    with pytest.raises(BreakError, match="ends before it starts"):
        resolve_acquisition_breaks({"acquisition_breaks": [
            {"start": "2026-06-02T00:00:00Z", "end": "2026-06-01T00:00:00Z",
             "kind": "data_gap"}]})


def test_a_break_without_a_kind_declares_nothing_usable():
    with pytest.raises(BreakError, match="missing"):
        resolve_acquisition_breaks({"acquisition_breaks": [
            {"start": "2026-06-01T00:00:00Z", "end": "2026-06-02T00:00:00Z"}]})


def test_an_unregistered_kind_warns_and_is_carried_through():
    """The vocabulary is open: a later revision must not break a reader."""
    errors, warnings = check_acquisition_breaks({"acquisition_breaks": [
        {"start": "2026-06-01T00:00:00Z", "end": "2026-06-02T00:00:00Z",
         "kind": "solar_flare"}]})
    assert errors == []
    assert any("open" in w for w in warnings)


def _frame(n=10, start="2026-06-01T00:00:00Z"):
    return pd.DataFrame({
        "ts": pd.date_range(start, periods=n, freq="1s"),
        "lat": 49.33, "lon": 1.38, "speed_mps": 12.0})


def test_a_data_gap_the_file_disproves_is_an_error():
    """The one claim the data can contradict."""
    df = _frame()
    errors, _ = check_acquisition_breaks({"acquisition_breaks": [
        {"start": "2026-06-01T00:00:00Z", "end": "2026-06-01T00:00:09Z",
         "kind": "data_gap"}]}, df)
    assert errors and "10 row(s) in it" in errors[0]


def test_a_gnss_outage_over_populated_rows_is_fine():
    """The IMU keeps running through an outage; rows are expected."""
    errors, _ = check_acquisition_breaks({"acquisition_breaks": [
        {"start": "2026-06-01T00:00:00Z", "end": "2026-06-01T00:00:09Z",
         "kind": "gnss_outage"}]}, _frame())
    assert errors == []


def test_validate_manifest_surfaces_a_malformed_break(tmp_path):
    path = tmp_path / "manifest.yaml"
    path.write_text(
        "dataset_id: XX_test_2026\nschema_version: telemachus-1.0\n"
        "source: {type: synthetic}\n"
        "acquisition_breaks:\n"
        "  - {start: 2026-06-02T00:00:00Z, end: 2026-06-01T00:00:00Z, kind: data_gap}\n")
    report = tele.validate_manifest(path)
    assert not report.ok
    assert any("ends before it starts" in e for e in report.errors)


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------

CORRECTED = {
    "corrections": [
        {"column": "lat", "adjusted": "lat_adj", "uncertainty": "lat_sigma",
         "produced_by": "acme-refine@2.3.1"},
        {"column": "lon", "adjusted": "lon_adj", "produced_by": "acme-refine@2.3.1"},
    ]
}


def _corrected_frame():
    df = _frame()
    df["lat_adj"] = df["lat"] + 3e-6
    df["lat_sigma"] = 0.4
    df["lon_adj"] = df["lon"] - 1e-6
    return df


def test_the_source_column_survives_the_correction():
    df = _corrected_frame()
    assert (df["lat"] == 49.33).all()
    assert not (df["lat_adj"] == df["lat"]).any()


def test_stripping_the_corrections_gives_back_the_source_file():
    """SPEC-01 §2.13.1: the invariant that makes losslessness checkable."""
    source = _frame()
    corrected = _corrected_frame()
    recovered = strip_corrections(corrected, CORRECTED)
    pd.testing.assert_frame_equal(recovered, source)


def test_stripping_works_from_the_suffixes_alone():
    """A consumer holding only a parquet file can still do it."""
    pd.testing.assert_frame_equal(strip_corrections(_corrected_frame()), _frame())


def test_a_correction_with_nothing_to_correct_is_refused():
    df = _corrected_frame().drop(columns=["lat"])
    errors, _ = check_corrections(CORRECTED, df)
    assert any("nothing to correct is not a correction" in e for e in errors)


def test_an_undeclared_corrected_column_is_refused():
    df = _corrected_frame()
    df["speed_mps_adj"] = 12.5
    errors, _ = check_corrections(CORRECTED, df)
    assert any("Undeclared corrected column" in e for e in errors)


def test_a_declared_column_missing_from_the_data_is_refused():
    errors, _ = check_corrections(CORRECTED, _frame())
    assert any("lat_adj" in e for e in errors)


def test_an_untraceable_correction_warns():
    manifest = {"corrections": [{"column": "lat", "adjusted": "lat_adj"}]}
    df = _frame()
    df["lat_adj"] = 49.331
    errors, warnings = check_corrections(manifest, df)
    assert errors == []
    assert any("produced_by" in w for w in warnings)


def test_produced_by_is_never_interpreted():
    """A pipeline publishes corrected data without publishing how it corrects."""
    corr = resolve_corrections(CORRECTED)[0]
    assert corr.produced_by == "acme-refine@2.3.1"
    assert corr.derived_columns == ("lat_adj", "lat_sigma")


def test_the_whole_thing_end_to_end(tmp_path):
    manifest = {
        "dataset_id": "XX_corrected_2026",
        "schema_version": "telemachus-1.0",
        "profile": "core",
        "source": {"type": "synthetic"},
        "data_files": [{"path": "data.parquet", "format": "parquet"}],
        **CORRECTED,
        **BREAKS,
    }
    (tmp_path / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    _corrected_frame().to_parquet(tmp_path / "data.parquet", index=False)

    report = tele.validate_dataset(tmp_path, level="full")
    assert report.ok, report.errors
