# FAQ Manifest

Questions courantes autour du **Dataset Manifest** (SPEC-02, v0.8 brouillon).

## Pourquoi un manifest ?

Le contrat Telemachus (SPEC-01 §3.1) déclare `device_id`, `trip_id`,
`acc_periods` et `trip_carrier_states` comme des champs
**par-fichier**, pas par-ligne. Il faut bien qu'ils vivent quelque
part. Avant SPEC-02, les producteurs les mettaient un peu où ils
voulaient (variable d'env, fichier de config, sidecar JSON ad-hoc…).
Le manifest normalise ce sidecar.

## Où se trouve le manifest ?

À côté des parquet :

```
mon-dataset/
├── manifest.yaml      ← ici
├── device_xxx.parquet
└── device_yyy.parquet
```

On préfère YAML (plus lisible). JSON avec le même schéma marche
aussi.

## Quelles colonnes peut-on omettre du parquet ?

Si le manifest les déclare, on peut les omettre :

| Colonne | Source dans le manifest |
|---------|--------------------------|
| `device_id` | `hardware.devices[0].name` (dataset mono-device) |
| `trip_id` | Suffixe du nom de parquet, ou `source.campaign + basename` |
| `carrier_state` | Matché sur le `trip_id` via `trip_carrier_states` |

Pour un dataset multi-devices, `device_id` **doit** être soit
présent par ligne, soit encodé dans le nom de fichier
(`<device>_*.parquet`). Détails en SPEC-02 §4.1.

## Comment le frame accéléromètre est-il appliqué ?

Pour chaque ligne au timestamp `ts`, le consommateur cherche la
première entrée `acc_periods` qui satisfait `start ≤ ts ≤ end` et
utilise son `frame` (`raw`, `compensated` ou `partial`). Si
`acc_periods` n'est pas déclaré, le défaut est `raw` (SPEC-01 §3.6).

## Licences dataset

Le manifest porte un champ `license` (chaîne libre façon SPDX) et,
optionnellement, un `license_warning`. Les cas typiques :

| Licence | Republier modifié | Exemple manifest |
|---------|---------------------|------------------|
| CC-BY-4.0 | ✅ avec attribution | `license: "CC-BY-4.0"` |
| CC-BY-NC-ND-4.0 | ❌ ND interdit les dérivés | `license: "CC-BY-NC-ND-4.0"`, `license_warning: "Non-commercial, no derivatives"` |
| CC0 | ✅ tout est permis | `license: "CC0-1.0"` |
| Interne / propriétaire | ❌ | `license: "internal"` |

Le tooling à venir ajoutera un champ
`license_republish_derivative: {allowed,forbidden,academic}` plus un
linter CI qui refuse de committer un parquet converti sous une
source `forbidden`. En attendant, c'est appliqué par convention —
voir [Écrire un adapter → Piège licence](writing-adapter.md#piege-licence).

## Et les métadonnées par-ligne qui varient ?

Tout ce qui varie réellement ligne à ligne reste dans le parquet
(`lat`, `ax_mps2`…). Le manifest ne sert qu'aux métadonnées
**par-fichier** qui ne varient pas, ou aux métadonnées segmentées
dans le temps (`acc_periods`, historique de config) qui ne changent
qu'à des bornes grossières.

## Mon manifest échoue la validation — où regarder ?

Lancer le validator avec sortie verbose :

```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json \
             -d manifest.yaml --errors=text --all-errors
```

Les pièges classiques :

- `start: 2025-01-01` (YAML l'auto-parse en date Python) → mettre
  des guillemets : `"2025-01-01T00:00:00Z"`
- `n_trips: null` est accepté — la plupart des compteurs tolèrent
  `null` pour dire « inconnu »
- Énumération invalide pour `hardware.class`
  (valeurs autorisées : `research`, `commercial`, `consumer`,
  `prototype`, `smartphone`)
- Bloc requis absent : `dataset_id`, `schema_version`, ou `source`
