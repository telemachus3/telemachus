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
    account = tele.RowAccount(raw_rows_in=0)
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


def test_a_mapping_can_be_a_yaml_file(export, tmp_path):
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump(MAPPING))
    assert len(csv_mapping.load(export, mapping=path)) == 200


def test_manifest_carries_the_accounting_and_the_declared_metadata(export):
    account = tele.RowAccount(raw_rows_in=0)
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
    account = tele.RowAccount(raw_rows_in=0)
    df = gpx.load(ride, account=account)
    assert account.finish(rows_out=len(df))["drop_reasons"] == {
        "duplicate_ts": 1, "no_timestamp": 1}


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
    account = tele.RowAccount(raw_rows_in=0)
    df = nmea.load(track, account=account)
    metrics = account.finish(rows_out=len(df))
    assert metrics["drop_reasons"] == {"bad_checksum": 1}


def test_nmea_refuses_to_invent_a_date(tmp_path):
    path = tmp_path / "gga_only.nmea"
    path.write_text(_sentence(
        "GPGGA,080000.00,4919.8000,N,00122.8000,E,1,09,0.9,52.1,M,46.9,M,,") + "\n")
    with pytest.raises(ValueError, match="will not guess"):
        nmea.load(path)
    assert len(nmea.load(path, date="2026-03-01")) == 1


def test_nmea_output_validates(track):
    assert tele.validate(nmea.load(track), profile="core").ok
