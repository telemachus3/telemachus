# À propos et pour aller plus loin

## Ce qu'est Telemachus

Un format de données petit, ouvert, indépendant du fabricant, pour
la mobilité et la télématique haute fréquence. Il fait **une chose,
bien** : définir l'encodage des couches D0 (brute device) puis D1 et
D2 (enrichies), pour que pipelines, datasets et outils parlent la
même langue.

Il ne définit **pas** :

- Quel algorithme calcule les colonnes D1 ou D2
- Quelles métriques constituent une « bonne conduite »
- Quelles décisions business tirer des données

Ça, c'est au consommateur de décider.

## Formats techniques — une spec, trois encodages

Les mêmes données Telemachus peuvent vivre dans trois encodages,
chacun adapté à une famille d'outils différente :

| Encodage | Cas d'usage | Outils |
|----------|-------------|--------|
| **Parquet** (colonnaire) | Analytique bulk, SQL ad-hoc, stockage froid | pandas, DuckDB, Spark, Athena |
| **JSON / JSONL** (document) | Streaming, payloads d'API, files de messages | MongoDB, Kafka, REST |
| **NumPy / Arrow** (mémoire) | Pipelines ML en Python, zero-copy | numpy, pyarrow, PyTorch |

Les trois encodages sont **équivalents en contenu** — le JSON
Schema (`telemachus_core_v0.2.json`) décrit le payload par message,
Parquet encode les mêmes payloads en bulk, NumPy/Arrow est la
représentation en mémoire qu'adoptent pandas et DuckDB. On choisit
selon l'outil, pas selon la sémantique.

Le **manifest dataset** (`manifest.yaml`, RFC-0014) reste toujours
en YAML (ou JSON équivalent) indépendamment de l'encodage du signal,
parce qu'il est fait pour être lu par un humain et qu'il est petit.

## Ce que Telemachus n'est *pas*

- Un produit de scoring
- Un dashboard commercial
- Une bibliothèque de méthodes

Pour la science appliquée (papers, méthodes, benchmarks), direction
le **site recherche compagnon** :
[research.roadsimulator3.fr](https://research.roadsimulator3.fr).

## Projets liés

| Projet | Rôle | Repo / site |
|--------|------|-------------|
| **Telemachus** | Format ouvert + SDK + CLI | ce site / [GitHub](https://github.com/telemachus3/telemachus) |
| **RoadSimulator3** | Générateur D0 synthétique | [github.com/SebE585/RoadSimulator3](https://github.com/SebE585/RoadSimulator3) |
| **Vitrine recherche** | Papers, méthodes, benchmarks | [research.roadsimulator3.fr](https://research.roadsimulator3.fr) |

## Citation

```
S. Edet (2025). Telemachus Specification.
Zenodo. https://doi.org/10.5281/zenodo.17228092
```

## Licence

MIT — s'applique à la spec, aux JSON Schemas, au SDK, à la CLI, aux
exemples d'adapters et à la documentation. Les datasets sous
`datasets/` portent leurs propres licences (CC-BY, CC0, etc.) —
voir le `manifest.yaml` de chaque dataset.

## Contribuer

Toutes les contributions sont bienvenues :

- **Bug dans la spec ?** Ouvrir une issue.
- **Ajouter un adapter pour le fabricant X ?** Une PR sous `python-cli/adapters/`.
- **Proposer une nouvelle RFC ?** Voir [RFCs → Proposer](rfcs.md#proposer-une-nouvelle-rfc).
- **Corriger une typo doc ?** L'icône crayon en haut à droite de chaque page deep-linke vers la source GitHub.
