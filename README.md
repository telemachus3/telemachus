[![Docs](https://img.shields.io/badge/docs-online-blue)](https://telemachus3.github.io/telemachus/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

# Telemachus

**Telemachus** is an open RFC-driven pivot standard for high-frequency
mobility and telematics data. It bridges simulated data
(RoadSimulator3) and real-world fleet sources (Webfleet, Samsara,
Geotab, Teltonika) under a unified, open schema.

This repository is the **monorepo** that consolidates the four previous
`telemachus-*` repositories (spec, Python SDK, CLI, datasets) into a
single source of truth.

## Layout

| Directory | What |
|-----------|------|
| [`spec/`](spec/) | RFCs + JSON Schemas — the normative specification |
| [`python-sdk/`](python-sdk/) | Python SDK & validator (`telemachus` package) |
| [`python-cli/`](python-cli/) | CLI tools (`telemachus-cli`, validate / convert / score) |
| [`datasets/`](datasets/) | Reference datasets & manifests (samples + pointers) |

## Versions

| Artifact | Version |
|----------|---------|
| Latest released spec | **v0.2** (2025-10-13) — stable core schema |
| Latest draft | **v0.8** — Telemachus Device Format (RFC-0013) + Dataset Manifest (RFC-0014) |

The v0.8 draft introduces the layered Telemachus processing layers data model, AccPeriod
frame tracking, CarrierState classification, and the normative
**Dataset Manifest** sidecar (RFC-0014).

## Quickstart

### Validate a telemetry payload against the core schema
```bash
ajv validate -s spec/schemas/telemachus_core_v0.2.json -d examples/*.jsonl
```

### Validate a dataset manifest (RFC-0014, v0.8 Draft)
```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json -d path/to/manifest.yaml
```

### Install the Python SDK & CLI (editable)
```bash
pip install -e python-sdk
pip install -e python-cli
```

## CLI examples

```bash
# Validate a file
telemachus validate examples/geotab_example_synthetic.json

# Convert JSON/JSONL directory to Parquet
telemachus to-parquet examples/ -o fleet.parquet

# Compute Completeness Score
telemachus tcs fleet.parquet
```

## RFCs

See [`spec/rfcs/`](spec/rfcs/) for the full list.

| RFC | Title | Status |
|-----|-------|--------|
| RFC-0001 | Core Schema (v0.2) | Released |
| RFC-0003 | Dataset Specification | Released |
| RFC-0004 | Extended FieldGroups | Released |
| RFC-0005 | Adapter Architecture | Released |
| RFC-0007 | Validation Framework | Released |
| RFC-0009 | RoadSimulator3 Integration Pipeline | Released |
| RFC-0011 | Versioning & Governance | Released |
| RFC-0013 | Telemachus Device Format (v0.7) | Released |
| RFC-0014 | Dataset Manifest (v0.8) | Draft |

## History

This monorepo preserves the full Git history of the four source
repositories. Each subdirectory contains the historical commits of
its respective former repo (rewritten via `git filter-repo
--to-subdirectory-filter`).

Former repos (now archived):
- `telemachus-spec` → [`spec/`](spec/)
- `telemachus-py` → [`python-sdk/`](python-sdk/)
- `telemachus-cli` → [`python-cli/`](python-cli/)
- `telemachus-datasets` → [`datasets/`](datasets/)

## Citation

```
S. Edet (2025). Telemachus Specification.
Zenodo. https://doi.org/10.5281/zenodo.17228092
```

## License

MIT — see [`LICENSE`](LICENSE).
