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

    Articles pratiques pour valider, lire et adapter des données Telemachus.

    [:octicons-arrow-right-24: Lire le guide](guide/validating.md)

-   :material-graph:{ .lg .middle } **Concepts**

    ---

    Le modèle en couches Telemachus record format, AccPeriod, CarrierState, multi-rate.

    [:octicons-arrow-right-24: Comprendre](concepts.md)

-   :material-file-document-multiple:{ .lg .middle } **RFCs**

    ---

    La spécification normative, versionnée et revue sous licence MIT.

    [:octicons-arrow-right-24: Parcourir les RFCs](rfcs.md)

</div>

## Ce que Telemachus apporte

- **Neutralité fabricant** : un seul schéma pour l'IMU, le GNSS, le mouvement, l'OBD et les événements.
- **Modèle en couches** : Telemachus (sortie device brute) → enriched (nettoyé et contextualisé) → events layer (événements).
- **Reproductibilité** : chaque dataset embarque un `manifest.yaml` normatif (SPEC-02).
- **Ouverture** : schémas, adapters de référence et outils Python sous licence MIT.

## Où Telemachus se place dans l'écosystème télématique

Les fournisseurs se répartissent grossièrement en deux familles :

| Type de fournisseur | Exemples | Ce qu'ils émettent |
|---------------------|----------|---------------------|
| **Fabricants de boîtiers** (installés dans le véhicule) | Danlaw, Teltonika, Queclink | Sortie device brute → naturellement **Telemachus** |
| **Fournisseurs de services** (SaaS au-dessus d'un ou plusieurs boîtiers) | Geotab, Samsara, Webfleet, Verizon Connect | Données nettoyées et enrichies → naturellement **enriched** / **events layer** |

Telemachus est la **langue commune** entre ces deux familles. Un
constructeur peut publier un adapter qui projette son flux en Telemachus. Un
opérateur de services peut soit consommer du Telemachus (et émettre son
propre enriched/events layer), soit publier directement ses adapters vers enriched/events layer.
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
| Dernière spec publiée | **v0.8** (2026-04-16) — 4 piliers SPEC |
| Dernier brouillon | **v0.8** — Telemachus Record Format (SPEC-01) + Dataset Manifest (SPEC-02) |

Telemachus est hébergé dans un unique [monorepo GitHub](https://github.com/telemachus3/telemachus).
Les 4 anciens dépôts (`telemachus-spec`, `telemachus-py`,
`telemachus-cli`, `telemachus-datasets`) ont été regroupés et
archivés ; leur historique git reste accessible sous `spec/`,
`python-sdk/`, `python-cli/` et `datasets/`.
