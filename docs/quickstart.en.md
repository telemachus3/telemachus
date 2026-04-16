# Quickstart

Get from zero to a validated Telemachus dataset in a few minutes.

## Install

You'll need Python 3.10+ and `git`.

```bash
git clone https://github.com/telemachus3/telemachus
cd telemachus
pip install -e python-sdk
pip install -e python-cli
```

The CLI also requires [`ajv`](https://ajv.js.org/) for JSON Schema
validation:

```bash
npm install -g ajv-cli
```

## Validate a payload against the core schema

A Telemachus payload is a JSON object describing one telemetry frame
(GNSS + IMU + motion + quality + optional context). Sample payloads
live under `spec/examples/`:

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d "spec/examples/*.json"
```

## Validate a dataset manifest (v0.8 Draft)

A *dataset* is a coherent collection of Telemachus parquet files plus a
sidecar `manifest.yaml` (SPEC-02). The manifest is the canonical
source for `device_id`, `trip_id`, `acc_periods` and
`trip_carrier_states`.

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d path/to/your/manifest.yaml
```

## Read a Telemachus file in Python

```python
import pandas as pd

df = pd.read_parquet("path/to/d0.parquet")
print(df.head())
print(df.columns.tolist())
# ['ts', 'lat', 'lon', 'speed_mps',
#  'ax_mps2', 'ay_mps2', 'az_mps2', ...]
```

For a full read/manifest workflow see [Reading Telemachus data](guide/reading-data.md).

## Next steps

- [Validating files](guide/validating.md) — strict and lenient modes
- [Reading Telemachus data](guide/reading-data.md) — Python, DuckDB, pandas
- [Writing an adapter](guide/writing-adapter.md) — convert vendor X → Telemachus
- [Manifest FAQ](guide/manifest-faq.md) — what SPEC-02 changes
- [Concepts](concepts.md) — the layered model
