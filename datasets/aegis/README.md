# AEGIS — Telemachus Format

Automotive sensor data from Graz (Austria), converted to [Telemachus v0.8](https://doi.org/10.5281/zenodo.17228091) format.

## Source

Brunner, P., Trügler, A., & Sackl, A. (2017). *AEGIS: Autonomous driving data from Graz.*
Original dataset: [Zenodo 820576](https://zenodo.org/records/820576) (CC-BY-4.0)

## Contents

| File | Format | Size | Description |
|------|--------|------|-------------|
| `manifest.yaml` | YAML | 1 KB | SPEC-02 dataset manifest |
| `aegis-telemachus.parquet` | Parquet | 17.7 MB | Full dataset (1,063,350 rows, 33 trips) |
| `aegis-telemachus.csv` | CSV | 226 MB | Same data, human-readable |

## Hardware

BeagleBone research platform: GPS 5 Hz, accelerometer 24 Hz, gyroscope 24 Hz, OBD-II speed.

## Usage

```python
import telemachus as tele
df = tele.read("aegis-telemachus.parquet")
```

## License

CC-BY-4.0 (inherited from source dataset)

## Citation

If you use this dataset, please cite both the original AEGIS dataset and the Telemachus format specification.
