# Lire des données D0

Sur disque, un dataset D0 Telemachus ressemble à ça :

```
mon-dataset/
├── manifest.yaml          ← RFC-0014 : device, trip, sensors, acc_periods…
├── d0_<id_1>.parquet      ← signal, colonnaire
├── d0_<id_2>.parquet
└── …
```

Le parquet de signal est volontairement « pur » : uniquement les
colonnes définies par RFC-0013 §3 (`ts`, `lat`, `lon`, `speed_mps`,
`ax/ay/az_mps2`, gyro optionnel, GNSS metadata recommandés).

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

# Hériter le device_id depuis le manifest si la colonne manque
# (inheritance rule, RFC-0014 §4.1)
if "device_id" not in df.columns:
    devices = manifest.get("hardware", {}).get("devices", [])
    if len(devices) == 1:
        df["device_id"] = devices[0]["name"]

# Tagger chaque ligne avec son frame accéléromètre (§4.2)
def frame_for(ts):
    for p in manifest.get("acc_periods", []):
        if pd.Timestamp(p["start"]) <= ts <= pd.Timestamp(p["end"]):
            return p["frame"]
    return "raw"  # défaut

df["acc_frame"] = pd.to_datetime(df["ts"]).apply(frame_for)
```

## Avec DuckDB

DuckDB lit le parquet nativement et brille pour l'exploration
ad-hoc :

```python
import duckdb
con = duckdb.connect()
con.sql("SELECT * FROM 'mon-dataset/d0_*.parquet' LIMIT 5").show()
con.sql("""
    SELECT
        date_trunc('minute', ts) AS minute,
        AVG(speed_mps) AS v_moy,
        COUNT(*) AS n
    FROM 'mon-dataset/d0_*.parquet'
    GROUP BY 1 ORDER BY 1
""").show()
```

## Piège du multi-rate

Les fichiers D0 sont timestampés au **rythme IMU** (souvent 10 Hz).
Les colonnes GNSS (`lat`, `lon`, `speed_mps`, `heading_deg`) valent
`NaN` sur les lignes sans fix GPS.

Pour calculer des métriques ligne à ligne, il faut donc enlever les
NaN explicitement :

```python
gnss = df.dropna(subset=["lat", "lon"])
imu = df  # toutes les lignes ont l'IMU
```

Plus de détails dans [Concepts → Multi-rate](../concepts.md#multi-rate-imu-gnss).

## Itérer par trip

Si le manifest déclare `trip_carrier_states`, on peut boucler sur
les trips en filtrant sur `is_vehicle_data` :

```python
for trip in manifest.get("trip_carrier_states", []):
    etat = trip["carrier_state"]
    if etat not in ("mounted_driving", "mounted_idle"):
        continue  # on saute desk / handheld / etc.
    sub = df[df["trip_id"] == trip["trip_id"]]
    # … votre analyse ici
```
