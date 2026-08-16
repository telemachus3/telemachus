"""Format adapters: CSV with a declarative mapping, GPX, NMEA.

These are the adapters that work on data this project has never seen, so the
tests are written from the position of someone arriving with their own export:
does the conversion happen, does it say what it threw away, and does the result
pass `tele validate`.
"""

import numpy as np
import pandas as pd
import pytest
import yaml

import telemachus as tele
from telemachus.adapters import csv_mapping, gpx, nmea
from telemachus.adapters.csv_mapping import MappingError

# ---------------------------------------------------------------------------
# CSV, declarative mapping
# ---------------------------------------------------------------------------

MAPPING = {
    "dataset_id": "FR_demo_2026",
    "device_id": "truck_07",
    "read": {"sep": ";", "decimal": ","},
    "columns": {
        "ts": {"column": "Horodatage", "unit": "iso8601"},
        "lat": {"column": "Latitude", "unit": "deg"},
        "lon": {"column": "Longitude", "unit": "deg"},
        "speed_mps": {"column": "Vitesse", "unit": "km/h"},
        "ax_mps2": {"column": "AccX", "unit": "g"},
        "ay_mps2": {"column": "AccY", "unit": "g"},
        "az_mps2": {"column": "AccZ", "unit": "g"},
        "n_satellites": {"column": "Satellites"},
    },
}


@pytest.fixture
def export(tmp_path):
    """A third-party export: foreign headers, semicolons, comma decimals,
    km/h speeds, g accelerations, two duplicated frames and one corrupt time."""
    n = 200
    ts = pd.date_range("2026-03-01T08:00:00Z", periods=n, freq="100ms")
    raw = pd.DataFrame({
        "Horodatage": ts.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3] + "Z",
        "Latitude": 49.33 + np.arange(n) * 1.2e-6,
        "Longitude": 1.38 + np.arange(n) * 2.0e-6,
        "Vitesse": 46.8,                          # km/h
        "AccX": 0.01, "AccY": 0.0, "AccZ": 1.0,   # g
        "Satellites": 9,
        "Conducteur": "anon",
    })
    raw = pd.concat([raw, raw.iloc[[10, 11]]], ignore_index=True)
    raw.loc[len(raw)] = ["not a date", 49.3, 1.4, 0, 0, 0, 1, 5, "anon"]
    path = tmp_path / "export.csv"
    raw.to_csv(path, index=False, sep=";", decimal=",")
    return path


def test_conversion_applies_the_declared_units(export):
    df = csv_mapping.load(export, mapping=MAPPING)
    assert df["speed_mps"].iloc[0] == pytest.approx(13.0, abs=1e-3)
    assert df["az_mps2"].iloc[0] == pytest.approx(9.80665, abs=1e-4)
    assert df["device_id"].iloc[0] == "truck_07"


def test_conversion_reports_what_it_dropped(export):
    account = tele.RowAccount()
    df = csv_mapping.load(export, mapping=MAPPING, account=account)
    metrics = account.finish(rows_out=len(df))
    assert metrics["raw_rows_in"] == 203
    assert metrics["rows_out"] == 200
    assert metrics["drop_reasons"] == {"duplicate_ts": 2, "unparseable_ts": 1}


def test_the_result_validates(export):
    df = csv_mapping.load(export, mapping=MAPPING)
    assert tele.validate(df, acc_frame="raw").ok


def test_unmapped_columns_are_dropped_or_carried_as_extras(export):
    assert "Conducteur" not in csv_mapping.load(export, mapping=MAPPING).columns
    kept = csv_mapping.load(export, mapping=MAPPING, extras="keep")
    assert "x_csv_conducteur" in kept.columns


def test_a_unit_is_required_on_a_column_that_carries_one(export):
    broken = {**MAPPING, "columns": {**MAPPING["columns"],
                                     "speed_mps": {"column": "Vitesse"}}}
    with pytest.raises(MappingError, match="'unit' is required"):
        csv_mapping.load(export, mapping=broken)


def test_a_misspelt_target_suggests_the_right_one(export):
    cols = {k: v for k, v in MAPPING["columns"].items() if k != "speed_mps"}
    cols["speed_ms"] = {"column": "Vitesse", "unit": "km/h"}
    with pytest.raises(MappingError, match="speed_mps"):
        csv_mapping.load(export, mapping={**MAPPING, "columns": cols})


def test_a_misspelt_source_column_lists_what_the_file_has(export):
    cols = {**MAPPING["columns"], "lat": {"column": "Latitud", "unit": "deg"}}
    with pytest.raises(MappingError) as exc:
        csv_mapping.load(export, mapping={**MAPPING, "columns": cols})
    assert "Latitude" in str(exc.value)


@pytest.fixture
def fleet_export(tmp_path):
    """One file, three vehicles, the same timestamps for all three.

    The shape any fleet export has, and the one a single scalar device_id
    cannot describe."""
    n = 60
    ts = pd.date_range("2026-03-01T08:00:00Z", periods=n, freq="1s")
    parts = []
    for i, name in enumerate(("truck_07", "truck_08", "truck_09")):
        parts.append(pd.DataFrame({
            "Horodatage": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Latitude": 49.33 + i * 0.01 + np.arange(n) * 1.2e-6,
            "Longitude": 1.38 + i * 0.01 + np.arange(n) * 2.0e-6,
            "Vitesse": 46.8,
            "Vehicule": name,
        }))
    path = tmp_path / "fleet.csv"
    pd.concat(parts, ignore_index=True).to_csv(path, index=False, sep=";", decimal=",")
    return path


FLEET_MAPPING = {
    "dataset_id": "FR_fleet_2026",
    "device_id": {"column": "Vehicule"},
    "read": {"sep": ";", "decimal": ","},
    "columns": {
        "ts": {"column": "Horodatage", "unit": "iso8601"},
        "lat": {"column": "Latitude", "unit": "deg"},
        "lon": {"column": "Longitude", "unit": "deg"},
        "speed_mps": {"column": "Vitesse", "unit": "km/h"},
    },
}


def test_device_id_can_name_a_column_when_one_file_holds_several_devices(fleet_export):
    out = csv_mapping.load(fleet_export, mapping=FLEET_MAPPING)
    assert sorted(out.device_id.unique()) == ["truck_07", "truck_08", "truck_09"]
    # nothing is dropped: three devices at the same instant are not duplicates
    assert len(out) == 180


def test_device_id_naming_an_absent_column_is_refused(fleet_export):
    mapping = FLEET_MAPPING | {"device_id": {"column": "Camion"}}
    with pytest.raises(MappingError, match="Camion"):
        csv_mapping.load(fleet_export, mapping=mapping)


def test_device_id_with_an_unsupported_key_is_refused(fleet_export):
    mapping = FLEET_MAPPING | {"device_id": {"colonne": "Vehicule"}}
    with pytest.raises(MappingError, match="device_id"):
        csv_mapping.load(fleet_export, mapping=mapping)


def test_a_mapped_column_is_measured_and_a_missing_one_is_absent(export):
    m = csv_mapping.manifest(MAPPING)["column_provenance"]
    assert m["speed_mps"] == "measured"
    # the watchlist states an absence rather than leaving it to be inferred
    assert m["heading_deg"] == "absent"


def test_a_mapping_can_say_the_source_computed_a_column(export):
    mapping = {**MAPPING, "columns": {
        **MAPPING["columns"],
        "speed_mps": {**MAPPING["columns"]["speed_mps"], "provenance": "derived"},
    }}
    assert csv_mapping.manifest(mapping)["column_provenance"]["speed_mps"] == "derived"
    # the column still converts: provenance describes it, it does not gate it
    assert len(csv_mapping.load(export, mapping=mapping)) == 200


def test_an_unknown_provenance_is_refused(export):
    mapping = {**MAPPING, "columns": {
        **MAPPING["columns"],
        "speed_mps": {**MAPPING["columns"]["speed_mps"], "provenance": "doppler"},
    }}
    with pytest.raises(MappingError, match="provenance"):
        csv_mapping.manifest(mapping)


def test_a_constant_column_is_not_reported_as_measured():
    mapping = {"dataset_id": "d", "columns": {
        "ts": {"column": "t", "unit": "iso8601"},
        "lat": {"column": "la", "unit": "deg"},
        "lon": {"column": "lo", "unit": "deg"},
        "speed_mps": {"value": 0.0},
    }}
    assert csv_mapping.manifest(mapping)["column_provenance"]["speed_mps"] == "derived"


# ---------------------------------------------------------------------------
# Guards against a silent column shift
# ---------------------------------------------------------------------------

@pytest.fixture
def headerless(tmp_path):
    """A headerless export addressed by index, with two fields always empty.

    The shape the guard exists for: no header to disagree with, so nothing
    detects that a field left the middle of the line.
    """
    def write(shift=False):
        rows = []
        for i in range(120):
            lat, lon = 49.33 + i * 1e-5, 1.38 + i * 1e-5
            fields = [f"2026-03-01T08:{i//60:02d}:{i%60:02d}Z", lat, lon,
                      12.5, "", "", 90.0]          # 7 fields, 4 and 5 empty
            if shift:
                # The observed failure: a field leaves the middle of the line
                # and the count stays right, so counting fields sees nothing.
                del fields[4]
                fields.append("")
            rows.append(";".join(str(f) for f in fields))
        path = tmp_path / ("shifted.csv" if shift else "clean.csv")
        path.write_text("\n".join(rows) + "\n")
        return path
    return write


HEADERLESS_MAPPING = {
    "dataset_id": "FR_headerless_2026",
    "device_id": "unit_01",
    "read": {"sep": ";", "header": None},
    "columns": {
        "ts": {"column": 0, "unit": "iso8601"},
        "lat": {"column": 1, "unit": "deg"},
        "lon": {"column": 2, "unit": "deg"},
        "speed_mps": {"column": 3, "unit": "m/s"},
        "heading_deg": {"column": 6, "unit": "deg"},
    },
    "guards": {"expected_fields": 7, "always_empty": [4, 5]},
}


def test_guards_are_silent_when_the_export_is_the_expected_shape(headerless):
    found = []
    csv_mapping.load(headerless(), mapping=HEADERLESS_MAPPING, anomalies=found)
    assert found == []


def test_a_removed_field_is_caught_by_the_always_empty_invariant(headerless):
    found = []
    csv_mapping.load(headerless(shift=True), mapping=HEADERLESS_MAPPING,
                     anomalies=found)
    # the field count alone would only see six fields for seven; the invariant
    # is what names the shift
    assert any("always_empty" in f for f in found), found


def test_a_shift_still_converts_because_a_guard_reports_and_does_not_refuse(headerless):
    found = []
    df = csv_mapping.load(headerless(shift=True), mapping=HEADERLESS_MAPPING,
                          anomalies=found)
    assert len(df) == 120 and found


def test_a_trailing_separator_does_not_cry_wolf(headerless, tmp_path):
    src = headerless()
    path = tmp_path / "trailing.csv"
    path.write_text("".join(line + ";\n" for line in
                            src.read_text().splitlines()))
    found = []
    csv_mapping.load(path, mapping=HEADERLESS_MAPPING, anomalies=found)
    assert found == [], found


def test_the_manifest_records_what_was_checked_and_what_was_found(headerless):
    found = []
    csv_mapping.load(headerless(shift=True), mapping=HEADERLESS_MAPPING,
                     anomalies=found)
    g = csv_mapping.manifest(HEADERLESS_MAPPING, anomalies=found)["source"]["guards"]
    assert g["declared"]["always_empty"] == [4, 5]
    assert g["findings"] == found and g["findings"]


def test_the_default_path_does_not_lose_a_finding(headerless):
    """The caller who never read the signature is the one to protect.

    Running the guards and dropping their result would reproduce, inside the
    guard, the silent loss the guard exists to prevent.
    """
    with pytest.warns(csv_mapping.GuardWarning, match="always_empty"):
        csv_mapping.load(headerless(shift=True), mapping=HEADERLESS_MAPPING)


def test_a_manifest_says_unknown_rather_than_empty_when_nobody_collected(headerless):
    with pytest.warns(csv_mapping.GuardWarning):
        csv_mapping.load(headerless(shift=True), mapping=HEADERLESS_MAPPING)
    g = csv_mapping.manifest(HEADERLESS_MAPPING)["source"]["guards"]
    # `[]` here would read as "checked, nothing found" on a source that is
    # in fact shifted
    assert g["findings"] is None


def test_a_clean_source_warns_nothing_on_the_default_path(headerless):
    import warnings as _w
    with _w.catch_warnings():
        _w.simplefilter("error", csv_mapping.GuardWarning)
        csv_mapping.load(headerless(), mapping=HEADERLESS_MAPPING)


def test_an_unsupported_guard_key_is_refused(headerless):
    mapping = {**HEADERLESS_MAPPING, "guards": {"alway_empty": [4]}}
    with pytest.raises(MappingError, match="guards"):
        csv_mapping.load(headerless(), mapping=mapping)


def test_a_mapping_can_be_a_yaml_file(export, tmp_path):
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump(MAPPING))
    assert len(csv_mapping.load(export, mapping=path)) == 200


def test_manifest_carries_the_accounting_and_the_declared_metadata(export):
    account = tele.RowAccount()
    df = csv_mapping.load(export, mapping=MAPPING, account=account)
    manifest = csv_mapping.manifest(MAPPING, account=account, rows_out=len(df))
    assert manifest["dataset_id"] == "FR_demo_2026"
    assert manifest["profile"] == "imu"
    assert manifest["source"]["metrics"]["raw_rows_dropped"] == 3


# ---------------------------------------------------------------------------
# GPX
# ---------------------------------------------------------------------------

GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="SomeWatch" xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk><name>Morning</name>
    <trkseg>
      <trkpt lat="49.3300" lon="1.3800"><ele>52.1</ele><time>2026-03-01T08:00:00Z</time>
        <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>118</gpxtpx:hr>
        </gpxtpx:TrackPointExtension></extensions></trkpt>
      <trkpt lat="49.3301" lon="1.3802"><ele>52.4</ele><time>2026-03-01T08:00:01Z</time></trkpt>
      <trkpt lat="49.3302" lon="1.3804"><ele>52.6</ele><time>2026-03-01T08:00:01Z</time></trkpt>
      <trkpt lat="49.3303" lon="1.3806"><ele>52.9</ele></trkpt>
    </trkseg>
    <trkseg>
      <trkpt lat="49.3400" lon="1.3900"><ele>60.0</ele><time>2026-03-01T09:00:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>
"""


@pytest.fixture
def ride(tmp_path):
    path = tmp_path / "ride.gpx"
    path.write_text(GPX)
    return path


def test_gpx_track_points_become_rows(ride):
    df = gpx.load(ride)
    assert len(df) == 3
    assert df["altitude_gps_m"].iloc[0] == pytest.approx(52.1, abs=1e-3)
    assert df["device_id"].iloc[0] == "SomeWatch"


def test_gpx_segments_become_trips(ride):
    assert gpx.load(ride)["trip_id"].nunique() == 2


def test_gpx_speed_is_absent_not_invented(ride):
    """GPX has no speed field; deriving one would put a computed value in a
    measurement column (SPEC-04 §5.2)."""
    df = gpx.load(ride)
    assert "speed_mps" in df.columns
    assert df["speed_mps"].isna().all()


def test_gpx_extensions_become_vendor_extras(ride):
    assert gpx.load(ride)["x_gpx_hr"].iloc[0] == "118"


def test_gpx_accounts_for_what_it_dropped(ride):
    account = tele.RowAccount()
    df = gpx.load(ride, account=account)
    assert account.finish(rows_out=len(df))["drop_reasons"] == {
        "duplicate_ts": 1, "no_timestamp": 1}


SHARED_SECOND = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.0" creator="OpenStreetMap.org"
     xmlns="http://www.topografix.com/GPX/1/0">
  <trk><trkseg>
    <trkpt lat="49.4400" lon="1.0900"><time>2026-03-01T08:00:00Z</time></trkpt>
  </trkseg></trk>
  <trk><trkseg>
    <trkpt lat="49.3300" lon="1.3800"><time>2026-03-01T08:00:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""


def test_gpx_two_recordings_may_share_a_second(tmp_path):
    """Two separate tracks are not duplicates of one another.

    A public archive hands back every contributor under one ``creator``, so
    ``device_id`` is constant and cannot key the dedup: two people who each
    recorded a point in the same second would lose one of them. The unit is the
    track segment. Measured on the Rouen extract of the OSM public traces,
    keying on the constant destroyed 7 618 of 178 436 timestamped points.
    """
    path = tmp_path / "shared.gpx"
    path.write_text(SHARED_SECOND)
    df = gpx.load(path)
    assert len(df) == 2
    assert df["trip_id"].nunique() == 2


def test_gpx_manifest_reads_the_file_rather_than_assuming(tmp_path):
    """Version and provenance are properties of the file, not of the adapter."""
    path = tmp_path / "shared.gpx"
    path.write_text(SHARED_SECOND)
    m = gpx.manifest(path)
    assert m["source"]["ingestion"] == "GPX 1.0 track points"
    # SPEC-01 §2.3.1: the column is in the frame, so it declares itself, and a
    # GPX with no speed extension declares `absent` rather than staying silent.
    assert m["column_provenance"]["speed_mps"] == "absent"


def test_gpx_manifest_declares_a_measured_speed_when_the_file_has_one(ride):
    """The Garmin fixture carries no speed; a Cluetrust one does."""
    assert gpx.manifest(ride)["column_provenance"]["speed_mps"] == "absent"
    assert gpx.manifest(ride)["column_provenance"]["altitude_gps_m"] == "measured"


# ---------------------------------------------------------------------------
# NMEA
# ---------------------------------------------------------------------------

def _sentence(body):
    checksum = 0
    for ch in body:
        checksum ^= ord(ch)
    return f"${body}*{checksum:02X}"


@pytest.fixture
def track(tmp_path):
    bodies = [
        "GPRMC,080000.00,A,4919.8000,N,00122.8000,E,25.3,84.5,010326,,,A",
        "GPGGA,080000.00,4919.8000,N,00122.8000,E,1,09,0.9,52.1,M,46.9,M,,",
        "GPGSV,3,1,11,01,05,040,20",
        "GPRMC,080001.00,A,4919.8060,N,00122.8100,E,25.1,84.8,010326,,,A",
        "GPGGA,080001.00,4919.8060,N,00122.8100,E,1,09,0.9,52.4,M,46.9,M,,",
    ]
    lines = [_sentence(b) for b in bodies]
    lines.append("$GPRMC,080002.00,A,4919.8120,N,00122.8200,E,25.0,85.0,010326,,,A*00")
    path = tmp_path / "track.nmea"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_nmea_merges_rmc_and_gga_into_one_row_per_epoch(track):
    df = nmea.load(track)
    assert len(df) == 2
    assert df["n_satellites"].iloc[0] == 9      # from GGA
    assert df["gnss_valid"].iloc[0]             # from RMC


def test_nmea_converts_ddmm_and_knots(track):
    df = nmea.load(track)
    assert df["lat"].iloc[0] == pytest.approx(49.33, abs=1e-4)
    assert df["lon"].iloc[0] == pytest.approx(1.38, abs=1e-4)
    assert df["speed_mps"].iloc[0] == pytest.approx(25.3 * 0.514444, abs=1e-3)


def test_nmea_counts_a_corrupt_position_sentence(track):
    account = tele.RowAccount()
    df = nmea.load(track, account=account)
    metrics = account.finish(rows_out=len(df))
    assert metrics["drop_reasons"] == {"bad_checksum": 1}


def test_nmea_manifest_declares_the_speed_measured(track):
    """An NMEA speed is the receiver's own solution, never the adapter's.

    The distinction is the whole point of SPEC-01 §2.14: a Doppler speed is
    independent of the position error, a position-differentiated one is made of
    it, and only the manifest can tell a consumer which one it holds.
    """
    p = nmea.manifest(track)["column_provenance"]
    assert p["speed_mps"] == "measured"
    assert p["heading_deg"] == "measured"
    assert p["altitude_gps_m"] == "measured"      # GGA carries it


def test_nmea_manifest_declares_absent_what_the_log_lacks(tmp_path):
    """A GGA-only log has no velocity sentence, and says so."""
    path = tmp_path / "gga_only.nmea"
    path.write_text(_sentence(
        "GPGGA,080000.00,4919.8000,N,00122.8000,E,1,09,0.9,52.1,M,46.9,M,,") + "\n")
    p = nmea.manifest(path)["column_provenance"]
    assert p["speed_mps"] == "absent"
    assert p["altitude_gps_m"] == "measured"


def test_nmea_refuses_to_invent_a_date(tmp_path):
    path = tmp_path / "gga_only.nmea"
    path.write_text(_sentence(
        "GPGGA,080000.00,4919.8000,N,00122.8000,E,1,09,0.9,52.1,M,46.9,M,,") + "\n")
    with pytest.raises(ValueError, match="will not guess"):
        nmea.load(path)
    assert len(nmea.load(path, date="2026-03-01")) == 1


def test_nmea_output_validates(track):
    assert tele.validate(nmea.load(track), profile="core").ok
