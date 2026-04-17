# Reproduire le dataset PVS au format Telemachus

Le dataset [PVS](https://www.kaggle.com/datasets/jefmenegazzo/pvs-passive-vehicular-sensors-datasets)
(Menegazzo & von Wangenheim, 2020 — Curitiba, Brésil) est distribué
sous licence **CC-BY-NC-ND-4.0**, qui interdit la republication d'œuvres
dérivées. Conséquences :

- PVS **n'est pas** sur Zenodo au format Telemachus (contrairement à
  AEGIS, STRIDE, RS3).
- Vous devez télécharger les CSV bruts sur Kaggle, puis convertir
  localement avec l'adapter `tele` embarqué.

Si vous voulez juste essayer Telemachus sur un vrai dataset IMU riche
sans passer par Kaggle, préférez [AEGIS](https://doi.org/10.5281/zenodo.19609044)
ou [STRIDE](https://doi.org/10.5281/zenodo.19609053) — tous deux
livrent des parquets prêts à l'emploi.

## Ce que PVS apporte

| Propriété | Valeur |
|---|---|
| Matériel | InvenSense MPU-9250, 2 capteurs par véhicule (`left` / `right`) |
| Accel / Gyro / Magnéto | 100 Hz vérité terrain |
| GPS | ~1 Hz |
| Trajets | 9 (3 véhicules × 3 conducteurs × 3 placements) |
| Lignes | 1 080 905 |
| Lieu | Curitiba, Paraná, Brésil — déc. 2019 |
| Licence | CC-BY-NC-ND-4.0 |

Points forts : **3 placements** par trajet (tableau de bord / au-dessus
suspension / sous suspension), **labels de surface de route**,
redondance double-capteur. Point faible : non republiable.

## Reproduction — 3 étapes

Le pas-à-pas complet (avec Kaggle CLI, arborescence attendue, vérif
checksum) vit à côté du convertisseur dans
[`datasets/pvs/README.md`](https://github.com/telemachus3/telemachus/blob/main/datasets/pvs/README.md).
En résumé :

```bash
pip install telemachus kaggle

# 1. Télécharger les données brutes depuis Kaggle
kaggle datasets download -d jefmenegazzo/pvs-passive-vehicular-sensors-datasets
unzip pvs-passive-vehicular-sensors-datasets.zip -d /chemin/vers/pvs/

# 2. Convertir au format Telemachus (choisir un placement + un côté)
tele convert pvs /chemin/vers/pvs/ -o datasets/pvs/ --placement dashboard --side left

# 3. Valider
tele validate datasets/pvs/ --level basic
```

## Citer PVS

Quand vous publiez des résultats utilisant PVS, citez à la fois le
dataset original et la spécification Telemachus :

- Menegazzo, J. & von Wangenheim, A. (2020). *PVS — Passive Vehicular
  Sensors datasets.* Kaggle.
- Edet, S. (2026). *Telemachus Specification v0.8.* Zenodo.
  DOI [10.5281/zenodo.19609019](https://doi.org/10.5281/zenodo.19609019).
