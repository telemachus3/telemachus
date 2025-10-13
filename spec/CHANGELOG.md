# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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