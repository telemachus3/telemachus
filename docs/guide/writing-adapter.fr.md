# Écrire un adapter

Un *adapter* convertit des données depuis un format fabricant (Geotab,
Webfleet, Samsara, Teltonika via Flespi, etc.) vers un dataset D0
Telemachus (parquet + manifest).

## Anatomie

```
mon-adapter/
├── adapter.py        ← lit le format source, émet du D0
├── manifest.yaml     ← décrit le dataset résultant
├── README.md         ← ce que fait l'adapter, licence, usage
└── tests/
```

L'adapter est **votre code, sous votre licence** (typiquement MIT).
Le manifest est **normatif** (valide contre
`spec/schemas/telemachus_manifest_v0.8.json`).

## Adapter minimal

```python
"""adapter.py — convertit <vendor> CSV → Telemachus Telemachus parquet."""
import pandas as pd
import yaml
from pathlib import Path

def adapt(input_csv: Path, output_dir: Path) -> None:
    df = pd.read_csv(input_csv)

    # Mapper colonnes vendor → noms + unités D0 (RFC-0013 §3)
    d0 = pd.DataFrame({
        "ts":         pd.to_datetime(df["timestamp"], utc=True),
        "lat":        df["latitude"],
        "lon":        df["longitude"],
        "speed_mps":  df["speed_kmh"] / 3.6,
        "ax_mps2":    df["accel_x_mg"] * 9.80665e-3,
        "ay_mps2":    df["accel_y_mg"] * 9.80665e-3,
        "az_mps2":    df["accel_z_mg"] * 9.80665e-3,
    }).sort_values("ts").reset_index(drop=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    d0.to_parquet(output_dir / "d0.parquet", index=False)

    manifest = {
        "dataset_id": output_dir.name,
        "schema_version": "telemachus-0.8",
        "source": {
            "type": "open_external",
            "citation": "Dataset Vendor X",
        },
        "hardware": {
            "vendor": "VendorX",
            "model": "DeviceY",
            "class": "commercial",
        },
        "sensors": {
            "gps": {"rate_hz": 1},
            "accelerometer": {
                "rate_hz": 10,
                "has_gyroscope": False,
                "unit": "m/s^2",
            },
        },
        "acc_periods": [{
            "start": d0["ts"].min().isoformat(),
            "end":   d0["ts"].max().isoformat(),
            "frame": "raw",
            "detection_method": "user",
        }],
        "data_files": [{"path": "d0.parquet", "format": "parquet"}],
    }
    with open(output_dir / "manifest.yaml", "w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)
```

## Checklist

- [ ] Toutes les colonnes obligatoires RFC-0013 §3.1 présentes (ou NaN si autorisé)
- [ ] Unités converties en SI (`m/s²`, `rad/s`, `m/s`, degrés WGS84)
- [ ] `ts` monotone croissant, UTC
- [ ] `acc_periods` correctement déclarés (`raw` si le device émet la gravité, `compensated` si le firmware la retire)
- [ ] Manifest valide contre `telemachus_manifest_v0.8.json`
- [ ] Parquet résultant valide contre le contrat D0 (voir [Valider](validating.md))

## Piège licence

Votre code adapter peut être en MIT indépendamment de la licence du
dataset source. **Mais** redistribuer le parquet converti est
contraint par la licence du *dataset source* — par exemple une source
CC-BY-NC-ND interdit de republier des dérivés. Documentez-le
clairement dans le README de votre adapter et ne committez jamais de
parquet dérivé sous une source restrictive.

Voir [FAQ Manifest → Licences](manifest-faq.md#licences-dataset).
