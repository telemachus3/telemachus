#!/usr/bin/env python3
import json, pathlib, pandas as pd

def load_dataset(dataset_dir: str) -> tuple[pd.DataFrame, dict]:
    d = pathlib.Path(dataset_dir)
    meta = json.loads((d/"dataset.json").read_text(encoding="utf-8"))
    samples = d/"samples.parquet"
    if samples.exists():
        df = pd.read_parquet(samples)
    else:
        df = pd.read_csv(d/"samples.csv")
    return df, meta

if __name__ == "__main__":
    df, meta = load_dataset("2025-10-01-v1.0")
    print(meta)
    print(df.head())