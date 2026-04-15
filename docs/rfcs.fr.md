# RFCs

La spécification normative vit sous [`spec/rfcs/`](https://github.com/telemachus3/telemachus/tree/main/spec/rfcs) dans le monorepo. Chaque RFC est une proposition versionnée et reviewable.

## Index

| RFC | Titre | Statut |
|-----|-------|--------|
| [RFC-0001](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0001-telemachus-core-0.2.md) | Telemachus Core (v0.2) | Publié |
| [RFC-0002](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0002-comparative-apis.md) | Comparative APIs | Informationnel |
| [RFC-0003](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0003-dataset-specification-0.2.md) | Dataset Specification | Publié |
| [RFC-0004](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0004-extended-fieldgroups-schema.md) | Extended FieldGroups | Publié |
| [RFC-0005](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0005%E2%80%93adapter-architecture.md) | Adapter Architecture | Publié |
| [RFC-0007](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0007-validation-framework-and-cli-rules.md) | Validation Framework & CLI Rules | Publié |
| [RFC-0009](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0009-rs3-integration-pipeline.md) | RoadSimulator3 Integration Pipeline | Publié |
| [RFC-0011](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0011-versioning-and-governance-policy.md) | Versioning & Governance Policy | Publié |
| [RFC-0013](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0013-d0-device-layer.md) | Telemachus Device Format (v0.7) | Publié |
| [RFC-0014](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0014-dataset-manifest-0.8.md) | Dataset Manifest (v0.8) | **Brouillon** |

## Proposer une nouvelle RFC

1. Ouvrir une issue sur le [monorepo](https://github.com/telemachus3/telemachus/issues) qui décrit le problème et la direction.
2. Si la direction tient la route, ouvrir une PR qui ajoute `spec/rfcs/RFC-NNNN-<slug>.md` en suivant le template des RFCs existantes.
3. La discussion a lieu sur la PR. La RFC reste `Brouillon` jusqu'au merge + annonce.
4. Les schémas (`spec/schemas/*.json`) et le CHANGELOG bougent dans la même PR.

Le process complet est décrit dans RFC-0011.

## Versions

Aucun engagement strict de semver tant que le format est pré-1.0 et
utilisé par une seule équipe. En pratique :

- Une nouvelle RFC qui ajoute des champs ou une couche → bump minor.
- Un changement qui casse les scripts existants → bump major.
- Clarifications et doc → bump patch.

Chaque manifest déclare sa `schema_version: "telemachus-X.Y"`. Les
consommateurs sont encouragés à warner sur une version inconnue,
pas à rejeter brutalement.
