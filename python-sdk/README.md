# telemachus-py

Python tools for the **Telemachus** open telematics pivot format:
- Export RS3 CSVs → Telemachus dataset (YAML manifest + Parquet tables)
- Validate a dataset.yaml and check referenced tables
- Summarize dataset (rows, columns, time span)

## Quickstart

```bash
tele export \
  --traj tests/data/rs3_trajectory.csv \
  --imu tests/data/rs3_imu.csv \
  --events tests/data/rs3_events.csv \
  --outdir out/tele/$(date -u +%Y%m%dT%H%M%SZ) \
  --freq-hz 10 --vehicle-id VEH-01 --vehicle-type passenger_car

tele validate out/tele/*/dataset.yaml
tele info out/tele/*/dataset.yaml
```

## License
AGPL-3
