#!/usr/bin/env python3
import sys, json, pathlib
import pandas as pd
REQ = ["timestamp","lat","lon","speed","acc_x","acc_y","acc_z","gyro_x","gyro_y","gyro_z","event","event_infra","event_behavior","event_context"]
def ok_alias(cols): return ("speed" in cols) or ("speed_mps" in cols)
def main(d):
    d=pathlib.Path(d); meta=json.loads((d/"dataset.json").read_text())
    print("[OK] dataset.json loaded:", meta.get("version"))
    pq=d/"samples.parquet"; df=pd.read_parquet(pq) if pq.exists() else pd.read_csv(d/"samples.csv")
    cols=list(df.columns); missing=[c for c in REQ if c not in cols and not (c=="speed" and "speed_mps" in cols)]
    assert ok_alias(cols), "need 'speed' or 'speed_mps'"; assert not missing, f"missing columns: {missing}"
    ts=pd.to_datetime(df["timestamp"], utc=True, errors="coerce"); assert ts.is_monotonic_increasing, "timestamps not monotonic"
    dt=ts.diff().dt.total_seconds().dropna(); hz=1.0/dt.median() if len(dt) else float("nan"); assert abs(hz-10.0)<0.5, f"Hz≈{hz:.2f}"
    assert df["lat"].between(-90,90).all() and df["lon"].between(-180,180).all(), "lat/lon out of range"
    sp=df["speed"] if "speed" in df.columns else df["speed_mps"]; assert (sp>=0).all(), "negative speed"
    print("[OK] basic checks passed ✅")
if __name__=="__main__":
    assert len(sys.argv)==2, "usage: verify.py <dataset_dir>"; main(sys.argv[1])
