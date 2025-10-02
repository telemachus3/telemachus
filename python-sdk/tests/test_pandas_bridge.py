from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from telemachus.pandas import (
    read_parquet_df,
    write_parquet_df,
    validate_df_against_arrow_schema,
    Frame,
)

# For tests, we assume 'trajectory' is a known table in TABLE_SCHEMAS with at least:
# timestamp (timestamp), lat (float), lon (float)
# Adjust columns if your official schema differs.


def _synthetic_traj_df(n=10, start="2025-01-01T00:00:00Z"):
    ts = pd.date_range(start=start, periods=n, freq="1s", tz="UTC")
    lat = 48.0 + np.linspace(0, 0.001, n)
    lon = 2.0 + np.linspace(0, 0.001, n)
    # required by trajectory schema: timestamp_ns, speed_mps, alt (and timestamp/lat/lon)
    ts_ns = ts.view("int64")
    speed = np.full(n, 0.0, dtype="float32")
    alt = np.zeros(n, dtype="float32")
    df = pd.DataFrame({
        "timestamp": ts,
        "timestamp_ns": ts_ns,
        "lat": lat,
        "lon": lon,
        "speed_mps": speed,
        "alt": alt,
    })
    return df


def test_roundtrip_parquet(tmp_path: Path):
    df = _synthetic_traj_df(n=16)
    p = tmp_path / "traj.parquet"
    write_parquet_df(df, p.as_posix())
    df2 = read_parquet_df(p.as_posix())
    assert len(df2) == 16
    assert "timestamp" in df2.columns


def test_validate_against_arrow_schema_soft_and_strict():
    df = _synthetic_traj_df(n=5)
    # soft: allow casts & extra columns (by default)
    validate_df_against_arrow_schema("trajectory", df, strict_types=False, allow_extra_columns=True)

    # strict types (if a cast is needed, may fail depending on the concrete schema)
    validate_df_against_arrow_schema("trajectory", df.astype({"lat": "float64"}), strict_types=True)


def test_frame_facade():
    df = _synthetic_traj_df(n=8)
    f = Frame.from_df("trajectory", df, validate=True)
    assert len(f.df) == 8
    # add an extra column and revalidate (allowed by default)
    f2 = f.with_column("extra_note", ["x"] * len(f.df))
    f2.validate(allow_extra_columns=True)