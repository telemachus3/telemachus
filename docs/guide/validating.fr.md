# Valider un fichier

Un dataset Telemachus se valide sur deux plans, qu'on peut
enchaîner ou séparer :

1. **Le signal** (parquet) respecte le contrat de colonnes Telemachus (SPEC-01).
2. **Le manifest** (`manifest.yaml`) respecte le schéma du manifest dataset (SPEC-02).

Les deux contrôles sont indépendants.

## Valider un payload Core (JSON par message)

On utilise le JSON Schema avec n'importe quel validateur Draft-07.
Ici `ajv` :

```bash
ajv validate \
  -s spec/schemas/telemachus_core_v0.2.json \
  -d "vos_payloads/*.json"
```

Ce que la validation attrape :

- Clés requises manquantes (`timestamp`, `vehicle_id`, `position`)
- Valeurs hors bornes (lat en dehors de ±90°, vitesse négative)
- Clés inconnues au top level (le schéma est `additionalProperties: false`)
- Énumérations invalides (ex : `fix_type` inconnu)

## Valider un manifest de dataset (SPEC-02)

```bash
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/votre-dataset/manifest.yaml
```

!!! tip "YAML ou JSON ?"
    `ajv` lit nativement JSON. Pour un manifest YAML, soit on
    pré-convertit (`yq -o=json . manifest.yaml | ajv ...`), soit on
    passe par un validateur Python qui accepte YAML directement
    (`jsonschema` + `pyyaml`).

En Python, la variante qu'on utilise dans nos tests :

```python
import json, yaml, jsonschema
from datetime import datetime, date

with open("spec/schemas/telemachus_manifest_v0.8.json") as f:
    schema = json.load(f)
with open("datasets/votre-dataset/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

# Coercion datetime → str ISO-8601 (YAML auto-parse les dates)
def coerce(v):
    if isinstance(v, dict): return {k: coerce(x) for k,x in v.items()}
    if isinstance(v, list): return [coerce(x) for x in v]
    if isinstance(v, (datetime, date)): return v.isoformat()
    return v

jsonschema.validate(coerce(manifest), schema)
print("OK")
```

## Valider le parquet contre le contrat Telemachus

Pas encore de CLI canonique (c'est prévu dans la suite de conformité
1.0). Les contrôles minimaux à la main :

```python
import pandas as pd
df = pd.read_parquet("d0.parquet")

REQUIS = ["ts", "lat", "lon", "speed_mps",
          "ax_mps2", "ay_mps2", "az_mps2"]
manquants = [c for c in REQUIS if c not in df.columns]
assert not manquants, f"colonnes manquantes : {manquants}"

assert df["ts"].is_monotonic_increasing, "ts doit être croissant"
assert df["lat"].dropna().between(-90, 90).all()
assert df["lon"].dropna().between(-180, 180).all()
```

Pour les contrôles de gravité par AccPeriod (SPEC-01 §6 règle 3),
voir [Concepts → AccPeriod](../concepts.md#accperiod-le-referentiel-de-laccelerometre).

## Strict vs tolérant

Les schémas actuels fonctionnent en mode **strict** : champ requis
absent = rejet immédiat. Le tooling futur proposera un mode
`--lenient` qui rétrograde les violations en warnings, utile pour
identifier quels fichiers legacy ne sont pas conformes sans bloquer
le pipeline.
