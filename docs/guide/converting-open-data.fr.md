# Convertir un dataset Open sans adapter existant

Il arrive qu'on tombe sur un dataset public intéressant (Zenodo,
Kaggle, Figshare…) qui n'a pas encore d'entrée dédiée sous
`datasets/` dans le monorepo. Voici le chemin manuel pour en tirer
un dataset Telemachus Telemachus valide.

## 0. Vérifier la licence avant tout

Appliquez le test de [Écrire un adapter → Piège licence](writing-adapter.md#piege-licence).
Une source en `CC-BY-NC-ND` interdit de republier un dérivé : vous
pouvez publier le **code de l'adapter**, pas le **parquet converti**.
Tout ce qui suit suppose que vous avez le droit de garder une copie
locale pour votre propre usage.

## 1. Inventorier la source

Ouvrez les fichiers bruts et identifiez, colonne par colonne, ce
que chaque flux contient vraiment :

| Colonne source | Unité | Cadence | Correspond à Telemachus |
|----------------|-------|---------|-----------------|
| `timestamp_ms` | ms depuis epoch | — | `ts` (convertir en datetime UTC) |
| `latitude` | deg | 1 Hz | `lat` |
| `longitude` | deg | 1 Hz | `lon` |
| `speed_kmh` | km/h | 1 Hz | `speed_mps` (÷ 3.6) |
| `accel_x_g` | g | 100 Hz | `ax_mps2` (× 9.80665) |
| `accel_y_g` | g | 100 Hz | `ay_mps2` |
| `accel_z_g` | g | 100 Hz | `az_mps2` |
| `gyro_x_dps` | deg/s | 100 Hz | `gx_rad_s` (× π/180) |
| … | | | |

Si une colonne Telemachus attendue manque, décidez tout de suite comment la
gérer :

- **Colonnes GPS absentes** au rythme IMU → laisser en `NaN` (convention multi-rate, SPEC-01 §3.5)
- **Heading manquant** → le recalculer depuis deux points GPS consécutifs (bearing Haversine)
- **Gyro absent** → laisser les colonnes gyro absentes (SPEC-01 §3.3 : absentes ou full-NaN, jamais remplies avec des zéros)

## 2. Télécharger et décompresser

Les scripts vivent dans un dossier adapter dans votre copie de
travail, **pas commité** si la licence est restrictive :

```bash
mkdir -p datasets/xx_my_source/
cd datasets/xx_my_source/
cat > download.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
mkdir -p raw
curl -sSL -o raw/data.zip "https://example.org/dataset.zip"
cd raw && unzip -q data.zip && cd ..
echo "fichiers bruts sous datasets/xx_my_source/raw/"
EOF
chmod +x download.sh
```

## 3. Écrire l'adapter

Le template complet est sur [Écrire un adapter](writing-adapter.md).
Le minimum à faire :

1. Lire les fichiers bruts (CSV / Parquet / format vendor).
2. Renommer et convertir les colonnes (attention aux unités !) vers les noms Telemachus.
3. Trier par `ts`, s'assurer de la monotonie, dédupliquer si besoin.
4. Écrire le parquet Telemachus.
5. Produire un `manifest.yaml` qui déclare `hardware`,
   `sensors.*.rate_hz`, `acc_periods` (start/end/frame), le bloc
   `source` et la `license`.

## 4. Détecter le frame accéléromètre

Étape critique, souvent oubliée. Faites ce check sur un segment
stationnaire connu (device à l'arrêt sur une table, véhicule à
l'arrêt moteur coupé) :

```python
import numpy as np, pandas as pd
df = pd.read_parquet("d0.parquet")

# Prendre une fenêtre stationnaire (10 premières secondes ici)
rest = df.iloc[:int(10 * 100)]  # 10 s à 100 Hz
a_norm = np.sqrt(rest["ax_mps2"]**2 + rest["ay_mps2"]**2 + rest["az_mps2"]**2)
mean_g = a_norm.mean()
print(f"||a|| au repos : {mean_g:.2f} m/s²")

if mean_g > 8:
    frame = "raw"           # gravité présente
elif mean_g < 2:
    frame = "compensated"   # firmware l'a retirée
else:
    frame = "partial"
print(f"→ frame = {frame}")
```

Et reportez le résultat dans `manifest.yaml` sous `acc_periods` :

```yaml
acc_periods:
  - start: 2024-01-01T00:00:00Z
    end:   2024-12-31T23:59:59Z
    frame: raw               # ou compensated / partial
    detection_method: auto
    residual_g: 0.0          # uniquement si frame=partial
```

## 5. Valider

Les deux artefacts doivent passer :

```bash
# Manifest
ajv validate \
  -s spec/schemas/telemachus_manifest_v0.8.json \
  -d datasets/xx_my_source/manifest.yaml

# Sanity Telemachus (pas encore de CLI canonique)
python -c "
import pandas as pd
df = pd.read_parquet('datasets/xx_my_source/d0.parquet')
req = ['ts','lat','lon','speed_mps','ax_mps2','ay_mps2','az_mps2']
assert not [c for c in req if c not in df.columns], 'colonnes manquantes'
assert df['ts'].is_monotonic_increasing
print('OK')
"
```

## 6. Partager (optionnel)

Si la licence autorise la redistribution :

1. Ouvrez une PR qui ajoute votre adapter sous `python-cli/adapters/`.
2. Ajoutez le `manifest.yaml` sous `datasets/xx_my_source/`.
3. Volume brut < 10 Mo : vous pouvez committer le parquet directement.
   Au-delà : `git-lfs` pour les fichiers > 10 Mo, ou mettez le
   parquet sur Zenodo et référencez-le dans le manifest.

La [matrice des sources Open](open-sources-matrix.md) vous dit
quelles sources sont déjà couvertes, histoire d'éviter les doublons.
