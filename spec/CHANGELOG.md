# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.9] - 2026-06-03

Device-frame coverage completion. No breaking change vs. 0.8: every addition is
an optional column, a clarification, or a publication rule.

### Added
- **Sensitive identifiers (SPEC-01 §2.4)** — `device_imei` and `sim_iccid` are now
  *defined* optional fields. A telematics record legitimately carries them for
  operational use; the *publication* policy (SPEC-04) restricts them. In a
  published open dataset they MUST be omitted or anonymized, the opaque
  `device_id` being used instead. Sensitivity is a publication concern, not a
  reason to exclude a field from the format.
- **GNSS quality (SPEC-01 §2.5)** — `pdop`, plus three flags with distinct and
  non-interchangeable roles: `gnss_valid` (per-fix valid bit), `gnss_state`
  (receiver mode), `gnss_fix_status` (fix acquired).
- **Device telemetry & motion state (SPEC-01 §2.9.1)** — slowly-varying status
  reported on heartbeat frames (`moving`, `instant_moving`, battery, GSM…).
  Sparse on the multi-rate timeline; being *persistent states* rather than
  instantaneous measurements, a consumer SHOULD forward-fill them — unlike
  GNSS/IMU, which must not be filled — subject to a TTL beyond which the state
  reverts to NaN.
- **Row accounting (SPEC-02)** — `raw_rows_in` / `rows_out` / `raw_rows_dropped`
  with mandatory `drop_reasons`, so a consumer can audit what an adapter
  discarded upstream. The validator only ever sees the output file.
- **High-rate IMU burst decoding (SPEC-03)** — deterministic timestamp derivation
  for bursts of N samples per frame (`burst_size`, `burst_rate_hz`).

### Changed
- **Coverage rule (SPEC-01)** — every source field MUST map to a standard column,
  a defined-but-sensitive identifier, an `x_<vendor>_<field>` extra, or the
  explicit exclusion list. Nothing is silently lost.
- **Vendor extras** — the `<field>` part MUST be sanitized to `snake_case`. A
  source field that is always empty on a device SHOULD be omitted rather than
  emitted as an all-NaN column.
- **AccPeriod semantics (SPEC-01 §2.12, SPEC-02)** — the frame states only what
  the device firmware did with gravity (`raw` / `compensated` / `partial`).
  Orientation, mounting estimation and rectification are **off-board processing
  (D1+)** and never belong in a Telemachus record or manifest. `residual_g`
  becomes an optional descriptive hint, not a conformance target; a `partial`
  period need only satisfy `0 < |a|_rest < g`.
- **Cellular identifiers** — `gsm_mcc` / `gsm_mnc` / `gsm_operator` are
  quasi-identifiers (they reveal fleet operator and country). In a published open
  dataset they MUST be coarsened or omitted; `gsm_network_type` may be kept.

### Fixed
- Dropping rows solely because the advisory `gnss_valid` flag is false is now
  explicitly **NOT permitted** (SPEC-01 §2.5): some firmwares assert it on only a
  minority of otherwise valid fixes, so the practice discards good positioned data.

---

## [0.8] - 2026-04-15 (Draft)
### Added
- **RFC-0014** : Dataset Manifest — Canonical File-Level Metadata. Promotes the de-facto `manifest.yaml` sidecar format to normative spec. Formalizes `device_id`/`trip_id`/`acc_periods`/`trip_carrier_states` inheritance from manifest to per-row (RFC-0014 §4).
- `schemas/telemachus_manifest_v0.8.json` — JSON Schema Draft-07 implementing RFC-0014. Validated against several production manifests in adapter projects.

### Notes
- No breaking change vs. 0.7. Existing per-row `device_id`/`trip_id` columns remain valid; the manifest becomes the authoritative source when those columns are absent.
- RFC-0013 §3.6 (AccPeriod) and §3.7 (CarrierState) remain the normative definitions; RFC-0014 hoists their declaration syntax to the dataset manifest.

---

## [0.2] - 2025-10-13
### Added
- Introduction of the **RFC governance model** (RFC-0001 to RFC-0011).
- Core schema upgraded to **Telemachus v0.2**, aligning with RFC-0001.
- New documentation sections: *RFC Index*, *Versioning & Governance*, *Adapter Architecture*, and *Extended FieldGroups*.
- Integration of **RS3 pipeline** (RFC-0009) and **Validation Framework** (RFC-0007).

### Updated
- Documentation restructured with explicit links to all RFCs.
- All schema references and fieldgroups updated for v0.2.
- Context Extensions enriched with *Environmental Impact*, *Urban*, and *Safety* contexts.

### Fixed
- Broken relative links in MkDocs replaced with absolute GitHub URLs.
- Standardization of “Powertrain & Energy” terminology across all docs.

### Governance
- Added version lifecycle and public RFC discussion process (RFC-0011).
- Introduced roadmap alignment with semantic versioning.

---

## [Unreleased]
- Provider mappings expansion (Teltonika, others).
- First implementation of Telemahus Completeness Score (TCS).
- Context extensions (altitude IGN, weather ERA5, road genome).
- CLI `to-parquet` command.
- Python SDK packaging for PyPI.

---

## [0.1-alpha] - 2025-09-30
### Added
- Initial **Telemachus Core schema** (GNSS, Motion, Quality, IMU, Engine, Events, Context, Source).
- Example files (`geotab.json`, `webfleet.json`, `samsara.json`).
- Documentation site with:
  - Introduction
  - State of the Art
  - Core Specification
  - Examples
  - Provider Mappings
  - Completeness Score (TCS)
  - Context Extensions
  - Versioning Policy
  - Glossary
  - Roadmap
- GitHub Actions workflows:
  - Schema validation (ajv).
  - Automatic documentation deployment (MkDocs + Pages).
- Initial Python SDK skeleton (`telemachus-py`).
- Initial CLI skeleton (`telemachus-cli`).