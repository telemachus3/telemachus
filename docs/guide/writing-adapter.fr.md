# Écrire un adapter

Un *adapter*, c'est du code qui convertit des données venant d'un
format fabricant (Geotab, Webfleet, Samsara, Teltonika via Flespi…)
vers un dataset Telemachus format (parquet + manifest).

## Structure type

```
mon-adapter/
├── adapter.py        ← lit le format source, émet du Telemachus
├── manifest.yaml     ← décrit le dataset produit
├── README.md         ← ce que fait l'adapter, licence, usage
└── tests/
```

L'adapter reste **votre code, sous votre licence** (typiquement MIT).
Le manifest est **normatif** : il doit valider contre
`spec/schemas/telemachus_manifest_v0.8.json`.

## Adapter minimal

```python
"""adapter.py — convertit <vendor> CSV vers Telemachus Telemachus parquet."""
import pandas as pd
import yaml
from pathlib import Path

def adapt(input_csv: Path, output_dir: Path) -> None:
    df = pd.read_csv(input_csv)

    # Mapper les colonnes vendor vers les noms + unités Telemachus (SPEC-01 §3)
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

## Check-list à cocher

- [ ] Toutes les colonnes obligatoires SPEC-01 §3.1 sont là (ou NaN si le cas est autorisé)
- [ ] Les unités sont en SI (`m/s²`, `rad/s`, `m/s`, degrés WGS84)
- [ ] `ts` est croissant strictement, en UTC
- [ ] `acc_periods` reflète la réalité (`raw` si la gravité est présente dans le signal, `compensated` si le firmware l'a retirée)
- [ ] Le manifest passe la validation contre `telemachus_manifest_v0.8.json`
- [ ] Le parquet produit passe les contrôles Telemachus (voir [Valider](validating.md))

## Piège licence

Votre code adapter peut très bien être en MIT, même si le dataset
source ne l'est pas. **Attention en revanche** : redistribuer le
parquet converti, c'est un autre sujet — c'est la licence du dataset
source qui s'applique. Un dataset en CC-BY-NC-ND, par exemple,
interdit de republier un dérivé. À documenter clairement dans le
README de votre adapter, et ne jamais committer le parquet dérivé
dans ce cas.

Plus de détails dans [FAQ Manifest → Licences](manifest-faq.md#licences-dataset).
