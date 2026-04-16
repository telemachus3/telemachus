# Manifest FAQ

Common questions about the **Dataset Manifest** (SPEC-02, v0.8 Draft).

## Why a manifest?

The Telemachus contract (SPEC-01 §3.1) declares `device_id`, `trip_id`,
`acc_periods` and `trip_carrier_states` as **per-file** rather than
per-row. They have to live somewhere. Before SPEC-02, producers
emitted them ad-hoc (env var, config, sidecar JSON…). The manifest
formalises that sidecar.

## Where does the manifest sit?

Next to the parquet(s):

```
my-dataset/
├── manifest.yaml      ← here
├── d0_xxx.parquet
└── d0_yyy.parquet
```

YAML is preferred (human-friendly). JSON with the same schema is also
accepted by validators.

## Inheritance — what columns can I omit from the parquet?

If the manifest declares them, you can omit:

| Column | Manifest source |
|--------|-----------------|
| `device_id` | `hardware.devices[0].name` (single-device datasets) |
| `trip_id`   | parquet filename suffix or `source.campaign + basename` |
| `carrier_state` | matched per `trip_id` from `trip_carrier_states` |

For multi-device datasets, `device_id` MUST be either per-row or
encoded in the filename (`d0_<device>_*.parquet`). See SPEC-02 §4.1.

## How is the accelerometer frame applied?

For each row at timestamp `ts`, the consumer finds the first
`acc_periods` entry where `start ≤ ts ≤ end` and uses its `frame`
(`raw`, `compensated` or `partial`). If no `acc_periods` declared,
the default is `raw` (SPEC-01 §3.6).

## Dataset licenses

The manifest carries `license` (free SPDX-style string) and an
optional `license_warning`. Common cases:

| License | Republish modified | Manifest hint |
|---------|--------------------|---------------|
| CC-BY-4.0 | ✅ with attribution | `license: "CC-BY-4.0"` |
| CC-BY-NC-ND-4.0 | ❌ ND forbids derivatives | `license: "CC-BY-NC-ND-4.0"`, `license_warning: "Non-commercial, no derivatives"` |
| CC0 | ✅ everything | `license: "CC0-1.0"` |
| Internal / proprietary | ❌ | `license: "internal"` |

Future tooling will add a `license_republish_derivative:
{allowed,forbidden,academic}` field plus a CI linter that refuses to
commit converted parquet under a `forbidden` source. For now, this
is enforced by convention — see [Writing an adapter →
Licensing pitfall](writing-adapter.md#licensing-pitfall).

## What about per-row metadata that varies?

Anything that genuinely varies per row stays per-row in the parquet
(e.g. `lat`, `ax_mps2`). The manifest is for **file-level** metadata
that doesn't vary, OR for time-segmented metadata (`acc_periods`,
config history) that varies on coarse boundaries.

## My manifest fails validation — where do I look?

Run the validator with verbose output:

```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json \
             -d manifest.yaml --errors=text --all-errors
```

Common pitfalls:

- `start: 2025-01-01` (YAML auto-parses this to a date) → quote it: `"2025-01-01T00:00:00Z"`
- `n_trips: null` is fine — most counts accept null as "unknown"
- Unknown enum values for `hardware.class` (`research|commercial|consumer|prototype|smartphone`)
- Missing required block: `dataset_id`, `schema_version`, `source`
