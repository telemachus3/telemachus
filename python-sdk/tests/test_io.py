# tests/test_io.py
from telemachus.io import load_jsonl
def test_load_json_single_object(tmp_path):
    p = tmp_path/"one.json"
    p.write_text('{"timestamp":"2025-01-01T00:00:00Z","vehicle_id":"V1","position":{"lat":1,"lon":2}}')
    df = load_jsonl(str(p))
    assert len(df)==1
    assert "position.lat" in df.columns