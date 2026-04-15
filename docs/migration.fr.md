# Quoi de neuf

Journal pragmatique, volontairement pas trop formel, de ce qui
change entre versions. Telemachus reste pré-1.0 et la spec évolue où
elle doit — pas de semver strict, pas de revue publique multi-semaines
pour l'instant. Vous upgradez votre code consommateur quand vous
voulez les nouveautés.

## 0.8 brouillon — RFC-0014 Dataset Manifest

Non cassant. Ajoute le sidecar normatif `manifest.yaml` (RFC-0014)
avec des règles d'héritage qui vous permettent de sortir `device_id`,
`trip_id`, `acc_periods` et `trip_carrier_states` du parquet signal.

Opt-in : les parquets 0.7 existants restent valides. Pour upgrader
un dataset, il suffit d'ajouter un `manifest.yaml` à côté. Validator :

```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json \
             -d manifest.yaml
```

Convention ajoutée : colonnes spécifiques fabricant préfixées
`x_<source>_<field>` (par exemple `x_teltonika_ext_voltage_v`). Les
consommateurs peuvent les ignorer sans risque.

## 0.7 — RFC-0013 Telemachus Device Format

Introduit le modèle en couches D0 / D1 / D2. Formalise AccPeriod
(suivi du référentiel accéléromètre) et CarrierState (classification
du contexte par trip).

## 0.2 — Publiée le 2025-10-13

Premier schéma cœur stable. JSON Schema pour les payloads par
message, exemples JSON pour Geotab et Webfleet.

## Suivre les changements

- Les [Releases GitHub](https://github.com/telemachus3/telemachus/releases) (quand elles sont taguées)
- Le `CHANGELOG.md` à la racine du monorepo
- Ou simplement les fichiers RFC-NNNN récents sous `spec/rfcs/`
