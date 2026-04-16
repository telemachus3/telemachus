# Démarrage rapide

De zéro à un dataset Telemachus validé, en quelques minutes.

## Installation

Il vous faut Python 3.10+ et `git`.

```bash
git clone https://github.com/telemachus3/telemachus
cd telemachus
pip install -e python-sdk
pip install -e python-cli
```

La CLI s'appuie aussi sur [`ajv`](https://ajv.js.org/) pour la
validation JSON Schema :

```bash
npm install -g ajv-cli
```

## Valider un payload contre le schéma cœur

Un payload Telemachus, c'est un objet JSON qui décrit une trame de
télémétrie (GNSS + IMU + mouvement + qualité + contexte optionnel).
Des exemples vivent sous `spec/examples/` :

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d "spec/examples/*.json"
```

## Valider un manifest de dataset (v0.8 brouillon)

Un *dataset*, ce sont un ou plusieurs fichiers parquet Telemachus accompagnés
d'un `manifest.yaml` sidecar (SPEC-02). Le manifest est la source
d'autorité pour `device_id`, `trip_id`, `acc_periods` et
`trip_carrier_states`.

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d chemin/vers/votre/manifest.yaml
```

## Lire un fichier Telemachus en Python

```python
import pandas as pd

df = pd.read_parquet("chemin/vers/data.parquet")
print(df.head())
print(df.columns.tolist())
# ['ts', 'lat', 'lon', 'speed_mps',
#  'ax_mps2', 'ay_mps2', 'az_mps2', ...]
```

Pour un workflow complet (lecture + manifest + héritage), voir
[Lire des données Telemachus](guide/reading-data.md).

## Et ensuite ?

- [Valider un fichier](guide/validating.md) — modes strict et tolérant
- [Lire des données Telemachus](guide/reading-data.md) — Python, DuckDB, pandas
- [Écrire un adapter](guide/writing-adapter.md) — convertir un format X vers Telemachus
- [FAQ Manifest](guide/manifest-faq.md) — ce que SPEC-02 apporte concrètement
- [Concepts](concepts.md) — le modèle en couches et les groupes fonctionnels
