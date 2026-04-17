# Quickstart

Get from zero to a validated Telemachus dataset in a few minutes.

## Install

Python 3.10+ :

```bash
pip install telemachus
```

This ships the library (`import telemachus`), the `tele` CLI, and every
adapter (AEGIS, PVS, STRIDE). Schema validation is built-in — no `ajv`
or external tool needed.

## Try it — 5-minute demo

The easiest way to see Telemachus in action is the
[AEGIS demo notebook](notebooks/aegis-demo.ipynb). It downloads a real
open dataset from Zenodo, loads it, and plots one trip. Runnable in
Colab in one click.

## Read a dataset

```python
import telemachus as tele

df = tele.read("path/to/manifest.yaml")   # or directly to a .parquet
print(f"{len(df):,} rows, {df['trip_id'].nunique()} trips, "
      f"profile = {tele.sensor_profile(df)}")
```

`tele.read()` returns a regular pandas DataFrame with SI units and
UTC-aware timestamps — no wrapper, no hidden state.

## Validate a dataset

```bash
tele validate path/to/dataset/ --level full
```

Or from Python:

```python
report = tele.validate(df, profile="full")  # core | imu | full
print(report)
# ValidationReport(PASS, profile=full, level=basic, errors=0, warnings=0)
```

## Convert an open dataset

```bash
tele convert aegis  /path/to/aegis/csvs      -o datasets/aegis/
tele convert stride /path/to/stride/road_data -o datasets/stride/ --category driving
tele convert pvs    /path/to/pvs/trips        -o datasets/pvs/    --placement dashboard
```

## Next steps

- [Validating files](guide/validating.md) — strict and lenient modes
- [Reading Telemachus data](guide/reading-data.md) — Python, DuckDB, pandas
- [Writing an adapter](guide/writing-adapter.md) — convert vendor X → Telemachus
- [Manifest FAQ](guide/manifest-faq.md) — what SPEC-02 changes
- [Concepts](concepts.md) — record format and profiles
