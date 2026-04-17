# Reproducing the PVS dataset in Telemachus format

The [PVS](https://www.kaggle.com/datasets/jefmenegazzo/pvs-passive-vehicular-sensors-datasets)
dataset (Menegazzo & von Wangenheim, 2020 — Curitiba, Brazil) is
licensed under **CC-BY-NC-ND-4.0**, which forbids redistribution of
derivative works. As a consequence:

- PVS is **not** on Zenodo in Telemachus format (unlike AEGIS, STRIDE, RS3).
- You need to download the raw CSVs from Kaggle yourself, then convert
  locally with the bundled `tele` adapter.

If you just want to try Telemachus on a real IMU-rich dataset without
going through Kaggle, reach for [AEGIS](https://doi.org/10.5281/zenodo.19609044)
or [STRIDE](https://doi.org/10.5281/zenodo.19609053) instead — both
ship ready-to-use parquets.

## What PVS brings

| Property | Value |
|---|---|
| Hardware | InvenSense MPU-9250, 2 sensors per vehicle (`left` / `right`) |
| Accel / Gyro / Magneto | 100 Hz ground truth |
| GPS | ~1 Hz |
| Trips | 9 (3 vehicles × 3 drivers × 3 sensor placements) |
| Rows | 1,080,905 |
| Location | Curitiba, Paraná, Brazil — Dec 2019 |
| License | CC-BY-NC-ND-4.0 |

Strong points: **3 placements** per trip (dashboard / above-suspension /
below-suspension), **road surface labels**, dual-sensor redundancy.
Weak point: can't be republished.

## Reproduction — 3 steps

The full step-by-step (with Kaggle CLI, expected tree, checksum
verification) lives next to the converter in
[`datasets/pvs/README.md`](https://github.com/telemachus3/telemachus/blob/main/datasets/pvs/README.md).
In short:

```bash
pip install telemachus kaggle

# 1. Download raw data from Kaggle
kaggle datasets download -d jefmenegazzo/pvs-passive-vehicular-sensors-datasets
unzip pvs-passive-vehicular-sensors-datasets.zip -d /path/to/pvs/

# 2. Convert to Telemachus (pick a placement + side)
tele convert pvs /path/to/pvs/ -o datasets/pvs/ --placement dashboard --side left

# 3. Validate
tele validate datasets/pvs/ --level basic
```

## Citing PVS

When you publish results using PVS data, cite both the original dataset
and the Telemachus format spec:

- Menegazzo, J. & von Wangenheim, A. (2020). *PVS — Passive Vehicular
  Sensors datasets.* Kaggle.
- Edet, S. (2026). *Telemachus Specification v0.8.* Zenodo.
  DOI [10.5281/zenodo.19609019](https://doi.org/10.5281/zenodo.19609019).
