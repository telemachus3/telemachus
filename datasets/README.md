# Telemachus Datasets

All datasets in [Telemachus v0.8](https://doi.org/10.5281/zenodo.19609019) format.
See `INDEX.yaml` for the complete machine-readable index.

## Open datasets (Zenodo)

| Dataset | Dir | DOI | Rows | Trips | License |
|---------|-----|-----|------|-------|---------|
| **AEGIS** (Graz, AT) | `aegis/` | [10.5281/zenodo.19609044](https://doi.org/10.5281/zenodo.19609044) | 1,063,350 | 33 | CC-BY-4.0 |
| **STRIDE** (Rajshahi, BD) | `stride/` | [10.5281/zenodo.19609053](https://doi.org/10.5281/zenodo.19609053) | 340,900 | 23 | CC-BY-4.0 |
| **RS3** (Le Havre, FR) | `rs3/` | [10.5281/zenodo.19609057](https://doi.org/10.5281/zenodo.19609057) | 131,186 | 1 | CC0-1.0 |
| **PVS** (Curitiba, BR) | `pvs/` | non-redistributable | 1,080,905 | 9 | CC-BY-NC-ND-4.0 |

## Directory structure

```
datasets/
├── INDEX.yaml              # Central index (all datasets, Open + private)
├── aegis/                  # AEGIS — CC-BY-4.0, on Zenodo
│   ├── manifest.yaml
│   ├── aegis-telemachus.parquet
│   ├── SHA256SUMS
│   └── README.md
├── stride/                 # STRIDE — CC-BY-4.0, on Zenodo
│   ├── manifest.yaml
│   ├── stride-telemachus.parquet
│   ├── SHA256SUMS
│   └── README.md
├── rs3/                    # RS3 synthetic — CC0, on Zenodo
│   ├── manifest.yaml
│   ├── rs3-telemachus.parquet
│   ├── SHA256SUMS
│   └── README.md
└── pvs/                    # PVS — CC-BY-NC-ND, local only
    ├── manifest.yaml
    ├── .gitignore          # parquet not committed
    ├── SHA256SUMS
    └── README.md           # reproduction instructions
```

Parquet files are `.gitignore`d. To get them locally:

```bash
# Download from Zenodo
wget https://zenodo.org/records/19609044/files/aegis-telemachus.parquet -O datasets/aegis/aegis-telemachus.parquet
wget https://zenodo.org/records/19609053/files/stride-telemachus.parquet -O datasets/stride/stride-telemachus.parquet
wget https://zenodo.org/records/19609057/files/rs3-telemachus.parquet -O datasets/rs3/rs3-telemachus.parquet

# Or generate via adapters
tele convert aegis /path/to/raw/ -o datasets/aegis/
tele convert stride /path/to/raw/ -o datasets/stride/
tele convert pvs /path/to/raw/ -o datasets/pvs/ --placement dashboard --side left
```

## Quick start

```python
import telemachus as tele

df = tele.read("datasets/aegis/aegis-telemachus.parquet")
report = tele.validate(df, profile="imu", level="basic")
```
