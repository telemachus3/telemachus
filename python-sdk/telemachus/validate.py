import os, json, jsonschema, urllib.request

DEFAULT_SCHEMA_URL = os.getenv(
    "TELEMACHUS_SCHEMA_URL",
    "https://raw.githubusercontent.com/telemachus3/telemachus-spec/main/schemas/telemachus.schema.json"
)

def _load_schema(schema_path_or_url: str | None = None):
    path = schema_path_or_url or DEFAULT_SCHEMA_URL
    if path.startswith("http"):
        with urllib.request.urlopen(path) as r:
            return json.loads(r.read().decode("utf-8"))
    with open(path) as f:
        return json.load(f)

def validate(path: str, schema: str | None = None):
    schema_obj = _load_schema(schema)
    validator = jsonschema.Draft7Validator(schema_obj)
    with open(path) as f:
        data = [json.loads(line) for line in f]
    errors = []
    for i, rec in enumerate(data):
        errs = list(validator.iter_errors(rec))
        if errs:
            errors.append({"index": i, "errors": [e.message for e in errs]})
    return {"ok": len(errors) == 0, "errors": errors}


# Parquet conversion and completeness scoring utilities
import pandas as pd

def to_parquet(json_path: str, out_path: str, schema: str | None = None):
    """
    Load a JSON or JSONL file, validate records, and export to Parquet.
    """
    schema_obj = _load_schema(schema)
    validator = jsonschema.Draft7Validator(schema_obj)
    records = []
    with open(json_path) as f:
        for i, line in enumerate(f):
            rec = json.loads(line)
            errs = list(validator.iter_errors(rec))
            if errs:
                raise ValueError(f"Validation errors at record {i}: {[e.message for e in errs]}")
            records.append(rec)
    df = pd.json_normalize(records)
    df.to_parquet(out_path, index=False)
    return out_path

def from_parquet(path: str):
    """
    Load a Parquet file into a pandas DataFrame.
    """
    return pd.read_parquet(path)

def score_completeness(df: pd.DataFrame, core_fields: list[str] | None = None) -> dict:
    """
    Compute Telemahus Completeness Score (TCS) for a DataFrame.
    Returns global score (%) and per-field coverage.
    """
    if core_fields is None:
        core_fields = [
            "timestamp",
            "vehicle_id",
            "position.lat",
            "position.lon",
            "position.altitude_m",
            "position.heading_deg",
            "motion.speed_kph",
            "motion.bearing_deg",
            "quality.hdop",
            "quality.vdop",
            "quality.pdop",
            "quality.num_satellites",
            "quality.fix_type",
            "imu.accel.x_ms2",
            "imu.accel.y_ms2",
            "imu.accel.z_ms2",
            "imu.gyro.x_rads",
            "imu.gyro.y_rads",
            "imu.gyro.z_rads",
            "imu.mag.x_ut",
            "imu.mag.y_ut",
            "imu.mag.z_ut",
            "engine.rpm",
            "engine.odometer_km",
            "engine.fuel_pct",
            "engine.fuel_l",
            "engine.fuel_rate_lph",
            "engine.throttle_pct",
            "engine.engine_temp_c",
            "engine.battery_voltage_v"
        ]
    total = len(core_fields)
    coverage = {}
    for field in core_fields:
        coverage[field] = float(df[field].notna().mean()) if field in df.columns else 0.0
    score = sum(coverage.values()) / total * 100
    return {"score_pct": score, "coverage": coverage}