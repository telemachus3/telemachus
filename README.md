[![PyPI](https://img.shields.io/pypi/v/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Python](https://img.shields.io/pypi/pyversions/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Docs](https://img.shields.io/badge/docs-telemachus3.org-blue)](https://telemachus3.org)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21959388.svg)](https://doi.org/10.5281/zenodo.21959388)
[![License](https://img.shields.io/badge/spec-MIT-green)](LICENSE)
[![SDK License](https://img.shields.io/badge/SDK-Apache--2.0-green)](python-sdk/LICENSE)

# Telemachus

**Telemachus** is an open, Parquet-native pivot format for high-frequency
mobility and telematics data. It bridges the rigor of scientific
kinematics (multi-rate GNSS+IMU at 10-100 Hz, accelerometer gravity
frame tracking) and scalable fleet analytics (OBD, trip metadata,
carrier state) in a single format — instantly queryable in Pandas,
Spark, DuckDB, or Athena.

**Why not an existing standard?** Robotics formats (ROS bags) handle
the physics but aren't columnar. Fleet APIs (Geotab, Samsara) handle
scale but abstract away raw sensors. IoT protocols (MQTT, SensorThings)
handle transport but not analytical storage. Telemachus fills the gap:
raw sensor data, SI units, flat columns, Parquet files, Python SDK.

This repository is the **monorepo** consolidating spec, Python SDK,
CLI, and reference datasets into a single source of truth.

## Layout

| Directory | What |
|-----------|------|
| [`spec/`](spec/) | SPECs + JSON Schemas — the normative specification |
| [`python-sdk/`](python-sdk/) | Python SDK & validator (`telemachus` package on PyPI) |
| [`python-cli/`](python-cli/) | CLI tools (`tele` command, bundled with the SDK) |
| [`datasets/`](datasets/) | Open datasets in Telemachus format — AEGIS, STRIDE, RS3, PVS |
| [`docs/`](docs/) | Site sources (mkdocs) + the AEGIS demo notebook |

## Versions

| Artifact | Version |
|----------|---------|
| **Current spec** | **v1.0** (2026-08-15) — 4 SPEC pillars |
| **Library** | **1.0.0a4** — pre-release; `pip` does not install it by default |

The specification defines the Telemachus record format (column contracts,
AccPeriod frame tracking, CarrierState classification, burst sampling,
magnetometer support) and the normative **Dataset Manifest**.

1.0 is not a feature count. Until it, SPEC-02 required a row accounting the
reference implementation did not produce, and SPEC-04 asserted a perimeter that
had never been written down: a specification whose own library did not honour
it. 1.0 ends that gap, breaks the imports it needs to break while a break is
still cheap, and adds the adapters that let someone convert their own data
without talking to the author. See the [changelog](CHANGELOG.md).

## Quickstart

### Install
```bash
pip install telemachus
```

### Try it in 5 minutes

The [AEGIS demo notebook](docs/notebooks/aegis-demo.ipynb)
([open in Colab](https://colab.research.google.com/github/telemachus3/telemachus/blob/main/docs/notebooks/aegis-demo.ipynb))
downloads a real Open dataset from Zenodo, loads it, and plots one trip.

### Read a dataset
```python
import telemachus as tele

df = tele.read("path/to/manifest.yaml")   # or directly a .parquet
print(tele.sensor_profile(df))            # → "gps+imu+gyro"
```

### Validate
```bash
tele validate path/to/dataset/ --level full     # full dataset (parquet + manifest)
tele validate path/to/data.parquet --level basic
tele info path/to/manifest.yaml                 # dataset summary
```

### Convert **your own** data

Nobody adopts a format by writing new data into it. The format adapters convert
what you already have, and none of them needs a line of Python.

```bash
# CSV, through a declarative mapping — column AND unit, declared as data
tele mapping-template myexport.csv > mapping.yaml     # lists your own headers
$EDITOR mapping.yaml                                  # fill in the units
tele convert csv myexport.csv --mapping mapping.yaml -o out/

tele convert gpx  rides/     -o out/                  # GPX 1.0 / 1.1
tele convert nmea track.nmea -o out/                  # NMEA 0183 RMC/GGA/VTG
```

A mapping is a file, so it can be reviewed, diffed, and sent back to whoever
produced the export:

```yaml
columns:
  ts:        {column: "Date UTC",  unit: iso8601}
  lat:       {column: "Latitude",  unit: deg}
  speed_mps: {column: "Vitesse",   unit: km/h}     # <- the unit is required
  ax_mps2:   {column: "AccX",      unit: g}
```

`unit` is **required** on every column that carries one. A correct column name
over values in the wrong unit passes every schema check there is; asking for
the unit where the column is named is what stops that, and `tele convert` also
writes down what it dropped and why:

```
  600 rows, 9 columns -> out/csv.parquet
  manifest -> out/manifest.yaml
  dropped 3 of 603 rows: {'duplicate_ts': 2, 'unparseable_ts': 1}
  ValidationReport(PASS, profile=imu, level=full, errors=0, warnings=0)
```

### Convert an Open research dataset
```bash
tele convert aegis  /path/to/aegis/csvs      -o datasets/aegis/
tele convert pvs    /path/to/pvs/trips       -o datasets/pvs/    --placement dashboard
tele convert stride /path/to/stride/road_data -o datasets/stride/ --category driving
```

### Say what the device was doing, not just what it measured

Three manifest blocks describe the *acquisition* rather than the movement, and
between them they carry what makes a file interpretable years later:

```yaml
acc_periods:            # which frame the accelerometer was in     (SPEC-02 §3.7)
carrier_profile:        # what the device was riding on            (SPEC-02 §3.8)
acquisition_breaks:     # whether the acquisition was intact       (SPEC-02 §3.9)
```

The last one exists because **a hole in the data is not a hole in the
movement**. A file with no rows between two instants is ambiguous — parked
underground, device rebooted, network dropped and the frames arrive three days
later, GNSS lost fix while the IMU kept running — and every consumer guesses
differently. Worse, a *frozen* sensor leaves no hole at all: the rows are
present, well-formed, constant, and pass every validation rule.

`carrier_profile` opens the manifest to carriers that are not vehicles. The
invariant is the declaration, not the vocabulary: any profile must say which of
its states an analysis may use. `vehicle` is the default and is unchanged.

### Correct a value without destroying it

```
ts          lat         lat_adj     lat_sigma
...         49.330121   49.330118   0.4
```

The source column keeps its measured values; the correction sits beside it, and
its producer is declared once in the manifest. The invariant is checkable —
`strip_corrections` removes every declared `_adj` and `_sigma` column and must
give back exactly the source file.

Nothing in the specification says how a corrected value is obtained.
`produced_by` is an opaque string, so a pipeline can publish corrected data in
an open format while its method stays its own. SPEC-04 §5.2.1 draws that line
layer by layer.

### Two tiers, visible in the import path

`telemachus` and `telemachus.metrics` are **normative**: everything in them
fills a manifest field or serves a validation rule, and moves only with the
specification. `telemachus.analysis` is the **convenience** tier: maintained,
outside the specified perimeter, free to evolve. What lives there answers a
question by making a decision — where a trip begins, what counts as a stop —
rather than by reading a property of the data. The rule and its worked
application to the whole library are in SPEC-04 §5.3.

```python
from telemachus.metrics  import haversine_m, gap_profile   # spec-bound
from telemachus.analysis import segment_trips, stops       # decisions
```

## Specifications (v1.0)

The spec was consolidated in April 2026 from 10 RFCs into 4 pillars:

| SPEC | Title | Scope |
|------|-------|-------|
| [SPEC-01](spec/SPEC-01-record-format.md) | Telemachus Record Format | Column definitions, functional groups (GNSS, IMU, Vehicle I/O), validation rules, hardware mapping |
| [SPEC-02](spec/SPEC-02-manifest.md) | Dataset Manifest | manifest.yaml schema, sensors, AccPeriods, CarrierState, inheritance rules |
| [SPEC-03](spec/SPEC-03-adapters-validation.md) | Adapters & Validation | Adapter interface, Open dataset specs (AEGIS/PVS/STRIDE), validation framework, CLI |
| [SPEC-04](spec/SPEC-04-governance.md) | Governance & Versioning | Versioning model, release checklist, IP channel separation |

Previous RFCs (0001→0014) are archived in [`spec/rfcs/`](spec/rfcs/) with deprecation notices pointing to the corresponding SPEC.

## Citation

```
S. Edet (2026). Telemachus v1.0 — Specification and Python SDK. Zenodo.
https://doi.org/10.5281/zenodo.21959388

Concept DOI: resolves to the latest release. The v0.8 specification keeps its
own version DOI, [10.5281/zenodo.19609019](https://doi.org/10.5281/zenodo.19609019),
which remains the right thing to cite for a result produced against v0.8.
```

Open datasets shipped in Telemachus format:

- **AEGIS** (Austria, GNSS+IMU+Gyro+OBD, CC-BY-4.0) — [10.5281/zenodo.19609044](https://doi.org/10.5281/zenodo.19609044)
- **STRIDE** (Bangladesh, smartphone 100 Hz, CC-BY-4.0) — [10.5281/zenodo.19609053](https://doi.org/10.5281/zenodo.19609053)
- **RS3** (Le Havre synthetic, CC0-1.0) — [10.5281/zenodo.19609057](https://doi.org/10.5281/zenodo.19609057)

## License

| What | Licence | Why |
|------|---------|-----|
| Specification (SPEC-01→04), schemas, docs | [MIT](LICENSE) | Implement it anywhere, in anything, with no obligation |
| Python SDK and CLI | [Apache-2.0](python-sdk/LICENSE) | Permissive **plus an explicit patent grant**, so a legal department can approve it without a review cycle |
| Datasets | CC-BY / CC0, per-file | See each dataset's `manifest.yaml` |

**The library is deliberately permissive, and that is a decision rather than an
oversight.** A format's reference implementation is how everyone reads and
writes the format; putting copyleft on it taxes the one thing the project wants
to spread. Lossless audio settled this two decades ago — the reference library
went permissive precisely so that closed players could read the format, and the
format won because of it.

Apache-2.0 rather than MIT for the code, for one reason that matters here: it
grants a patent licence over **what is in the SDK** and terminates it for anyone
who sues over patents. Adopters get certainty about the library; nothing is
granted about methods that are not in it. The specification stays MIT, which is
silent on patents — and by construction it describes no protected method, since
SPEC-04 §5.2.1 keeps reconstruction out of scope.
