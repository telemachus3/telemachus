from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd
import yaml
from jsonschema import validate as json_validate

from telemachus.schemas.manifest_schema import MANIFEST_JSON_SCHEMA  # existing JSON Schema
from telemachus.pandas.io import read_parquet_df
from telemachus.pandas.validate import validate_df_against_arrow_schema


@dataclass(slots=True)
class Dataset:
    """
    High-level façade over a Telemachus dataset directory.

    Responsibilities:
    - load and validate dataset manifest (dataset.yaml) with JSON Schema
    - provide accessors to read pandas DataFrames for tables
    - validate all tables against PyArrow schemas
    - compute a simple summary (rows, time-span) for convenience
    """
    root: Path
    manifest: dict

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "Dataset":
        mpath = Path(manifest_path)
        root = mpath.parent
        with open(mpath, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        json_validate(instance=manifest, schema=MANIFEST_JSON_SCHEMA)
        return cls(root=root, manifest=manifest)

    @property
    def tables(self) -> Dict[str, str]:
        """
        Return mapping: table_name -> relative path (as declared in manifest).
        """
        entries = self.manifest.get("tables", [])
        return {e["name"]: e["path"] for e in entries}

    def table_path(self, name: str) -> Path:
        if name not in self.tables:
            raise KeyError(f"Unknown table '{name}'. Known: {list(self.tables)}")
        return (self.root / self.tables[name]).resolve()

    def read_df(self, name: str, columns: list[str] | None = None) -> pd.DataFrame:
        return read_parquet_df(self.table_path(name).as_posix(), columns=columns)

    def validate_all(self, *, strict_types: bool = False, allow_extra_columns: bool = True) -> None:
        for name in self.tables.keys():
            df = self.read_df(name)
            validate_df_against_arrow_schema(
                name, df,
                strict_types=strict_types,
                allow_extra_columns=allow_extra_columns,
            )

    def summary(self) -> Dict[str, dict]:
        """
        Return per-table summary: rows, time_span (if timestamp present), and columns.
        """
        out: Dict[str, dict] = {}
        for name in self.tables.keys():
            df = self.read_df(name)
            info = {"rows": int(len(df)), "columns": list(df.columns)}
            if "timestamp" in df.columns:
                ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
                info["time_span"] = {
                    "start": ts.min().isoformat() if len(ts) else None,
                    "end": ts.max().isoformat() if len(ts) else None,
                }
            out[name] = info
        return out