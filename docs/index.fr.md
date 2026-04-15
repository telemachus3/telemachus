---
hide:
  - navigation
  - toc
---

# Telemachus

**Standard ouvert orienté RFC pour les données mobilité et télématique haute fréquence.**

Telemachus fait le pont entre données simulées (RoadSimulator3) et
sources flottes réelles (Webfleet, Samsara, Geotab, Teltonika) sous un
schéma ouvert unifié — afin que pipelines d'analyse, outils de
calibration et datasets de référence parlent la même langue.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Démarrage rapide**

    ---

    Installer, valider votre premier fichier, ingérer un dataset exemple.

    [:octicons-arrow-right-24: Commencer](quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Guide**

    ---

    Articles pratiques pour valider, lire et adapter des données D0.

    [:octicons-arrow-right-24: Lire le guide](guide/validating.md)

-   :material-graph:{ .lg .middle } **Concepts**

    ---

    Le modèle en couches D0 → D1 → D2, AccPeriod, CarrierState, multi-rate.

    [:octicons-arrow-right-24: Comprendre les concepts](concepts.md)

-   :material-file-document-multiple:{ .lg .middle } **RFCs**

    ---

    La spécification normative — versionnée, revue, MIT.

    [:octicons-arrow-right-24: Parcourir les RFCs](rfcs.md)

</div>

## Pourquoi Telemachus ?

- **Indépendant du fabricant** — un seul schéma pour IMU, GNSS, motion, OBD, événements.
- **En couches** — D0 (sortie device brute) → D1 (nettoyé + contextualisé) → D2 (événements).
- **Reproductible** — chaque dataset embarque un `manifest.yaml` normatif (RFC-0014).
- **Ouvert** — schémas, adapters de référence et outils Python sous MIT.

## En un coup d'œil

| Artefact | Version |
|----------|---------|
| Dernière spec publiée | **v0.2** (2025-10-13) — schéma cœur stable |
| Dernier brouillon | **v0.8** — Telemachus Device Format (RFC-0013) + Dataset Manifest (RFC-0014) |

Telemachus est hébergé dans un unique [monorepo GitHub](https://github.com/telemachus3/telemachus).
Les 4 anciens dépôts (`telemachus-spec`, `telemachus-py`,
`telemachus-cli`, `telemachus-datasets`) ont été consolidés et
archivés ; leur historique git complet est préservé sous `spec/`,
`python-sdk/`, `python-cli/` et `datasets/` respectivement.
