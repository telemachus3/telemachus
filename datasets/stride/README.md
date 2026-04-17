# STRIDE — Telemachus Format

Smartphone-based road quality data from Bangladesh, converted to [Telemachus v0.8](https://doi.org/10.5281/zenodo.17228091) format.

## Source

STRIDE: Smartphone-based road quality dataset for driving behaviour and road anomaly detection.
Original dataset: [Figshare 25460755](https://figshare.com/articles/dataset/25460755) (CC-BY-4.0)

## Contents

| File | Format | Size | Description |
|------|--------|------|-------------|
| `manifest.yaml` | YAML | 1 KB | SPEC-02 dataset manifest |
| `stride-telemachus.parquet` | Parquet | 7.6 MB | Full dataset (340,900 rows, 23 trips) |
| `stride-telemachus.csv` | CSV | 100 MB | Same data, human-readable |

## Hardware

Xiaomi POCO X2 smartphone: GPS 1 Hz, accelerometer 100 Hz, gyroscope 100 Hz, magnetometer 100 Hz.

## Usage

```python
import telemachus as tele
df = tele.read("stride-telemachus.parquet")
```

## License

CC-BY-4.0 (inherited from source dataset)

## Citation

If you use this dataset, please cite both the original STRIDE dataset and the Telemachus format specification.
