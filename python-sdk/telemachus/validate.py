"""
Validation utilities for Telemachus datasets (v0.1).

This module validates a dataset described by a YAML manifest (dataset.yaml)
and a set of Parquet tables (trajectory/imu/events/...).

Key entry points:
- validate_manifest(manifest_path) -> (ok: bool, report: str)
- summarize_dataset(manifest_path) -> str

Backward-compat note:
The previous implementation validated JSON/JSONL records against a remote Draft-7 schema.
Telemachus v0.1 now uses a local YAML manifest + Parquet tables. For convenience, a thin
`validate()` wrapper is provided to keep a similar return signature.
"""

from __future__ import annotations

import os
from typing import Tuple

import yaml
import pyarrow.parquet as pq
from jsonschema import Draft202012Validator

from .models import Manifest
from .schemas.manifest_schema import MANIFEST_SCHEMA


def _load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _check_parquet(path: str) -> Tuple[bool, str]:
    try:
        pq.ParquetFile(path)  # lightweight read of metadata
        return True, ""
    except Exception as e:
        return False, f"Cannot read Parquet '{path}': {e}"


def validate_manifest(manifest_path: str) -> tuple[bool, str]:
    """
    Validate a Telemachus manifest and referenced Parquet tables.

    Returns:
        (ok, report)
        ok: bool indicating success
        report: human-readable summary of validation outcome
    """
    if not os.path.exists(manifest_path):
        return False, f"❌ Manifest not found: {manifest_path}"

    data = _load_yaml(manifest_path)

    # 1) JSON Schema structure validation
    errors = sorted(Draft202012Validator(MANIFEST_SCHEMA).iter_errors(data), key=lambda e: e.path)
    if errors:
        report = "\n".join([f"- {e.message} @ {list(e.path)}" for e in errors])
        return False, f"❌ Schema errors:\n{report}"

    # 2) Pydantic semantic checks
    try:
        manifest = Manifest(**data)
    except Exception as e:
        return False, f"❌ Manifest semantic validation failed: {e}"

    # 3) Parquet tables existence + readability
    base = os.path.dirname(os.path.abspath(manifest_path))
    missing = []
    unreadable = []
    for t in manifest.tables:
        table_path = os.path.join(base, t.path)
        if not os.path.exists(table_path):
            missing.append(table_path)
            continue
        ok, err = _check_parquet(table_path)
        if not ok:
            unreadable.append(err)

    if missing or unreadable:
        parts = []
        if missing:
            parts.append("Missing tables:\n" + "\n".join(f"- {p}" for p in missing))
        if unreadable:
            parts.append("Unreadable tables:\n" + "\n".join(f"- {e}" for e in unreadable))
        return False, "❌ Parquet issues detected:\n" + "\n".join(parts)

    return True, f"✅ Manifest OK — {manifest.dataset_id} (freq={manifest.frequency_hz}Hz, tables={len(manifest.tables)})"


def summarize_dataset(manifest_path: str) -> str:
    """
    Produce a short textual summary (rows, columns) for each table in the dataset.
    """
    if not os.path.exists(manifest_path):
        return f"❌ Manifest not found: {manifest_path}"

    data = _load_yaml(manifest_path)
    base = os.path.dirname(os.path.abspath(manifest_path))

    try:
        m = Manifest(**data)
    except Exception as e:
        return f"❌ Manifest semantic validation failed: {e}"

    lines = [f"Dataset: {m.dataset_id} — freq={m.frequency_hz}Hz"]
    for t in m.tables:
        p = os.path.join(base, t.path)
        if not os.path.exists(p):
            lines.append(f"- {t.name}: MISSING ({p})")
            continue
        try:
            pf = pq.ParquetFile(p)
            rows = pf.metadata.num_rows
            cols = pf.schema_arrow.names
            lines.append(f"- {t.name}: {rows} rows, cols={list(cols)}")
        except Exception as e:
            lines.append(f"- {t.name}: ERROR reading ({e})")
    return "\n".join(lines)


# ---- Compatibility wrapper ----

def validate(path: str, schema: str | None = None) -> dict:
    """
    Compatibility wrapper to keep a dict-style response for callers used to the old API.

    If `path` is a YAML file (manifest), run the v0.1 manifest validation.
    Otherwise, return a helpful error directing users to the new workflow.
    """
    if path.lower().endswith((".yml", ".yaml")):
        ok, report = validate_manifest(path)
        return {"ok": ok, "errors": [] if ok else [report]}
    return {
        "ok": False,
        "errors": [
            "Telemachus v0.1 validates YAML manifests + Parquet tables. "
            "Provide a dataset.yaml path (see tele validate <manifest>)."
        ],
    }