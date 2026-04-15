---
hide:
  - navigation
  - toc
---

# Telemachus

**Un standard ouvert pour les données de mobilité et de télématique haute fréquence, guidé par un processus RFC.**

Telemachus sert de pont entre les données simulées (RoadSimulator3)
et les sources de flottes réelles (Webfleet, Samsara, Geotab,
Teltonika). Un seul schéma, une seule manière de lire, quelle que
soit l'origine : vos pipelines d'analyse, vos outils de calibration
et vos datasets de référence parlent enfin la même langue.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Démarrage rapide**

    ---

    Installer, valider votre premier fichier, charger un dataset exemple.

    [:octicons-arrow-right-24: Commencer](quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Guide**

    ---

    Articles pratiques pour valider, lire et adapter des données D0.

    [:octicons-arrow-right-24: Lire le guide](guide/validating.md)

-   :material-graph:{ .lg .middle } **Concepts**

    ---

    Le modèle en couches D0 → D1 → D2, AccPeriod, CarrierState, multi-rate.

    [:octicons-arrow-right-24: Comprendre](concepts.md)

-   :material-file-document-multiple:{ .lg .middle } **RFCs**

    ---

    La spécification normative, versionnée et revue sous licence MIT.

    [:octicons-arrow-right-24: Parcourir les RFCs](rfcs.md)

</div>

## Ce que Telemachus apporte

- **Neutralité fabricant** : un seul schéma pour l'IMU, le GNSS, le mouvement, l'OBD et les événements.
- **Modèle en couches** : D0 (sortie device brute) → D1 (nettoyé et contextualisé) → D2 (événements).
- **Reproductibilité** : chaque dataset embarque un `manifest.yaml` normatif (RFC-0014).
- **Ouverture** : schémas, adapters de référence et outils Python sous licence MIT.

## Où Telemachus se place dans l'écosystème télématique

Les fournisseurs se répartissent grossièrement en deux familles :

| Type de fournisseur | Exemples | Ce qu'ils émettent |
|---------------------|----------|---------------------|
| **Fabricants de boîtiers** (installés dans le véhicule) | Danlaw, Teltonika, Queclink | Sortie device brute → naturellement **D0** |
| **Fournisseurs de services** (SaaS au-dessus d'un ou plusieurs boîtiers) | Geotab, Samsara, Webfleet, Verizon Connect | Données nettoyées et enrichies → naturellement **D1** / **D2** |

Telemachus est la **langue commune** entre ces deux familles. Un
constructeur peut publier un adapter qui projette son flux en D0. Un
opérateur de services peut soit consommer du D0 (et émettre son
propre D1/D2), soit publier directement ses adapters vers D1/D2.
Personne n'a besoin d'apprendre un énième format pour intégrer.

## Pour qui ?

<div class="grid cards" markdown>

-   :material-chart-line:{ .lg .middle } **Data scientists et chercheurs**

    ---

    Vous travaillez sur des logs qui existent déjà. Vous voulez un
    schéma stable pour que votre pipeline pandas ou DuckDB n'ait pas
    à être réécrit à chaque fournisseur. Et vous voulez un accord
    clair sur ce que « vitesse » ou « accélération » signifie, quelle
    que soit la source.

-   :material-memory:{ .lg .middle } **Concepteurs de dataloggers**

    ---

    Vous concevez un device (ou un firmware) qui va produire des
    logs. Vous voulez viser un format déjà accepté par les
    consommateurs en aval, avec un validateur et une suite de tests.

</div>

## Versions

| Artefact | Version |
|----------|---------|
| Dernière spec publiée | **v0.2** (2025-10-13) — schéma cœur stable |
| Dernier brouillon | **v0.8** — Telemachus Device Format (RFC-0013) + Dataset Manifest (RFC-0014) |

Telemachus est hébergé dans un unique [monorepo GitHub](https://github.com/telemachus3/telemachus).
Les 4 anciens dépôts (`telemachus-spec`, `telemachus-py`,
`telemachus-cli`, `telemachus-datasets`) ont été regroupés et
archivés ; leur historique git reste accessible sous `spec/`,
`python-sdk/`, `python-cli/` et `datasets/`.
