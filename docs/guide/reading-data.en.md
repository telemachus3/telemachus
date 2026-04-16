# Reading Telemachus data

A Telemachus Telemachus dataset is, on disk:

```
my-dataset/
├── manifest.yaml          ← SPEC-02: device, trip, sensors, acc_periods…
├── d0_<id_1>.parquet      ← signal, columnar
├── d0_<id_2>.parquet
└── …
```

The signal parquet is "pure" — only the columns defined by SPEC-01
§3 (`ts`, `lat`, `lon`, `speed_mps`, `ax/ay/az_mps2`, optional `gx/gy/gz_rad_s`,
recommended `heading_deg`, `hdop`, `n_satellites`).

Everything else lives in the manifest.

## With pandas

```python
import pandas as pd
import yaml
from pathlib import Path

ds = Path("my-dataset")
manifest = yaml.safe_load((ds / "manifest.yaml").read_text())

df = pd.concat(
    [pd.read_parquet(p) for p in ds.glob("d0_*.parquet")],
    ignore_index=True,
).sort_values("ts").reset_index(drop=True)

# Inherit device_id from manifest if absent (SPEC-02 §4.1)
if "device_id" not in df.columns:
    devices = manifest.get("hardware", {}).get("devices", [])
    if len(devices) == 1:
        df["device_id"] = devices[0]["name"]

# Tag each row with its accelerometer frame (SPEC-02 §4.2)
def frame_for(ts):
    for p in manifest.get("acc_periods", []):
        if pd.Timestamp(p["start"]) <= ts <= pd.Timestamp(p["end"]):
            return p["frame"]
    return "raw"  # default

df["acc_frame"] = pd.to_datetime(df["ts"]).apply(frame_for)
```

## With DuckDB

DuckDB reads parquet natively and is great for ad-hoc exploration:

```python
import duckdb
con = duckdb.connect()
con.sql("SELECT * FROM 'my-dataset/d0_*.parquet' LIMIT 5").show()
con.sql("""
    SELECT
        date_trunc('minute', ts) AS minute,
        AVG(speed_mps) AS v,
        COUNT(*) AS n
    FROM 'my-dataset/d0_*.parquet'
    GROUP BY 1 ORDER BY 1
""").show()
```

## Multi-rate gotcha

Telemachus files are timestamped at the **IMU rate** (typically 10 Hz). GNSS
columns (`lat`, `lon`, `speed_mps`, `heading_deg`) contain `NaN` on
rows where no GNSS fix is available.

When computing per-row metrics, drop NaNs explicitly:

```python
gnss = df.dropna(subset=["lat", "lon"])
imu = df  # all rows have IMU
```

See [Concepts → Multi-rate](../concepts.md#multi-rate-imu-vs-gnss).

## Per-trip iteration

If your manifest declares `trip_carrier_states`, you can iterate
trips and filter on `is_vehicle_data`:

```python
for trip in manifest.get("trip_carrier_states", []):
    state = trip["carrier_state"]
    if state not in ("mounted_driving", "mounted_idle"):
        continue  # skip desk/handheld/etc.
    sub = df[df["trip_id"] == trip["trip_id"]]
    # ... your analytics
```
