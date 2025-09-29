# tests/test_dataset.py
from telemachus.dataset import TelemachusDataset
def test_dataset_flow(tmp_path):
    j = tmp_path/"data.json"
    j.write_text('{"timestamp":"2025-01-01T00:00:00Z","vehicle_id":"V1","position":{"lat":1,"lon":2}}')
    ds = TelemachusDataset.from_jsonl(str(j))
    summary = ds.summary()
    assert summary["rows"]==1