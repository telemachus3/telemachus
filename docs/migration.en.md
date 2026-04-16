# What's new

A pragmatic, not-too-formal log of what changed between versions.
Telemachus is still pre-1.0 and the spec evolves where it needs to —
no strict semver promises, no multi-week review cycles yet. Bump
your consumer code when you want to pick up new features.

## 0.8 Draft — SPEC-02 Dataset Manifest

Non-breaking. Adds the normative `manifest.yaml` sidecar (SPEC-02)
with inheritance rules so you can keep `device_id` / `trip_id` /
`acc_periods` / `trip_carrier_states` out of the parquet signal.

Opt-in: existing 0.7 parquets stay valid. To upgrade a dataset, just
add a `manifest.yaml` next to the parquet. Validator:

```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json \
             -d manifest.yaml
```

Convention added: vendor-specific columns prefixed
`x_<source>_<field>` (e.g. `x_teltonika_ext_voltage_v`). Consumers
ignore them safely.

## 0.7 — SPEC-01 Telemachus Device Format

Introduces the Telemachus / enriched / events layer data model. Formalises AccPeriod
(accelerometer frame tracking) and CarrierState (context
classification per trip).

## 0.2 — Released 2025-10-13

First stable core schema. JSON Schema for per-message payloads, JSON
examples for Geotab and Webfleet.

## How to track changes

- Follow the [GitHub Releases](https://github.com/telemachus3/telemachus/releases) (when tagged)
- Read `CHANGELOG.md` at the monorepo root
- Or just look at recent RFC-NNNN files under `spec/rfcs/`
