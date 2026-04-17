---
hide:
  - navigation
  - toc
---

# Telemachus

**Open, Parquet-native pivot format for high-frequency telematics data.**

[![PyPI](https://img.shields.io/pypi/v/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Python](https://img.shields.io/pypi/pyversions/telemachus.svg)](https://pypi.org/project/telemachus/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19609019.svg)](https://doi.org/10.5281/zenodo.19609019)
[![License: MIT (spec) / AGPL-3.0 (SDK)](https://img.shields.io/badge/license-MIT%20%2F%20AGPL--3.0-blue.svg)](https://github.com/telemachus3/telemachus/blob/main/LICENSE)

Telemachus bridges the rigor of scientific kinematics (multi-rate
GNSS+IMU at 10-100 Hz, accelerometer gravity frame tracking) and
scalable fleet analytics (OBD, trip metadata, carrier state) in a
single format -- instantly queryable in Pandas, Spark, DuckDB, or Athena.

```bash
pip install telemachus
```

**Try the [AEGIS demo notebook](notebooks/aegis-demo.ipynb)**
([open in Colab](https://colab.research.google.com/github/telemachus3/telemachus/blob/main/docs/notebooks/aegis-demo.ipynb))
to see the format in action on a real Open dataset in 5 minutes.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quickstart**

    ---

    Install, validate your first file, convert an Open dataset.

    [:octicons-arrow-right-24: Get started](quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Guide**

    ---

    How-to articles for validating, reading, and converting data.

    [:octicons-arrow-right-24: Read the guide](guide/validating.md)

-   :material-graph:{ .lg .middle } **Concepts**

    ---

    Record format, AccPeriod, CarrierState, multi-rate, profiles.

    [:octicons-arrow-right-24: Learn the concepts](concepts.md)

-   :material-file-document-multiple:{ .lg .middle } **Specifications**

    ---

    The normative spec -- 4 pillars, peer-reviewed, MIT.

    [:octicons-arrow-right-24: Browse SPECs](rfcs.md)

</div>

## Why Telemachus?

- **Vendor-agnostic** -- one schema for GNSS, IMU, OBD, I/O, CAN.
- **Profile-based** -- `core` (GPS only), `imu` (+ accelerometer), `full` (+ gyroscope). Not one-size-fits-all.
- **Parquet-native** -- flat columns, SI units, instantly queryable.
- **Reproducible** -- every dataset ships with a normative `manifest.yaml`.
- **Open** -- MIT-licensed schemas, reference adapters and Python tools.

## Why not an existing standard?

| Standard | Raw IMU? | Parquet? | Fleet metadata? | Gap |
|----------|:---:|:---:|:---:|-----|
| **ROS bags** (MCAP) | Yes | No (message stream) | No | Not columnar |
| **Fleet APIs** (Geotab, Samsara) | No | No (JSON REST) | Yes | No raw sensors |
| **IoT** (MQTT, SensorThings) | Transport only | No | No | Protocol, not format |
| **GTFS / MDS** | No | No | Macro only | Scheduling, not kinematics |
| **Telemachus** | **Yes** | **Yes** | **Yes** | -- |

## Who is this for?

<div class="grid cards" markdown>

-   :material-chart-line:{ .lg .middle } **Data scientists & researchers**

    ---

    Working on existing telematics logs. You want a consistent schema
    so your Pandas/DuckDB pipeline doesn't need rewriting per vendor.

-   :material-memory:{ .lg .middle } **Datalogger designers**

    ---

    Building a device or firmware that produces logs. You want a
    target format accepted downstream -- with a validator and test suite.

</div>

## At a glance

| Artifact | Version |
|----------|---------|
| **Current spec** | **v0.8** (2026-04-16) -- 4 SPEC pillars |
| **Python SDK** | **v0.8.0** -- read, validate, convert, introspect |
| **Adapters** | AEGIS, PVS, STRIDE (Open datasets) |

Telemachus is hosted as a single [monorepo on GitHub](https://github.com/telemachus3/telemachus).
