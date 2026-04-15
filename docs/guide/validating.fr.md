# Valider un fichier

Un dataset Telemachus a deux niveaux de validité :

1. **Le signal** (parquet) respecte le contrat colonnes D0 (RFC-0013).
2. **Le manifest** (`manifest.yaml`) respecte le schéma de manifest dataset (RFC-0014).

Les deux contrôles sont indépendants et peuvent être lancés séparément.

## Valider un payload Core (JSON par message)

Utilisez le JSON Schema avec n'importe quel validateur compatible
Draft-07 (`ajv` ici) :

```bash
ajv validate \
  -s spec/schemas/telemachus_core_v0.2.json \
  -d "vos_payloads/*.json"
```

Ce qui est attrapé :

- Clés requises manquantes (`timestamp`, `vehicle_id`, `position`)
- Valeurs hors-bornes (lat hors ±90°, vitesse négative)
- Clés top-level inconnues (le schéma est `additionalProperties: false`)
- Énumérations invalides (ex. `fix_type` inconnu)

## Valider un manifest dataset (RFC-0014)

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/votre-dataset/manifest.yaml
```

!!! tip "YAML vs JSON"
    `ajv` lit nativement JSON. Pour valider un manifest YAML, soit
    pré-convertir (`yq -o=json . manifest.yaml | ajv ...`), soit
    utiliser un validateur Python qui lit YAML directement
    (`jsonschema` + `pyyaml`).

Alternative Python :

```python
import json, yaml, jsonschema

with open("spec/schemas/telemachus_manifest_v0.8.json") as f:
    schema = json.load(f)
with open("datasets/votre-dataset/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

# Coercion datetime → str (ISO-8601)
from datetime import datetime, date
def coerce(v):
    if isinstance(v, dict): return {k: coerce(x) for k,x in v.items()}
    if isinstance(v, list): return [coerce(x) for x in v]
    if isinstance(v, (datetime, date)): return v.isoformat()
    return v

jsonschema.validate(coerce(manifest), schema)
print("OK")
```

## Valider le parquet contre D0

Il n'y a pas encore de CLI canonique (prévue dans la suite de
conformité 1.0). Les contrôles minimaux à la main :

```python
import pandas as pd
df = pd.read_parquet("d0.parquet")

REQUIS = ["ts", "lat", "lon", "speed_mps",
          "ax_mps2", "ay_mps2", "az_mps2"]
manquants = [c for c in REQUIS if c not in df.columns]
assert not manquants, f"colonnes manquantes : {manquants}"

assert df["ts"].is_monotonic_increasing, "ts doit être monotone"
assert df["lat"].dropna().between(-90, 90).all()
assert df["lon"].dropna().between(-180, 180).all()
```

Pour les contrôles gravité par AccPeriod (RFC-0013 §6 règle 3), voir
[Concepts → AccPeriod](../concepts.md#accperiod-le-referentiel-de-laccelerometre).

## Strict vs tolérant

Les schémas actuels sont **stricts** : champ requis manquant → rejet.
Le tooling futur proposera un mode `--lenient` qui dégradera les
violations en warnings, utile pour découvrir quels fichiers legacy ne
sont pas conformes sans casser le pipeline.
