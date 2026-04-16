# Concepts

Les cinq idées à avoir en tête pour lire correctement des données Telemachus.

## Telemachus, vu comme cinq groupes fonctionnels

Le schéma Telemachus est **plat** (parquet colonnaire, pas de structure
imbriquée), mais mentalement il se décompose en cinq groupes
fonctionnels. Les connaître, c'est retenir plus facilement pourquoi
chaque colonne existe.

```
Telemachus = datetime       ts
   + GPS            lat, lon, speed_mps, heading_deg,
                    altitude_gps_m, hdop, n_satellites
   + IMU
       ├── accel    ax_mps2, ay_mps2, az_mps2
       ├── gyro     gx_rad_s, gy_rad_s, gz_rad_s   (optionnel)
       └── magneto  mx_uT,    my_uT,    mz_uT      (optionnel)
   + OBD / CAN      ignition, odometer_m, rpm,
                    speed_obd_mps, fuel_*, …       (optionnel)
   + extra          x_<source>_<field>             (spécifique fabricant)
```

| Groupe | Ce qu'il vous dit | Cadence typique |
|--------|--------------------|-----------------|
| **datetime** | *Quand* la mesure a été prise | Cadence IMU (10 Hz) |
| **GPS** | *Où* se trouve le véhicule et à quelle vitesse | 1 Hz (NaN entre les fix) |
| **IMU** | *Comment* le véhicule bouge (accélérations, rotations, champ) | 10 à 100 Hz |
| **OBD/CAN** | *Ce que dit le véhicule lui-même* (données bus) | 1 Hz (variable) |
| **extra** | Tout ce qui est propre à un fabricant et ne rentre pas ailleurs | variable |

!!! note "Pourquoi colonnes plates et pas de structures imbriquées ?"
    Parquet est optimisé pour les colonnes plates (pushdown des
    projections, scans rapides). Imbriquer `imu.accel.x_mps2`, c'est
    visuellement propre mais coûteux en perf et compatibilité. Le
    *modèle mental* est imbriqué ; le *schéma* reste plat.

### Champs `extra` spécifiques fabricant

Quand un fabricant expose un champ qui n'a pas d'équivalent standard
Telemachus (un compteur propriétaire, un flag interne device, etc.),
on utilise la convention **`x_<source>_<field>`** :

| Colonne | Sens |
|---------|------|
| `x_teltonika_ext_voltage_v` | Tension d'alim externe Teltonika |
| `x_geotab_geofence_id` | Identifiant geofence propre à Geotab |
| `x_danlaw_codec_id` | Tag codec firmware Danlaw |

Le préfixe `x_` signale « hors contrat Telemachus normatif, le consommateur
peut l'ignorer sans risque ». Le segment `<source>` lève toute
ambiguïté si plusieurs fabricants sont mélangés dans un même dataset.

## Le modèle en couches Telemachus record format

| Couche | Rôle | Entrée | Sortie |
|--------|------|--------|--------|
| **Telemachus** | Device | Matériel | Parquet brut — uniquement ce que le device mesure |
| **enriched** | Nettoyé et contextualisé | Telemachus | Telemachus enrichi : map matching, DEM, calibration IMU, score de qualité |
| **events layer** | Événements et situations | enriched | enriched + colonne `event` + table d'événements (freinages, nids-de-poule, virages…) |

La spec Telemachus est **normative sur Telemachus** (SPEC-01). Les contrats
de colonnes enriched et events layer sont documentés en SPEC-01 §4, mais leurs
*algorithmes* restent volontairement hors scope — deux consommateurs
peuvent calculer un enriched différemment tant que le schéma de sortie reste
conforme.

**Règle d'or** : une colonne dérivée de données externes (cartes,
DEM, sortie d'un algo) appartient à enriched ou au-dessus, jamais à Telemachus.

## Multi-rate IMU ↔ GNSS

La plupart des devices streamment l'IMU à 10 Hz et le GNSS à 1 Hz.
Telemachus est timestampé au **rythme IMU**, avec les colonnes GNSS qui
valent `NaN` entre les fix :

```
ts                    lat      lon       speed_mps  ax_mps2  ay_mps2  az_mps2
2025-01-01T08:00:00.0 49.3347  1.3830    5.2        0.12     0.03     9.81
2025-01-01T08:00:00.1 NaN      NaN       NaN        0.15    -0.01     9.80
2025-01-01T08:00:00.2 NaN      NaN       NaN        0.11     0.02     9.82
…
2025-01-01T08:00:01.0 49.3348  1.3831    5.3        0.13     0.01     9.81
```

Pour vos métriques GNSS seules (distance, vitesse moyenne), enlevez
les NaN explicitement. Pour vos métriques IMU seules (jerk,
vibration), prenez toutes les lignes.

Le manifest déclare `sensors.gps.rate_hz` et
`sensors.accelerometer.rate_hz` précisément pour que vous puissiez
pré-allouer vos buffers et choisir une stratégie d'interpolation
adaptée.

## AccPeriod : le référentiel de l'accéléromètre

Un même accéléromètre physique peut émettre dans plusieurs
**référentiels** selon l'état du firmware :

| Frame | Au repos | Comportement |
|-------|----------|--------------|
| `raw` | `\|a\|` ≈ 9.81 m/s² | Sortie capteur brute |
| `compensated` | `\|a\|` ≈ 0 m/s² | Firmware a retiré la gravité |
| `partial` | `0 < \|a\| < g` | Compensation imparfaite |

L'information compte : les traitements aval (calibration IMU,
détection d'événements) ont besoin de savoir si la gravité est
présente ou non dans le signal.

Le manifest déclare un ou plusieurs segments `acc_periods`, chacun
couvrant une plage temporelle avec un frame cohérent :

```yaml
acc_periods:
  - start: 2025-01-01T00:00:00Z
    end:   2025-03-15T12:00:00Z
    frame: compensated
    detection_method: empirical
  - start: 2025-03-15T12:00:01Z
    end:   present
    frame: raw
    detection_method: profile_change
```

Par défaut (si le manifest ne déclare rien) : une seule période
implicite avec `frame: "raw"`. La définition normative complète se
trouve dans SPEC-01 §3.6.

## CarrierState : ce trip, c'est vraiment de la conduite ?

Un device télématique enregistre en continu, mais **toutes ces
données ne correspondent pas à de la conduite réelle**. Un boîtier
laissé sur un établi, manipulé à la main pendant un test, ou
temporairement débranché émet tout de même des messages.

Le `carrier_state` classe chaque trip dans l'un des six contextes :

| État | Description | Véhicule ? | Utilisable en analytique ? |
|------|-------------|------------|------------------------------|
| `mounted_driving` | Installé, véhicule en mouvement | Oui | Oui |
| `mounted_idle` | Installé, véhicule à l'arrêt | Oui | Oui (ZUPT) |
| `unplugged` | Alim externe perdue | Inconnu | Optionnel |
| `desk` | Sur une surface stable, hors véhicule | Non | Non |
| `handheld` | Manipulé à la main | Non | Non |
| `unknown` | Signaux insuffisants | Inconnu | Non |

La classification combine quatre indicateurs : tension d'alim
externe, vitesse GPS, variance de la norme accéléromètre, dérive de
position GPS. L'arbre de décision complet est en SPEC-01 §3.7.

Dans le manifest, on déclare les états via `trip_carrier_states` :

```yaml
trip_carrier_states:
  - trip_id: "T20250410_1053_001"
    carrier_state: "mounted_driving"
    confidence: "high"
```

En aval, tout traitement qui présuppose un contexte véhicule
**doit** filtrer sur `is_vehicle_data == True` (autrement dit,
`carrier_state` ∈ {`mounted_driving`, `mounted_idle`}).
