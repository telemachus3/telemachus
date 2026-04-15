# RFCs

La spécification normative vit dans [`spec/rfcs/`](https://github.com/telemachus3/telemachus/tree/main/spec/rfcs) du monorepo. Chaque RFC est une proposition versionnée et reviewable.

## Index

| RFC | Titre | Statut |
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
| [RFC-0014](https://github.com/telemachus3/telemachus/blob/main/spec/rfcs/RFC-0014-dataset-manifest-0.8.md) | Dataset Manifest (v0.8) | **Brouillon** |

## Comment proposer une RFC

1. Ouvrir une issue sur le [monorepo](https://github.com/telemachus3/telemachus/issues) décrivant le problème et la direction proposée.
2. Une fois la direction endorsée, ouvrir une PR ajoutant `spec/rfcs/RFC-NNNN-<slug>.md` selon le template existant.
3. La discussion a lieu sur la PR. La RFC est `Draft` jusqu'au merge + annonce.
4. Schémas (`spec/schemas/*.json`) et entrées CHANGELOG sont mis à jour dans la même PR.

Le processus complet est RFC-0011.

## Versioning

Telemachus suit semver au niveau **spécification** :

- **Major** : changement cassant du modèle de données.
- **Minor** : nouvelle RFC ajoutant champs ou couches (cadence 0.x actuelle).
- **Patch** : clarifications, fixes doc, pas de changement schéma.

Chaque manifest déclare son `schema_version: "telemachus-X.Y"`. Les consommateurs doivent rejeter les majors inconnus et warner sur les minors inconnus.
