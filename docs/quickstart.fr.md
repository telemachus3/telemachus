# Démarrage rapide

De zéro à un dataset Telemachus validé, en quelques minutes.

## Installation

Python 3.10+ :

```bash
pip install telemachus
```

Ça livre la bibliothèque (`import telemachus`), la CLI `tele`, et
tous les adapters (AEGIS, PVS, STRIDE). La validation de schéma est
intégrée — pas besoin de `ajv` ni d'outil externe.

## Essayer — démo 5 minutes

Le plus rapide pour voir Telemachus en action : le
[notebook de démo AEGIS](notebooks/aegis-demo.ipynb). Il télécharge un
vrai dataset open depuis Zenodo, le charge, et trace un trajet.
Ouvrable dans Colab en un clic.

## Lire un dataset

```python
import telemachus as tele

df = tele.read("chemin/vers/manifest.yaml")   # ou directement un .parquet
print(f"{len(df):,} lignes, {df['trip_id'].nunique()} trajets, "
      f"profil = {tele.sensor_profile(df)}")
```

`tele.read()` renvoie un pandas DataFrame normal, en unités SI, avec
des timestamps UTC-aware — pas de wrapper, pas d'état caché.

## Valider un dataset

```bash
tele validate chemin/vers/dataset/ --level full
```

Ou depuis Python :

```python
report = tele.validate(df, profile="full")  # core | imu | full
print(report)
# ValidationReport(PASS, profile=full, level=basic, errors=0, warnings=0)
```

## Convertir un dataset Open

```bash
tele convert aegis  /chemin/aegis/csvs         -o datasets/aegis/
tele convert stride /chemin/stride/road_data   -o datasets/stride/ --category driving
tele convert pvs    /chemin/pvs/trips          -o datasets/pvs/    --placement dashboard
```

## Et ensuite ?

- [Valider un fichier](guide/validating.md) — modes strict et tolérant
- [Lire des données Telemachus](guide/reading-data.md) — Python, DuckDB, pandas
- [Écrire un adapter](guide/writing-adapter.md) — convertir un format X vers Telemachus
- [FAQ Manifest](guide/manifest-faq.md) — ce que SPEC-02 apporte
- [Concepts](concepts.md) — format d'enregistrement et profils
