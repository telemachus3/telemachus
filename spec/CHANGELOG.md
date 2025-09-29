


# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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