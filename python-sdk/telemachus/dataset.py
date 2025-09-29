

from typing import Optional, Iterable, Dict, Any, List
import json
import pandas as pd
from pandas import Timestamp
from telemachus.io import load_jsonl
from telemachus.validate import validate, to_parquet, from_parquet, score_completeness


class TelemachusDataset:
    """
    Object-oriented interface for working with Telemachus Core datasets.
    Provides methods for loading, validating, scoring, and exporting telematics data.
    """

    def __init__(self, path: str, schema: str | None = None):
        self.path = path
        self.schema = schema
        self.df: pd.DataFrame | None = None
        self.validation_report: dict | None = None

    def load(self):
        """Load a JSON or JSONL file into a pandas DataFrame."""
        self.df = load_jsonl(self.path)
        return self

    def validate(self):
        """Validate the file against the Telemachus schema."""
        self.validation_report = validate(self.path)
        return self

    def completeness(self):
        """Compute Telemahus Completeness Score (TCS) on the loaded DataFrame."""
        if self.df is None:
            self.load()
        return score_completeness(self.df)

    def to_parquet(self, out_path: str):
        """Export the dataset to a Parquet file after validation."""
        return to_parquet(self.path, out_path, self.schema)

    @classmethod
    def from_parquet(cls, parquet_path: str):
        """Create a TelemachusDataset object from a Parquet file."""
        obj = cls(path=parquet_path)
        obj.df = from_parquet(parquet_path)
        return obj

    # ---- Convenience constructors ----
    @classmethod
    def from_jsonl(cls, path: str, schema: Optional[str] = None):
        """Create and load a dataset from a JSON/JSONL file."""
        obj = cls(path=path, schema=schema)
        return obj.load()

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, schema: Optional[str] = None):
        """Create a dataset from an in-memory DataFrame."""
        obj = cls(path="", schema=schema)
        obj.df = df.copy()
        return obj

    @classmethod
    def from_records(cls, records: Iterable[Dict[str, Any]], schema: Optional[str] = None):
        """Create a dataset from an iterable of dict records."""
        df = pd.json_normalize(list(records))
        return cls.from_dataframe(df, schema=schema)

    # ---- Configuration helpers ----
    def with_schema(self, schema: Optional[str]):
        """Fluent setter for schema URL/path."""
        self.schema = schema
        return self

    # ---- Data manipulation ----
    def _ensure_loaded(self):
        if self.df is None:
            self.load()

    def filter_time(self, start: Optional[str] = None, end: Optional[str] = None):
        """Filter rows by timestamp ISO-8601 (UTC)."""
        self._ensure_loaded()
        if "timestamp" not in self.df.columns:
            return self
        ts = pd.to_datetime(self.df["timestamp"], utc=True, errors="coerce")
        mask = pd.Series(True, index=self.df.index)
        if start:
            mask &= ts >= pd.to_datetime(start, utc=True)
        if end:
            mask &= ts <= pd.to_datetime(end, utc=True)
        self.df = self.df.loc[mask].reset_index(drop=True)
        return self

    def select_fields(self, fields: List[str]):
        """Keep only selected flattened columns (e.g., 'position.lat')."""
        self._ensure_loaded()
        keep = [c for c in fields if c in self.df.columns]
        self.df = self.df[keep].copy()
        return self

    def add_context(self, name: str, context: Dict[str, Any]):
        """Broadcast a context dict under the 'context.<name>.*' namespace as columns."""
        self._ensure_loaded()
        for k, v in context.items():
            self.df[f"context.{name}.{k}"] = v
        return self

    def map_provider(self, mapping: Dict[str, str], inplace: bool = True):
        """Rename provider-specific columns to Telemachus Core names using a mapping dict."""
        self._ensure_loaded()
        new_df = self.df.rename(columns=mapping)
        if inplace:
            self.df = new_df
            return self
        return TelemachusDataset.from_dataframe(new_df, schema=self.schema)

    # ---- Persistence ----
    def to_jsonl(self, out_path: str):
        """Write current DataFrame to JSON Lines (flattened records)."""
        self._ensure_loaded()
        with open(out_path, "w") as f:
            for rec in self.df.to_dict(orient="records"):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return out_path

    def save_parquet(self, out_path: str, validate_before: bool = False):
        """Export current DataFrame to Parquet. Optionally validate the original file before export."""
        self._ensure_loaded()
        if validate_before and self.path:
            _ = validate(self.path)
        self.df.to_parquet(out_path, index=False)
        return out_path

    # ---- Reporting ----
    def summary(self) -> Dict[str, Any]:
        """Basic dataset summary (rows, columns, time span)."""
        self._ensure_loaded()
        info: Dict[str, Any] = {
            "rows": int(len(self.df)),
            "columns": sorted(list(self.df.columns)),
        }
        if "timestamp" in self.df.columns:
            ts = pd.to_datetime(self.df["timestamp"], utc=True, errors="coerce")
            info["time_min"] = ts.min().isoformat() if not ts.isna().all() else None
            info["time_max"] = ts.max().isoformat() if not ts.isna().all() else None
        try:
            tcs = self.completeness()
            info["tcs_score_pct"] = tcs.get("score_pct")
        except Exception:
            info["tcs_score_pct"] = None
        return info