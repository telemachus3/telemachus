"""
Pandas bridge for Telemachus.

Utilities to:
- load/save pandas DataFrames for Telemachus tables
- validate DataFrames against the official PyArrow TABLE_SCHEMAS
- provide a lightweight Frame façade (no duplicate schemas)
"""

from .io import read_parquet_df, read_csv_df, write_parquet_df, write_csv_df
from .validate import validate_df_against_arrow_schema
from .frame import Frame

__all__ = [
    "read_parquet_df",
    "read_csv_df",
    "write_parquet_df",
    "write_csv_df",
    "validate_df_against_arrow_schema",
    "Frame",
]