# Validating files

A Telemachus dataset has two layers of validity:

1. **The signal** (parquet) conforms to the Telemachus column contract (SPEC-01).
2. **The manifest** (`manifest.yaml`) conforms to the dataset manifest schema (SPEC-02).

Both checks are independent and you can run them separately.

## Validating a Core payload (per-message JSON)

Use the JSON Schema and any Draft-07 compatible validator (`ajv` shown):

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d "your_payloads/*.json"
```

What this catches:

- Missing required keys (`timestamp`, `vehicle_id`, `position`)
- Out-of-range values (lat outside ±90°, speed negative)
- Unknown top-level keys (the schema is `additionalProperties: false`)
- Invalid enum values (e.g. unknown `fix_type`)

## Validating a dataset manifest (SPEC-02)

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/your-dataset/manifest.yaml
```

!!! tip "YAML vs JSON"
    `ajv` natively reads JSON. To validate a YAML manifest you can
    pre-convert it (`yq -o=json . manifest.yaml | ajv ...`) or use a
    Python validator that reads YAML directly (`jsonschema` + `pyyaml`).

A Python alternative:

```python
import json, yaml, jsonschema

with open("spec/schemas/telemachus_manifest_v0.8.json") as f:
    schema = json.load(f)
with open("datasets/your-dataset/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

# datetime → str coercion (ISO-8601)
from datetime import datetime, date
def coerce(v):
    if isinstance(v, dict): return {k: coerce(x) for k,x in v.items()}
    if isinstance(v, list): return [coerce(x) for x in v]
    if isinstance(v, (datetime, date)): return v.isoformat()
    return v

jsonschema.validate(coerce(manifest), schema)
print("OK")
```

## Validating the parquet against Telemachus

There is no canonical CLI yet (planned in the 1.0 conformance suite).
The minimum hand-rolled checks:

```python
import pandas as pd
df = pd.read_parquet("data.parquet")

REQUIRED = ["ts", "lat", "lon", "speed_mps",
            "ax_mps2", "ay_mps2", "az_mps2"]
missing = [c for c in REQUIRED if c not in df.columns]
assert not missing, f"missing columns: {missing}"

assert df["ts"].is_monotonic_increasing, "ts must be monotonic"
assert df["lat"].dropna().between(-90, 90).all()
assert df["lon"].dropna().between(-180, 180).all()
```

For per-AccPeriod gravity checks (SPEC-01 §6 rule 3), see
[Concepts → AccPeriod](../concepts.md#accperiod-the-accelerometer-frame).

## Strict vs lenient

The current schemas are **strict**: missing required field → reject.
Future tooling will offer a `--lenient` mode that downgrades violations
to warnings, useful for discovering which legacy files are non-conformant
without breaking the pipeline.
