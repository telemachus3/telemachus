# À propos & pour aller plus loin

## Ce qu'est Telemachus

Un format de données petit, ouvert, indépendant du fabricant pour la
mobilité et la télématique haute fréquence. Il fait **une chose
bien** : définir comment la sortie device brute (D0) et ses couches
enrichies aval (D1, D2) sont encodées, pour que pipelines, datasets
et outils interopèrent.

Il ne définit **pas** :

- Quel algorithme calcule les colonnes D1/D2
- Quelles métriques constituent une « bonne conduite »
- Quelles décisions business prendre à partir des données

Ça appartient au consommateur.

## Ce que Telemachus n'est *pas*

- Un produit de scoring
- Un dashboard commercial
- Une bibliothèque de méthodes

Pour la science appliquée (papers, méthodes, benchmarks), voir le
**site research compagnon** :
[research.roadsimulator3.fr](https://research.roadsimulator3.fr).

## Typologie des projets liés

| Projet | Rôle | Repo / site |
|--------|------|-------------|
| **Telemachus** | Format de données ouvert & SDK & CLI | ce site / [GitHub](https://github.com/telemachus3/telemachus) |
| **RoadSimulator3** | Générateur D0 synthétique (simulation) | [github.com/SebE585/RoadSimulator3](https://github.com/SebE585/RoadSimulator3) |
| **Vitrine recherche** | Papers, méthodes, benchmarks | [research.roadsimulator3.fr](https://research.roadsimulator3.fr) |

## Citation

```
S. Edet (2025). Telemachus Specification.
Zenodo. https://doi.org/10.5281/zenodo.17228092
```

## Licence

MIT — s'applique à la spec, aux JSON Schemas, au SDK, à la CLI, aux
exemples d'adapters et à la documentation. Les datasets livrés sous
`datasets/` portent leurs propres licences (CC-BY, CC0, etc.) —
voir le `manifest.yaml` de chaque dataset.

## Contribuer

Toutes contributions bienvenues :

- **Bug dans la spec ?** Ouvrir une issue.
- **Ajouter un adapter pour le fabricant X ?** PR sous `python-cli/adapters/`.
- **Proposer une nouvelle RFC ?** Voir [RFCs → Comment proposer](rfcs.md#comment-proposer-une-rfc).
- **Corriger une typo doc ?** Utiliser l'icône crayon en haut à droite de n'importe quelle page (deep-link vers la source GitHub).
