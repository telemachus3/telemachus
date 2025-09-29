[![Docs](https://img.shields.io/badge/docs-online-blue)](https://telemachus3.github.io/telemachus-spec/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)
# Telemachus Core Specification

**Telemachus Core** is an open pivot format for telematics data.  
It unifies fragmented data from providers (Geotab, Webfleet, Samsara…) into a single, open, machine-readable schema.

## Vision
- 📡 Cover GNSS, CAN/engine, IMU, and driving events.
- 🌍 Allow context enrichments (topography, weather, road genome).
- ⚖️ Separate **Core (open, MIT)** vs **Fleet Premium (proprietary KPIs)**.
- 🔬 Provide a neutral standard, like GTFS for public transport, but for telematics B2B.

## Quickstart
Validate example data against the schema:

```bash
# install ajv-cli (npm install -g ajv-cli) or use docker image later
ajv validate -s schemas/telemachus.schema.json -d examples/*.jsonl
```

## Repositories
- telemachus-py – Python SDK
- telemachus-cli – CLI tool

## Citation
If you use Telemachus in research or projects, please cite:

S. Edet (2025). *Telemachus Core Specification (v0.1-alpha)*.  
Zenodo. https://doi.org/10.5281/zenodo.17228092

## Roadmap & Changelog
- [Roadmap](docs/10_roadmap.md)
- [Changelog](CHANGELOG.md)

## CLI Examples
```bash
# Validate a file
telemachus validate examples/geotab.json

# Convert JSON/JSONL directory to Parquet
telemachus to-parquet examples/ -o fleet.parquet

# Compute Completeness Score
telemachus tcs fleet.parquet
```

## License
MIT