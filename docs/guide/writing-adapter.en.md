# Writing an adapter

An *adapter* converts data from a vendor format (Geotab, Webfleet,
Samsara, Teltonika via Flespi, etc.) into a Telemachus Telemachus dataset
(parquet + manifest).

## Anatomy

```
my-adapter/
├── adapter.py        ← reads source format, emits D0
├── manifest.yaml     ← describes the resulting dataset
├── README.md         ← what the adapter does, license, usage
└── tests/
```

The adapter is **your code, under your license** (typically MIT).
The manifest is **normative** (validates against
`spec/schemas/telemachus_manifest_v0.8.json`).

## Minimal adapter

```python
"""adapter.py — convert <vendor> CSV → Telemachus Telemachus parquet."""
import pandas as pd
import yaml
from pathlib import Path

def adapt(input_csv: Path, output_dir: Path) -> None:
    df = pd.read_csv(input_csv)

    # Map vendor columns → Telemachus column names + units (RFC-0013 §3)
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
            "citation": "Vendor X dataset",
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

- [ ] All RFC-0013 §3.1 mandatory columns present (or NaN where allowed)
- [ ] Units converted to SI (`m/s²`, `rad/s`, `m/s`, degrees WGS84)
- [ ] `ts` monotonically increasing, UTC
- [ ] `acc_periods` declared correctly (`raw` if device emits gravity, `compensated` if firmware-stripped)
- [ ] Manifest validates against `telemachus_manifest_v0.8.json`
- [ ] Resulting parquet validates against D0 contract (see [Validating](validating.md))

## Licensing pitfall

Your adapter code can be MIT regardless of the source dataset's
license. **But** redistributing the converted parquet is bound by the
*source dataset's* license — for example a CC-BY-NC-ND source forbids
republishing derivatives. Document this clearly in your adapter
README and never commit derived parquet under a restrictive source.

See [Manifest FAQ → Licenses](manifest-faq.md#dataset-licenses).
