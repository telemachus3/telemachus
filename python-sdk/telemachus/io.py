import pandas as pd
import json

def load_jsonl(path: str) -> pd.DataFrame:
    records = []
    with open(path, "r") as f:
        for line in f:
            records.append(json.loads(line))
    return pd.json_normalize(records)