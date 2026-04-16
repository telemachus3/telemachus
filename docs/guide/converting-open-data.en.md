# Converting Open data without a ready-made adapter

Sometimes you spot an interesting public dataset (a Zenodo upload, a
Kaggle competition, a Figshare release) that isn't yet represented
under `datasets/` in the monorepo. This page walks through the
manual conversion to a valid Telemachus Telemachus dataset.

## 0. Before you start — check the license

Run the license test from [Writing an adapter →
Licensing pitfall](writing-adapter.md#licensing-pitfall). A
`CC-BY-NC-ND` source forbids republishing derivatives, so you can
ship the **adapter code** but not the **converted parquet**.
Everything that follows assumes you're allowed to keep a local copy
for your analysis.

## 1. Inventory the source

Open the raw files and identify, column by column, what each sensor
stream actually contains:

| Source column | Unit | Rate | Maps to Telemachus format |
|---------------|------|------|------------|
| `timestamp_ms` | ms since epoch | — | `ts` (convert to UTC datetime) |
| `latitude` | deg | 1 Hz | `lat` |
| `longitude` | deg | 1 Hz | `lon` |
| `speed_kmh` | km/h | 1 Hz | `speed_mps` (÷ 3.6) |
| `accel_x_g` | g | 100 Hz | `ax_mps2` (× 9.80665) |
| `accel_y_g` | g | 100 Hz | `ay_mps2` |
| `accel_z_g` | g | 100 Hz | `az_mps2` |
| `gyro_x_dps` | deg/s | 100 Hz | `gx_rad_s` (× π/180) |
| … | | | |

If any expected Telemachus column is missing, plan how you'll handle it:

- **GPS columns absent** at IMU rate → leave as `NaN` (multi-rate convention, SPEC-01 §3.5)
- **Heading missing** → recompute from consecutive GPS points (Haversine bearing)
- **Gyro missing** → simply leave the gyro columns absent (SPEC-01 §3.3: must be absent OR all-NaN, never zero-filled)

## 2. Fetch & unpack

Scripts go in an adapter folder under your working copy, **not
committed** if the license is restrictive:

```bash
mkdir -p datasets/xx_my_source/
cd datasets/xx_my_source/
cat > download.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
mkdir -p raw
curl -sSL -o raw/data.zip "https://example.org/dataset.zip"
cd raw && unzip -q data.zip && cd ..
echo "raw files under datasets/xx_my_source/raw/"
EOF
chmod +x download.sh
```

## 3. Write the adapter

See the full template in [Writing an adapter](writing-adapter.md).
The minimum your adapter must do:

1. Read the raw files (CSV / Parquet / whatever).
2. Rename & convert columns (units!) to the Telemachus names.
3. Sort by `ts`, ensure monotonicity, drop or fix duplicates.
4. Write the Telemachus parquet.
5. Emit a `manifest.yaml` declaring `hardware`, `sensors.*.rate_hz`,
   `acc_periods` (start/end/frame), `source` block, `license`.

## 4. Detect the accelerometer frame

Critical step often forgotten. Run this check on a known stationary
segment (device on a table, vehicle parked + engine off):

```python
import numpy as np, pandas as pd
df = pd.read_parquet("data.parquet")

# Pick a stationary window (first 10 seconds for instance)
rest = df.iloc[:int(10 * 100)]  # 10 s at 100 Hz
a_norm = np.sqrt(rest["ax_mps2"]**2 + rest["ay_mps2"]**2 + rest["az_mps2"]**2)
mean_g = a_norm.mean()
print(f"||a|| at rest: {mean_g:.2f} m/s²")

if mean_g > 8:
    frame = "raw"           # gravity present
elif mean_g < 2:
    frame = "compensated"   # firmware-stripped
else:
    frame = "partial"
print(f"→ frame = {frame}")
```

Put the result in `manifest.yaml` under `acc_periods`:

```yaml
acc_periods:
  - start: 2024-01-01T00:00:00Z
    end:   2024-12-31T23:59:59Z
    frame: raw               # or compensated / partial
    detection_method: auto
    residual_g: 0.0          # only if frame=partial
```

## 5. Validate

Both artefacts must pass:

```bash
# Manifest
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/xx_my_source/manifest.yaml

# Telemachus sanity (no canonical CLI yet)
python -c "
import pandas as pd
df = pd.read_parquet('datasets/xx_my_source/data.parquet')
req = ['ts','lat','lon','speed_mps','ax_mps2','ay_mps2','az_mps2']
assert not [c for c in req if c not in df.columns], 'columns missing'
assert df['ts'].is_monotonic_increasing
print('OK')
"
```

## 6. Submit (optional)

If the license permits redistribution, you can:

1. Open a PR adding your adapter under `python-cli/adapters/`.
2. Add the `manifest.yaml` under `datasets/xx_my_source/`.
3. If the raw volume is < 10 MB, commit the parquet too. Otherwise
   use `git-lfs` for files > 10 MB, or publish the parquet on Zenodo
   and reference it in the manifest.

See [Open sources matrix](open-sources-matrix.md) for the current
coverage to avoid overlap.
