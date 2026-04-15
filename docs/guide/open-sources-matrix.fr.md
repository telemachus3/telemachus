# Sources Open — matrice de couverture D0

Quels datasets publics sont déjà mappés vers Telemachus format, et ce
que chacun expose. Utilisez ce tableau pour choisir le dataset qui
correspond à votre expérimentation, ou pour repérer les colonnes que
vous devrez synthétiser si vous croisez plusieurs sources.

## Vue d'ensemble

Légende : ✅ présent · ⚠️ dérivé / approximatif · ❌ absent · — sans objet

| Dataset | `ts` | `lat`/`lon` | `speed_mps` | IMU accel | IMU gyro | Magneto | OBD / CAN | Adapter prêt |
|---------|:----:|:-----------:|:-----------:|:---------:|:--------:|:-------:|:---------:|:------------:|
| **AEGIS** (Zenodo 820576, CC-BY-4.0) | ✅ | ✅ | ⚠️ GPS 5 Hz | ✅ 24 Hz | ✅ 24 Hz | ❌ | ✅ | ✅ |
| **PVS Menegazzo** (Kaggle, CC-BY-NC-ND-4.0) | ✅ | ✅ | ✅ 1 Hz | ✅ 100 Hz | ✅ 100 Hz (deg/s) | ❌ | ❌ | ✅ (code only) |
| **STRIDE Bangladesh** (Figshare 25460755, CC-BY-4.0) | ✅ | ✅ | ✅ 1 Hz | ✅ 100 Hz | ✅ 100 Hz | ⚠️ (pas ingéré) | ❌ | ✅ |
| **UAH-DriveSet** (Academic) | ✅ | ✅ | ✅ | ✅ 10 Hz | ❌ | ❌ | ❌ | ⏳ (à faire) |
| **Smartphone Accident** (CC0) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ | ⏳ (à faire) |

Le `manifest.yaml` de chaque dataset, sous [`datasets/`](https://github.com/telemachus3/telemachus/tree/main/datasets), détaille les cadences natives, les déclarations de frame, les avertissements licence et les `papers_using` associés.

## Notes par colonne

### Gyroscope
Seuls AEGIS, PVS et STRIDE fournissent un gyroscope natif. Si votre
méthode a besoin d'une vérité terrain gyroscopique, ce sont vos trois
candidats. PVS est en `deg/s` à la source — le loader [PRIVATE] convertit
automatiquement en `rad/s` en lisant `sensors.gyroscope.unit` dans le
manifest.

### Vitesse
PVS et STRIDE exposent une `speed_mps` GPS correcte à 1 Hz. AEGIS a
du GPS à 5 Hz mais le canal vitesse mérite une vérification ; le
loader [PRIVATE] utilise la vitesse OBD en repli quand elle est
disponible.

### Magnétomètre
STRIDE est techniquement la seule source avec des données
magnétomètre, mais aucun loader ne les ingère aujourd'hui (le fichier
`Magnetometer.csv` est présent mais pas parsé). Si votre méthode en
a besoin, prévoir une petite extension de loader.

### OBD / CAN
Seul AEGIS embarque des PIDs OBD (vitesse véhicule, RPM…) venant du
bus. Pour tout le reste, vous travaillerez avec la vitesse dérivée
GPS et les accélérations.

## Quel dataset pour quel usage ?

| Tâche | Meilleur choix | Pourquoi |
|-------|----------------|----------|
| Vérité terrain yaw à haute cadence | PVS ou STRIDE | Gyro 100 Hz, labels propres |
| Détection multi-surface / nids-de-poule | PVS | 3 emplacements × 3 véhicules, surfaces labellisées |
| Comparaison cross-conditions | AEGIS | 35 trips, OBD, multi-sessions |
| Capteurs smartphone grand public | STRIDE (Android) ou UAH (iPhone) | Hardware consumer |
| Nécessité de redistribuer en forme dérivée | **Pas PVS** | NC-ND interdit la republication dérivée |

## Ajouter une nouvelle source

Si vous connaissez un dataset public absent de cette liste qui passe
le minimum requis (GPS + IMU accel sous licence permissive), suivez
le guide [Convertir un dataset Open](converting-open-data.md) et
ouvrez une PR.

Minimum pour l'inclusion :

- [ ] Licence permissive documentée (CC-BY / CC0 / Academic OK)
- [ ] DOI stable ou URL permanente
- [ ] Au moins `ts`, `lat`, `lon`, `ax/ay/az_mps2` récupérables
- [ ] Le manifest valide contre `spec/schemas/telemachus_manifest_v0.8.json`
