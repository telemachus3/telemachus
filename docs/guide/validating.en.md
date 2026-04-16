# Validating files

A Telemachus dataset has two layers of validity:

1. **The signal** (parquet) conforms to the Telemachus column contract (SPEC-01).
2. **The manifest** (`manifest.yaml`) conforms to the dataset manifest schema (SPEC-02).

## CLI validation

```bash
# Validate a complete dataset (manifest + parquet)
tele validate path/to/dataset/ --level full

# Validate a manifest only
tele validate path/to/manifest.yaml

# Quick check on a single parquet file
tele validate path/to/data.parquet --level basic

# Dataset info
tele info path/to/manifest.yaml
```

## Python API validation

```python
import telemachus as tele

# Validate a DataFrame
df = tele.read("path/to/manifest.yaml")
report = tele.validate(df, profile="imu")
print(report)
# ValidationReport(PASS, profile=imu, level=basic, errors=0, warnings=0)

# Validate a manifest file
report = tele.validate_manifest("path/to/manifest.yaml")

# Validate a complete dataset (manifest + parquet)
report = tele.validate_dataset("path/to/dataset/", level="full")
```

## Validation levels

| Level | Checks | Use case |
|-------|--------|----------|
| `basic` | Mandatory columns for declared profile, correct types, value ranges | Quick conformance |
| `strict` | All of `basic` + monotonic ts, AccPeriod gravity check | Research-grade |
| `manifest` | SPEC-02 rules (required fields, acc_periods, sensor config) | Manifest-only |
| `full` | `strict` + `manifest` + cross-validation | Publication-ready |

## Profiles

Validation adapts to the declared profile (SPEC-01 §2.2):

| Profile | Required columns |
|---------|-----------------|
| `core` | ts, lat, lon, speed_mps |
| `imu` | core + ax_mps2, ay_mps2, az_mps2 |
| `full` | imu + gx_rad_s, gy_rad_s, gz_rad_s |

If no profile is declared, the validator assumes `imu` (default).

## Manifest validation with JSON Schema

For programmatic manifest validation against the JSON Schema:

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/your-dataset/manifest.yaml
```

!!! tip "YAML vs JSON"
    `ajv` natively reads JSON. To validate a YAML manifest, pre-convert
    with `yq -o=json . manifest.yaml | ajv ...` or use the Python
    validator (`tele.validate_manifest()`) which reads YAML directly.

## What the validator checks

Based on SPEC-01 §3 validation rules:

1. Mandatory columns present for the declared profile
2. `ts` monotonically increasing
3. AccPeriod gravity frame consistency (profiles `imu`/`full`)
4. `lat`/`lon` within [-90,90] / [-180,180]
5. `heading_deg` within [0, 360)
6. `speed_mps` >= 0
7. No excluded columns (SPEC-01 §2.13)
8. Extra columns follow `x_<source>_<field>` convention
9. All present columns have correct data types
10. Gyro/magneto columns: all-or-nothing (no partial group)
11. `device_id`/`trip_id` resolvable from manifest if absent
