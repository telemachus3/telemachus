# Valider un fichier

Un dataset Telemachus se valide sur deux plans :

1. **Le signal** (parquet) respecte le contrat de colonnes Telemachus (SPEC-01).
2. **Le manifest** (`manifest.yaml`) respecte le schema manifest (SPEC-02).

## Validation CLI

```bash
# Valider un dataset complet (manifest + parquet)
tele validate chemin/vers/dataset/ --level full

# Valider un manifest seul
tele validate chemin/vers/manifest.yaml

# Check rapide sur un fichier parquet
tele validate chemin/vers/data.parquet --level basic

# Info dataset
tele info chemin/vers/manifest.yaml
```

## Validation Python

```python
import telemachus as tele

# Valider un DataFrame
df = tele.read("chemin/vers/manifest.yaml")
report = tele.validate(df, profile="imu")
print(report)

# Valider un manifest
report = tele.validate_manifest("chemin/vers/manifest.yaml")

# Valider un dataset complet
report = tele.validate_dataset("chemin/vers/dataset/", level="full")
```

## Niveaux de validation

| Niveau | Checks | Usage |
|--------|--------|-------|
| `basic` | Colonnes mandatory par profil, types, ranges | Check rapide |
| `strict` | `basic` + ts monotone, gravite AccPeriod | Recherche |
| `manifest` | Regles SPEC-02 (champs requis, acc_periods, sensors) | Manifest seul |
| `full` | `strict` + `manifest` + validation croisee | Publication |

## Profils

La validation s'adapte au profil declare (SPEC-01 §2.2) :

| Profil | Colonnes requises |
|--------|------------------|
| `core` | ts, lat, lon, speed_mps |
| `imu` | core + ax_mps2, ay_mps2, az_mps2 |
| `full` | imu + gx_rad_s, gy_rad_s, gz_rad_s |

Si aucun profil n'est declare, le validateur assume `imu` (defaut).
