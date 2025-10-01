# Dataset 2025-10-01 — v1.0

Premier export **Telemachus 0.1** (simulation RS3, 10 Hz).  
Colonnes principales : `timestamp, lat, lon, altitude_m, speed (m/s), acc_x/y/z (m/s²), gyro_x/y/z (rad/s), event + one-hot (event_infra/behavior/context)`.

## Provenance
- Généré avec RoadSimulator3 (runner.run_simulation2) — export inline.
- Altitude via plugin IGN.
- Voir `dataset.json` pour les métadonnées (vehicle_id/trip_id si fournis).

## Qualité / limites
- Données simulées (pas terrain).
- Événements présents mais non exhaustifs.
- Altitude : service IGN, sans validation externe.

## Chargement
```python
import pandas as pd
df = pd.read_parquet("samples.parquet")  # ou CSV
```

## `2025-10-01-v1.0/dataset.json` (exemple minimal)
```json
{
  "format": "telemachus",
  "version": "0.1",
  "release": "2025-10-01-v1.0",
  "files": {
    "samples_csv": "samples.csv",
    "samples_parquet": "samples.parquet"
  },
  "schema": {
    "hz": 10,
    "units": {
      "speed": "m/s",
      "acc": "m/s^2",
      "gyro": "rad/s",
      "altitude": "m"
    }
  },
  "provenance": {
    "generator": "RoadSimulator3",
    "altitude": "plugin-altitude-ign"
  },
  "vehicle_id": "VL-HN-01",
  "trip_id": "HN-20251001_090550"
}