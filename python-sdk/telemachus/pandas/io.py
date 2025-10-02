from __future__ import annotations

from typing import Optional

import pandas as pd


def read_parquet_df(path: str, *, columns: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Read a Telemachus table from Parquet into pandas.
    Ensures timestamp is UTC-aware if present.
    """
    df = pd.read_parquet(path, columns=columns)
    if "timestamp" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def write_parquet_df(df: pd.DataFrame, path: str, *, index: bool = False, compression: str = "snappy") -> None:
    """
    Write a pandas DataFrame to Parquet (arrow-friendly).
    """
    df.to_parquet(path, index=index, compression=compression)


def read_csv_df(path: str, *, dtype: Optional[dict] = None, tz_utc: bool = True) -> pd.DataFrame:
    """
    Read a CSV into pandas, with optional type hints.
    If a 'timestamp' column exists, parse to UTC.
    """
    df = pd.read_csv(path, dtype=dtype)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=tz_utc, errors="coerce")
    return df


def write_csv_df(df: pd.DataFrame, path: str, *, index: bool = False) -> None:
    df.to_csv(path, index=index)