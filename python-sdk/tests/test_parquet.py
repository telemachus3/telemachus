# tests/test_parquet.py
from telemachus.validate import to_parquet, from_parquet
def test_parquet_roundtrip(tmp_path):
    j = tmp_path/"data.jsonl"
    j.write_text('{"timestamp":"2025-01-01T00:00:00Z","vehicle_id":"V1","position":{"lat":1,"lon":2}}')
    out = tmp_path/"out.parquet"
    to_parquet(str(j), str(out))
    df2 = from_parquet(str(out))
    assert len(df2)==1