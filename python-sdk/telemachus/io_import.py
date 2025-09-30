

"""
Import utilities to read a Telemachus dataset (v0.1).

This module provides helpers to:
- load an entire dataset (manifest + Parquet tables) into memory
- read a single logical table by name

Conventions:
- The manifest is a YAML file (dataset.yaml) validated elsewhere.
- Table paths in the manifest are relative to the manifest directory.
"""

from __future__ import annotations

import os
from typing import Dict

import pandas as pd
import pyarrow.parquet as pq
import yaml


def _read_parquet(path: str) -> pd.DataFrame:
    """Read a Parquet file into a pandas DataFrame with pyarrow backend."""
    pf = pq.ParquetFile(path)
    return pf.read().to_pandas()


def load_dataset(manifest_path: str) -> Dict[str, object]:
    """
    Load a Telemachus dataset into memory.

    Args:
        manifest_path: path to the dataset.yaml manifest.

    Returns:
        A dict with:
          - "manifest": parsed YAML manifest as a dict
          - "tables": a dict[str, pandas.DataFrame] mapping logical table names to DataFrames
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)

    base = os.path.dirname(os.path.abspath(manifest_path))
    tables: Dict[str, pd.DataFrame] = {}

    for t in manifest.get("tables", []):
        name = t["name"]
        rel = t["path"]
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Table not found: {path} (from {rel})")
        tables[name] = _read_parquet(path)

    return {"manifest": manifest, "tables": tables}


def read_table(manifest_path: str, table_name: str) -> pd.DataFrame:
    """
    Read a single logical table from a Telemachus dataset.

    Args:
        manifest_path: path to the dataset.yaml manifest.
        table_name: logical table name to read (e.g., 'trajectory', 'imu', 'events').

    Returns:
        pandas.DataFrame containing the requested table.

    Raises:
        FileNotFoundError if the manifest or requested table path does not exist.
        KeyError if the table name is not declared in the manifest.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)

    base = os.path.dirname(os.path.abspath(manifest_path))
    lookup = {t["name"]: t for t in manifest.get("tables", [])}

    if table_name not in lookup:
        raise KeyError(f"Table '{table_name}' not declared in manifest.")

    rel = lookup[table_name]["path"]
    path = os.path.join(base, rel)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Table not found: {path} (from {rel})")

    return _read_parquet(path)