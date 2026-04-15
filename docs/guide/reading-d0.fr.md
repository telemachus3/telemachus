# Lire des données D0

Un dataset D0 Telemachus, sur disque :

```
mon-dataset/
├── manifest.yaml          ← RFC-0014 : device, trip, sensors, acc_periods…
├── d0_<id_1>.parquet      ← signal, colonnaire
├── d0_<id_2>.parquet
└── …
```

Le parquet de signal est « pur » — uniquement les colonnes définies
par RFC-0013 §3 (`ts`, `lat`, `lon`, `speed_mps`, `ax/ay/az_mps2`,
optionnels `gx/gy/gz_rad_s`, recommandés `heading_deg`, `hdop`,
`n_satellites`).

Tout le reste vit dans le manifest.

## Avec pandas

```python
import pandas as pd
import yaml
from pathlib import Path

ds = Path("mon-dataset")
manifest = yaml.safe_load((ds / "manifest.yaml").read_text())

df = pd.concat(
    [pd.read_parquet(p) for p in ds.glob("d0_*.parquet")],
    ignore_index=True,
).sort_values("ts").reset_index(drop=True)

# Hériter device_id du manifest si absent (RFC-0014 §4.1)
if "device_id" not in df.columns:
    devices = manifest.get("hardware", {}).get("devices", [])
    if len(devices) == 1:
        df["device_id"] = devices[0]["name"]

# Tagger chaque ligne avec son frame accéléromètre (RFC-0014 §4.2)
def frame_for(ts):
    for p in manifest.get("acc_periods", []):
        if pd.Timestamp(p["start"]) <= ts <= pd.Timestamp(p["end"]):
            return p["frame"]
    return "raw"  # défaut

df["acc_frame"] = pd.to_datetime(df["ts"]).apply(frame_for)
```

## Avec DuckDB

DuckDB lit le parquet nativement et excelle pour l'exploration
ad-hoc :

```python
import duckdb
con = duckdb.connect()
con.sql("SELECT * FROM 'mon-dataset/d0_*.parquet' LIMIT 5").show()
con.sql("""
    SELECT
        date_trunc('minute', ts) AS minute,
        AVG(speed_mps) AS v,
        COUNT(*) AS n
    FROM 'mon-dataset/d0_*.parquet'
    GROUP BY 1 ORDER BY 1
""").show()
```

## Piège multi-rate

Les fichiers D0 sont timestampés au **rythme IMU** (typiquement
10 Hz). Les colonnes GNSS (`lat`, `lon`, `speed_mps`, `heading_deg`)
contiennent `NaN` sur les lignes sans fix GNSS.

Pour calculer des métriques per-row, droppez explicitement les NaN :

```python
gnss = df.dropna(subset=["lat", "lon"])
imu = df  # toutes les lignes ont l'IMU
```

Voir [Concepts → Multi-rate](../concepts.md#multi-rate-imu-vs-gnss).

## Itération par trip

Si votre manifest déclare `trip_carrier_states`, vous pouvez itérer
les trips et filtrer sur `is_vehicle_data` :

```python
for trip in manifest.get("trip_carrier_states", []):
    state = trip["carrier_state"]
    if state not in ("mounted_driving", "mounted_idle"):
        continue  # skip desk/handheld/etc.
    sub = df[df["trip_id"] == trip["trip_id"]]
    # ... vos analytics
```
