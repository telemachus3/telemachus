# telemachus

[![PyPI](https://img.shields.io/pypi/v/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Python](https://img.shields.io/pypi/pyversions/telemachus.svg)](https://pypi.org/project/telemachus/)

Python SDK for the **Telemachus** open telematics format — read,
validate, convert, and introspect high-frequency GNSS+IMU datasets.

```
pip install telemachus
```

**Try it in 5 minutes**: the [AEGIS demo notebook](../docs/notebooks/aegis-demo.ipynb)
([open in Colab](https://colab.research.google.com/github/telemachus3/telemachus/blob/main/docs/notebooks/aegis-demo.ipynb))
downloads a real Zenodo dataset, loads it, and plots one trip.

## Read a dataset

```python
import telemachus as tele

df = tele.read("path/to/manifest.yaml")   # → pandas DataFrame
print(tele.sensor_profile(df))             # → "gps+imu+gyro"
```

## Sensor introspection

```python
tele.has_gps(df)       # True if lat, lon, speed_mps non-NaN
tele.has_imu(df)       # True if ax, ay, az non-NaN
tele.has_gyro(df)      # True if gx, gy, gz present
tele.has_magneto(df)   # True if mx, my, mz present
tele.has_obd(df)       # True if speed_obd or rpm present
tele.has_io(df)        # True if ignition or voltage present
tele.is_full_imu(df)   # accel + gyro
tele.is_gps_only(df)   # GPS but no IMU
```

## Validate

```python
report = tele.validate(df, profile="imu")
print(report)
# ValidationReport(PASS, profile=imu, level=basic, errors=0, warnings=0)

report = tele.validate_dataset("path/to/dataset/", level="full")
```

Three profiles adapt validation to hardware capabilities:

| Profile | Required columns | Use case |
|---------|-----------------|----------|
| `core` | ts, lat, lon, speed_mps | GPS trackers, fleet APIs |
| `imu` | core + ax, ay, az | Telematics devices with accelerometer |
| `full` | imu + gx, gy, gz | Research platforms with gyroscope |

## Convert Open datasets

```bash
tele convert aegis /path/to/aegis/csvs -o datasets/aegis/
tele convert pvs /path/to/pvs/trips -o datasets/pvs/ --placement dashboard
tele convert stride /path/to/stride/road_data -o datasets/stride/ --category driving
```

Supported Open datasets:

| Adapter | Source | Sensors | License |
|---------|--------|---------|---------|
| `aegis` | Zenodo 820576 (Austria) | GPS 5Hz + Accel 24Hz + Gyro + OBD | CC-BY-4.0 |
| `pvs` | Kaggle (Brazil) | GPS 1Hz + Accel 100Hz + Gyro + Magneto | CC-BY-NC-ND-4.0 |
| `stride` | Figshare (Bangladesh) | GPS 1Hz + Accel 100Hz + Gyro + Magneto | CC-BY-4.0 |

## CLI

```bash
tele validate path/to/manifest.yaml          # validate manifest
tele validate path/to/dataset/ --level full   # validate dataset
tele info path/to/manifest.yaml               # dataset summary
tele convert aegis /data/aegis -o out/        # convert Open dataset
```

## Telemachus record format

A Telemachus record is a flat Parquet row with 7 functional groups:

| # | Group | Columns | Status |
|---|-------|---------|--------|
| 1 | **Datetime** | `ts` | Mandatory |
| 2 | **GNSS** | `lat`, `lon`, `speed_mps`, `heading_deg`, `altitude_gps_m`, `hdop`, `h_accuracy_m`, `n_satellites` | Mandatory (lat/lon/speed) |
| 3 | **IMU** | `ax_mps2`, `ay_mps2`, `az_mps2`, `gx_rad_s`, `gy_rad_s`, `gz_rad_s`, `mx_uT`, `my_uT`, `mz_uT` | Profile-dependent |
| 4 | **OBD** | `speed_obd_mps`, `rpm`, `odometer_m` | Optional |
| 5 | **CAN** | `x_can_<signal>` | Future |
| 6 | **I/O** | `ignition`, `vehicle_voltage_v` | Optional |
| 7 | **Extra** | `x_<source>_<field>` | Optional |

Full specification: [SPEC-01](../spec/SPEC-01-record-format.md) |
[SPEC-02](../spec/SPEC-02-manifest.md) |
[SPEC-03](../spec/SPEC-03-adapters-validation.md)

## Development

```bash
git clone https://github.com/telemachus3/telemachus
cd telemachus/python-sdk
pip install -e .[dev]
pytest                  # 31 tests
```

## License

AGPL-3.0
