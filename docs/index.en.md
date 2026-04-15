---
hide:
  - navigation
  - toc
---

# Telemachus

**Open RFC-driven pivot standard for high-frequency mobility and telematics data.**

Telemachus bridges simulated data (RoadSimulator3) and real-world fleet
sources (Webfleet, Samsara, Geotab, Teltonika) under a unified, open
schema — so analytics pipelines, calibration tools and reference
datasets all speak the same language.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quickstart**

    ---

    Install, validate your first file, ingest a sample dataset.

    [:octicons-arrow-right-24: Get started](quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Guide**

    ---

    How-to articles for validating, reading and adapting Telemachus data.

    [:octicons-arrow-right-24: Read the guide](guide/validating.md)

-   :material-graph:{ .lg .middle } **Concepts**

    ---

    The layered D0 → D1 → D2 model, AccPeriod, CarrierState, multi-rate.

    [:octicons-arrow-right-24: Learn the concepts](concepts.md)

-   :material-file-document-multiple:{ .lg .middle } **RFCs**

    ---

    The normative specification — versioned, peer-reviewed, MIT.

    [:octicons-arrow-right-24: Browse RFCs](rfcs.md)

</div>

## Why Telemachus?

- **Vendor-agnostic** — one schema for IMU, GNSS, motion, OBD, events.
- **Layered** — D0 (raw device) → D1 (cleaned + contextualised) → D2 (events).
- **Reproducible** — every dataset ships with a normative `manifest.yaml` (RFC-0014).
- **Open** — MIT-licensed schemas, reference adapters and Python tools.

## At a glance

| Artifact | Version |
|----------|---------|
| Latest released spec | **v0.2** (2025-10-13) — stable core schema |
| Latest draft | **v0.8** — Telemachus Device Format (RFC-0013) + Dataset Manifest (RFC-0014) |

Telemachus is hosted as a single [monorepo on GitHub](https://github.com/telemachus3/telemachus).
The four legacy repositories (`telemachus-spec`, `telemachus-py`,
`telemachus-cli`, `telemachus-datasets`) have been consolidated and
archived; their full git history is preserved under `spec/`,
`python-sdk/`, `python-cli/` and `datasets/` respectively.
