# Specifications

La specification normative vit sous [`spec/`](https://github.com/telemachus3/telemachus/tree/main/spec) dans le monorepo. En avril 2026, 10 RFCs ont ete consolidees en 4 piliers SPEC.

## SPECs actuelles (v0.8)

| SPEC | Titre | Perimetre |
|------|-------|-----------|
| [SPEC-01](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-01-record-format.md) | **Telemachus Record Format** | 7 groupes fonctionnels, 3 profils, colonnes, validation, mapping hardware |
| [SPEC-02](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-02-manifest.md) | **Dataset Manifest** | manifest.yaml, capteurs, AccPeriods, CarrierState, heritage |
| [SPEC-03](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-03-adapters-validation.md) | **Adapters & Validation** | Interface adapter, specs AEGIS/PVS/STRIDE, validation, CLI |
| [SPEC-04](https://github.com/telemachus3/telemachus/blob/main/spec/SPEC-04-governance.md) | **Governance & Versioning** | Versioning, checklist release, separation des canaux |

## RFCs archivees

Les anciennes RFCs (0001-0014) sont archivees dans [`spec/rfcs/`](https://github.com/telemachus3/telemachus/tree/main/spec/rfcs) avec des notices de deprecation pointant vers le SPEC correspondant.

## Versions

Aucun engagement strict de semver tant que le format est pre-1.0 et
utilise par une seule equipe. En pratique :

- Une nouvelle SPEC qui ajoute des champs ou un profil : bump minor.
- Un changement qui casse les scripts existants : bump major.
- Clarifications et doc : bump patch.

Chaque manifest declare sa `schema_version: "telemachus-X.Y"`. Les
consommateurs sont encourages a warner sur une version inconnue,
pas a rejeter brutalement.
