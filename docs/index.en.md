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

## Where Telemachus fits in the telematics stack

Telemetry providers split roughly in two tiers:

| Provider type | Examples | What they emit |
|---------------|----------|----------------|
| **Hardware vendors** (black boxes on the vehicle) | Danlaw, Teltonika, Queclink | Raw device output → natural **D0** |
| **Service providers** (SaaS on top of one or more boxes) | Geotab, Samsara, Webfleet, Verizon Connect | Cleaned & enriched data → natural **D1** / **D2** |

Telemachus is the **common language** between those tiers. A
hardware vendor can publish an adapter that maps its feed to D0. A
service provider can publish adapters that map to D1/D2 — or consume
D0 from any vendor and emit its own D1/D2. No one has to learn
another format to integrate.

## Who is this for?

<div class="grid cards" markdown>

-   :material-chart-line:{ .lg .middle } **Data scientists & researchers**

    ---

    Working on logs that already exist. You want a consistent schema
    so your pandas/DuckDB pipeline doesn't need to be rewritten for
    each vendor. You want a shared understanding of what "speed" or
    "acceleration" means across sources.

-   :material-memory:{ .lg .middle } **Datalogger designers**

    ---

    Building a device (or firmware) that will produce logs. You want
    a target format that's already accepted downstream — and has a
    validator and a test suite.

</div>

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
