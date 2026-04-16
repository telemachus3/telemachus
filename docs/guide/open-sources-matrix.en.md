# Open sources — Telemachus coverage matrix

Which public datasets are mapped to Telemachus format, and what each one
exposes. Use this to pick the right dataset for your experiment, or
to spot which columns you'd need to synthesise if you work across
multiple sources.

## Coverage at a glance

Legend: ✅ present · ⚠️ derived / lossy · ❌ absent · — N/A

| Dataset | `ts` | `lat`/`lon` | `speed_mps` | IMU accel | IMU gyro | Magneto | OBD / CAN | Adapter ready |
|---------|:----:|:-----------:|:-----------:|:---------:|:--------:|:-------:|:---------:|:-------------:|
| **AEGIS** (Zenodo 820576, CC-BY-4.0) | ✅ | ✅ | ⚠️ GPS 5 Hz | ✅ 24 Hz | ✅ 24 Hz | ❌ | ✅ | ✅ |
| **PVS Menegazzo** (Kaggle, CC-BY-NC-ND-4.0) | ✅ | ✅ | ✅ 1 Hz | ✅ 100 Hz | ✅ 100 Hz (deg/s) | ❌ | ❌ | ✅ (code only) |
| **STRIDE Bangladesh** (Figshare 25460755, CC-BY-4.0) | ✅ | ✅ | ✅ 1 Hz | ✅ 100 Hz | ✅ 100 Hz | ⚠️ (not ingested) | ❌ | ✅ |
| **UAH-DriveSet** (Academic) | ✅ | ✅ | ✅ | ✅ 10 Hz | ❌ | ❌ | ❌ | ⏳ (pending) |
| **Smartphone Accident** (CC0) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ | ⏳ (pending) |

See each dataset's `manifest.yaml` under [`datasets/`](https://github.com/telemachus3/telemachus/tree/main/datasets) for detailed native rates, frame declarations, license warnings and `papers_using` references.

## Per-column notes

### Gyroscope
Only AEGIS, PVS and STRIDE ship a native gyroscope. If your method
needs gyro ground-truth, these are the three candidates. PVS gyro is
in `deg/s` at the source — the [PRIVATE] loader converts to `rad/s`
automatically based on `sensors.gyroscope.unit` in the manifest.

### Speed
Only PVS and STRIDE ship a proper GPS `speed_mps` field at 1 Hz.
AEGIS has GPS at 5 Hz but the speed channel needs verification; the
[PRIVATE] loader falls back to OBD speed when available.

### Magnetometer
STRIDE is the only source that technically exposes magnetometer
data, but no loader ingests it today (the `Magnetometer.csv` is
present but not parsed). If your method needs mag, plan a small
loader extension.

### OBD / CAN
Only AEGIS carries OBD PIDs (speed, RPM, …) from the vehicle bus.
For anything else you'll rely on GPS-derived speed and acceleration.

## Which dataset for which task?

| Task | Best choice | Why |
|------|-------------|-----|
| Yaw ground-truth at high rate | PVS or STRIDE | 100 Hz gyro, clean labels |
| Multi-surface / pothole detection | PVS | 3 placements × 3 vehicles × road surface labels |
| Cross-condition comparison | AEGIS | 35 trips, OBD, multi-session |
| Smartphone-only smartphone-grade IMU | STRIDE (Android) or UAH (iPhone) | Consumer hardware |
| Anything requiring redistribution in derivative form | **Not PVS** | NC-ND forbids derivative republishing |

## Adding a new source

If you know a public dataset that isn't listed here and meets the
minimum bar (has at least GPS + IMU accel with a permissive
license), follow [Converting Open data](converting-open-data.md) and
open a PR.

Minimum bar for inclusion:

- [ ] Permissive license documented (CC-BY / CC0 / Academic-OK)
- [ ] Stable DOI or permanent URL
- [ ] At least `ts`, `lat`, `lon`, `ax/ay/az_mps2` obtainable
- [ ] Manifest validates against
      `spec/schemas/telemachus_manifest_v0.8.json`
