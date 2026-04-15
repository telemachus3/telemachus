# FAQ Manifest

Questions courantes sur le **Dataset Manifest** (RFC-0014, v0.8 brouillon).

## Pourquoi un manifest ?

Le contrat D0 (RFC-0013 §3.1) déclare `device_id`, `trip_id`,
`acc_periods` et `trip_carrier_states` comme **par-fichier** plutôt
que par-ligne. Ces infos doivent vivre quelque part. Avant RFC-0014,
les producteurs les émettaient ad-hoc (variable d'env, config,
sidecar JSON…). Le manifest formalise ce sidecar.

## Où est le manifest ?

À côté des parquet :

```
mon-dataset/
├── manifest.yaml      ← ici
├── d0_xxx.parquet
└── d0_yyy.parquet
```

YAML est préféré (lisible). JSON avec le même schéma est aussi
accepté par les validators.

## Héritage — quelles colonnes puis-je omettre du parquet ?

Si le manifest les déclare, vous pouvez omettre :

| Colonne | Source manifest |
|---------|-----------------|
| `device_id` | `hardware.devices[0].name` (dataset mono-device) |
| `trip_id`   | suffixe nom de fichier parquet ou `source.campaign + basename` |
| `carrier_state` | matché par `trip_id` depuis `trip_carrier_states` |

Pour les datasets multi-devices, `device_id` DOIT être soit
par-ligne, soit encodé dans le nom de fichier
(`d0_<device>_*.parquet`). Voir RFC-0014 §4.1.

## Comment le frame accéléromètre est appliqué ?

Pour chaque ligne au timestamp `ts`, le consommateur trouve la
première entrée `acc_periods` où `start ≤ ts ≤ end` et utilise son
`frame` (`raw`, `compensated` ou `partial`). Si pas de `acc_periods`
déclaré, le défaut est `raw` (RFC-0013 §3.6).

## Licences dataset

Le manifest porte `license` (chaîne libre style SPDX) et un
`license_warning` optionnel. Cas courants :

| Licence | Republier modifié | Indice manifest |
|---------|--------------------|-----------------|
| CC-BY-4.0 | ✅ avec attribution | `license: "CC-BY-4.0"` |
| CC-BY-NC-ND-4.0 | ❌ ND interdit dérivés | `license: "CC-BY-NC-ND-4.0"`, `license_warning: "Non-commercial, no derivatives"` |
| CC0 | ✅ tout | `license: "CC0-1.0"` |
| Interne / propriétaire | ❌ | `license: "internal"` |

Le tooling futur ajoutera un champ `license_republish_derivative:
{allowed,forbidden,academic}` plus un linter CI qui refuse de
committer du parquet converti sous une source `forbidden`. Pour
l'instant, c'est appliqué par convention — voir [Écrire un adapter →
Piège licence](writing-adapter.md#piege-licence).

## Et les métadonnées par-ligne qui varient ?

Tout ce qui varie réellement par ligne reste par-ligne dans le
parquet (ex. `lat`, `ax_mps2`). Le manifest est pour les métadonnées
**par-fichier** qui ne varient pas, OU pour les métadonnées
segmentées dans le temps (`acc_periods`, historique config) qui
varient sur des bornes grossières.

## Mon manifest échoue à la validation — où regarder ?

Lancer le validator avec sortie verbose :

```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json \
             -d manifest.yaml --errors=text --all-errors
```

Pièges courants :

- `start: 2025-01-01` (YAML auto-parse en date) → quoter : `"2025-01-01T00:00:00Z"`
- `n_trips: null` est OK — la plupart des compteurs acceptent null pour "inconnu"
- Énumération inconnue pour `hardware.class` (`research|commercial|consumer|prototype|smartphone`)
- Bloc requis manquant : `dataset_id`, `schema_version`, `source`
