from __future__ import annotations

from typing import Optional, Set

import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd

def _resolve_table_schemas():
    """Lazily resolve a dict-like registry of PyArrow schemas from telemachus.core.schemas.
    Strategy:
    1) import telemachus.core.schemas as mod
    2) try common dict names TABLE_SCHEMAS/SCHEMAS/TABLES/ARROW_SCHEMAS/SCHEMA_REGISTRY
    3) otherwise, BUILD a registry from individual pa.Schema attributes (e.g., TRAJECTORY_SCHEMA)
    """
    try:
        from telemachus.core import schemas as _schemas
    except Exception as _e:
        raise ImportError("Cannot import telemachus.core.schemas module") from _e
    # 2) Direct-known dict names
    for name in ("TABLE_SCHEMAS", "SCHEMAS", "TABLES", "ARROW_SCHEMAS", "SCHEMA_REGISTRY"):
        reg = getattr(_schemas, name, None)
        if isinstance(reg, dict):
            try:
                if all(isinstance(v, pa.Schema) for v in reg.values()):
                    return reg
            except Exception:
                pass
    # 3) Build from individual pa.Schema attributes
    built = {}
    for attr in dir(_schemas):
        obj = getattr(_schemas, attr)
        if isinstance(obj, pa.Schema):
            # derive table name from attribute, e.g. TRAJECTORY_SCHEMA -> "trajectory"
            name = attr.lower()
            if name.endswith("_schema"):
                name = name[:-7]
            # common prefixes/suffixes cleanup
            for prefix in ("tele_", "telemahcus_", "telemachus_", "tbl_", "table_"):
                if name.startswith(prefix):
                    name = name[len(prefix):]
            built[name] = obj
    if built:
        return built
    raise ImportError(
        "No suitable PyArrow schema registry found in telemachus.core.schemas. "
        "Expected a dict[str, pa.Schema] (e.g., TABLE_SCHEMAS) or individual *_SCHEMA symbols."
    )


def _cast_table_to_schema(tbl: pa.Table, schema: pa.Schema, strict_types: bool) -> pa.Table:
    """
    Try to cast each column to the expected PyArrow type when not matching.
    If strict_types=True, raise on mismatch instead of attempting casts.
    """
    cols = []
    for field in schema:
        name = field.name
        if name not in tbl.column_names:
            raise ValueError(f"Missing required column: {name}")

        col = tbl[name]
        col_type = col.type
        exp_type = field.type

        if col_type.equals(exp_type):
            cols.append(col)
            continue

        if strict_types:
            raise TypeError(f"Incompatible dtype for '{name}': got {col_type}, expected {exp_type}")

        try:
            casted = pc.cast(col, exp_type)
            cols.append(casted)
        except Exception as e:
            raise TypeError(
                f"Failed casting column '{name}' from {col_type} to {exp_type}: {e}"
            ) from e

    # reorder to match schema; drop extras later if present
    tbl2 = pa.table(cols, schema=schema)
    return tbl2


def validate_df_against_arrow_schema(
    table: str,
    df: pd.DataFrame,
    *,
    strict_types: bool = False,
    allow_extra_columns: bool = True,
) -> None:
    """
    Validate a pandas DataFrame against the official PyArrow schema of a Telemachus table.

    - No schema duplication: TABLE_SCHEMAS[table] is the single source of truth.
    - If allow_extra_columns=False: raises if DataFrame has columns not present in schema.
    - If strict_types=True: fails on any dtype mismatch (no casting attempt).
    """
    TABLE_SCHEMAS = _resolve_table_schemas()
    if table not in TABLE_SCHEMAS:
        raise KeyError(f"Unknown Telemachus table '{table}'. Known: {list(TABLE_SCHEMAS)}")

    schema = TABLE_SCHEMAS[table]  # pyarrow.Schema
    tbl = pa.Table.from_pandas(df, preserve_index=False)

    # Column existence & optional extras
    expected: Set[str] = {f.name for f in schema}
    got: Set[str] = set(tbl.schema.names)
    missing = expected - got
    extra = got - expected

    if missing:
        raise ValueError(f"Missing columns for '{table}': {sorted(missing)}")
    if extra and not allow_extra_columns:
        raise ValueError(f"Unexpected columns for '{table}': {sorted(extra)}")

    # Strict/soft type checking
    _ = _cast_table_to_schema(tbl, schema, strict_types=strict_types)

    # Domain checks that are schema-agnostic (lightweight)
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        if ts.isna().any():
            raise ValueError("Invalid timestamps (NaT found after UTC coercion)")
        # monotonic non-decreasing recommended (not enforced here)
    if "lat" in df.columns and not ((df["lat"] >= -90.0) & (df["lat"] <= 90.0)).all():
        raise ValueError("lat out of range [-90, 90]")
    if "lon" in df.columns and not ((df["lon"] >= -180.0) & (df["lon"] <= 180.0)).all():
        raise ValueError("lon out of range [-180, 180]")