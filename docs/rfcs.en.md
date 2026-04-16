# Specifications

The normative specification lives in [`spec/`](https://github.com/telemachus3/telemachus/tree/main/spec) of the monorepo. In April 2026, 10 RFCs were consolidated into 4 SPEC pillars.

## Current SPECs (v0.8)

| SPEC | Title | Scope |
|------|-------|-------|
| [SPEC-01](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-01-record-format.md) | **Telemachus Record Format** | 7 functional groups, 3 profiles, column definitions, validation rules, hardware mapping |
| [SPEC-02](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-02-manifest.md) | **Dataset Manifest** | manifest.yaml schema, sensors, AccPeriods, CarrierState, inheritance rules |
| [SPEC-03](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-03-adapters-validation.md) | **Adapters & Validation** | Adapter interface, Open dataset specs (AEGIS/PVS/STRIDE), validation framework, CLI |
| [SPEC-04](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-04-governance.md) | **Governance & Versioning** | Versioning model, release checklist, channel separation |

## Archived RFCs

Previous RFCs (0001-0014) are archived in [`spec/rfcs/`](https://github.com/telemachus3/telemachus/tree/main/spec/rfcs) with deprecation notices pointing to the corresponding SPEC.

## Versioning

Telemachus follows pragmatic versioning at the **specification** level:

- **Major** : breaking change to the data model.
- **Minor** : new columns, profiles, or adapters.
- **Patch** : clarifications, doc fixes, no schema change.

Each manifest declares its `schema_version: "telemachus-X.Y"`. Consumers should reject unknown major versions and warn on unknown minors.
