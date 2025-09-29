# tests/test_tcs.py
import pandas as pd
from telemachus.validate import score_completeness
def test_tcs_missing_fields():
    df = pd.DataFrame([{"timestamp":"2025-01-01T00:00:00Z",
                        "vehicle_id":"V1",
                        "position.lat":48.85, "position.lon":2.35}])
    res = score_completeness(df)
    assert 0 < res["score_pct"] < 100
    assert res["coverage"]["position.altitude_m"] == 0.0