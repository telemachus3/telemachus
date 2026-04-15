# Concepts

Les quatre idées à comprendre pour lire correctement des données Telemachus.

## D0 → D1 → D2 — le modèle en couches

| Couche | Nom | Entrée | Sortie |
|--------|-----|--------|--------|
| **D0** | Device | Matériel | Parquet brut — uniquement ce que le device mesure |
| **D1** | Nettoyé & contextualisé | D0 | D0 enrichi + map matching, DEM, calibration IMU, qualité signal |
| **D2** | Événements & situations | D1 | D1 + colonne event + table d'événements (freinage, nid-de-poule, virage…) |

La spec Telemachus est **normative sur D0** (RFC-0013). Les contrats
colonnes D1 et D2 sont documentés en RFC-0013 §4 mais leurs
*algorithmes* sont intentionnellement hors scope — différents
consommateurs peuvent calculer D1/D2 différemment tant qu'ils
émettent des colonnes conformes.

**Règle d'or** : une colonne dérivée de données externes (cartes,
DEM, sortie algorithmique) appartient à D1 ou supérieur, jamais D0.

## Multi-rate IMU vs GNSS

La plupart des devices streamment l'IMU à 10 Hz et le GNSS à 1 Hz.
D0 est timestampé au **rythme IMU**, avec les colonnes GNSS
contenant `NaN` entre les fix :

```
ts                    lat      lon       speed_mps  ax_mps2  ay_mps2  az_mps2
2025-01-01T08:00:00.0 49.3347  1.3830    5.2        0.12     0.03     9.81
2025-01-01T08:00:00.1 NaN      NaN       NaN        0.15    -0.01     9.80
2025-01-01T08:00:00.2 NaN      NaN       NaN        0.11     0.02     9.82
…
2025-01-01T08:00:01.0 49.3348  1.3831    5.3        0.13     0.01     9.81
```

Pour des métriques GNSS seules (distance, vitesse moyenne), droppez
explicitement les NaN. Pour des métriques IMU seules (jerk,
vibration), utilisez toutes les lignes.

Le manifest `sensors.{gps,accelerometer}.rate_hz` déclare les
fréquences attendues pour que les consommateurs pré-allouent les
buffers et choisissent les stratégies d'interpolation.

## AccPeriod — le référentiel de l'accéléromètre

Le même accéléromètre physique peut émettre des données dans
différents **référentiels** selon l'état du firmware :

| Frame | Au repos | Comportement |
|-------|----------|--------------|
| `raw` | `\|a\|` ≈ 9.81 m/s² | Sortie capteur non traitée |
| `compensated` | `\|a\|` ≈ 0 m/s² | Firmware a soustrait la gravité |
| `partial` | `0 < \|a\| < g` | Compensation imparfaite |

Ça compte parce que les stages aval (calibration IMU, détection
d'événements) doivent savoir si la gravité est dans le signal.

Le manifest déclare un ou plusieurs segments `acc_periods` — chacun
une plage temporelle contiguë avec un frame cohérent :

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

Défaut si absent : une seule période implicite `frame: "raw"`. Voir
RFC-0013 §3.6 pour la définition normative complète.

## CarrierState — ce trip est-il vraiment de la conduite ?

Un device télématique enregistre en continu, mais **toutes ces
données ne viennent pas d'un contexte de conduite réel**. Un device
laissé sur un établi, manipulé à la main pendant des tests, ou
temporairement débranché émet quand même des messages.

Le `carrier_state` au niveau trip classe chaque trip dans l'un des
six contextes :

| État | Description | Véhicule ? | Pour analytics ? |
|------|-------------|------------|-------------------|
| `mounted_driving` | Installé, véhicule en mouvement | Oui | Oui |
| `mounted_idle` | Installé, véhicule stationnaire | Oui | Oui (ZUPT) |
| `unplugged` | Alimentation externe perdue | Inconnu | Optionnel |
| `desk` | Surface stable, hors véhicule | Non | Non |
| `handheld` | En mouvement à la main | Non | Non |
| `unknown` | Signaux insuffisants | Inconnu | Non |

La classification combine 4 signaux : tension d'alim externe,
vitesse GPS, variance norme accéléromètre, dérive position GPS.
Voir RFC-0013 §3.7 pour l'arbre de décision.

Dans le manifest, déclarez via `trip_carrier_states` :

```yaml
trip_carrier_states:
  - trip_id: "T20250410_1053_001"
    carrier_state: "mounted_driving"
    confidence: "high"
```

Les stages aval DOIVENT filtrer sur `is_vehicle_data == True` (i.e.
`carrier_state ∈ {mounted_driving, mounted_idle}`) pour toute
analytique qui présuppose un contexte véhicule.
