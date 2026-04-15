# RFCs

The normative specification lives in [`spec/rfcs/`](https://github.com/telemachus3/telemachus/tree/main/spec/rfcs) of the monorepo. Each RFC is a versioned, peer-reviewable proposal.

## Index

| RFC | Title | Status |
|-----|-------|--------|
| [RFC-0001](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0001-telemachus-core-0.2.md) | Telemachus Core (v0.2) | Released |
| [RFC-0002](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0002-comparative-apis.md) | Comparative APIs | Informational |
| [RFC-0003](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0003-dataset-specification-0.2.md) | Dataset Specification | Released |
| [RFC-0004](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0004-extended-fieldgroups-schema.md) | Extended FieldGroups | Released |
| [RFC-0005](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0005%E2%80%93adapter-architecture.md) | Adapter Architecture | Released |
| [RFC-0007](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0007-validation-framework-and-cli-rules.md) | Validation Framework & CLI Rules | Released |
| [RFC-0009](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0009-rs3-integration-pipeline.md) | RoadSimulator3 Integration Pipeline | Released |
| [RFC-0011](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0011-versioning-and-governance-policy.md) | Versioning & Governance Policy | Released |
| [RFC-0013](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0013-d0-device-layer.md) | Telemachus Device Format (v0.7) | Released |
| [RFC-0014](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0014-dataset-manifest-0.8.md) | Dataset Manifest (v0.8) | **Draft** |

## How to propose an RFC

1. Open an issue on the [monorepo](https://github.com/telemachus3/telemachus/issues) describing the problem and your proposed direction.
2. Once the direction is endorsed, open a PR adding `spec/rfcs/RFC-NNNN-<slug>.md` following the existing template.
3. Discussion happens on the PR. The RFC is `Draft` until merged and announced.
4. Schemas (`spec/schemas/*.json`) and CHANGELOG entries are updated in the same PR.

The full process is RFC-0011.

## Versioning

Telemachus follows semantic versioning at the **specification** level:

- **Major** : breaking change to the data model.
- **Minor** : new RFC adding fields or layers (current 0.x cadence).
- **Patch** : clarifications, doc fixes, no schema change.

Each manifest declares its `schema_version: "telemachus-X.Y"`. Consumers should reject unknown major versions and warn on unknown minors.
