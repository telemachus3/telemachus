from telemachus.io import load_jsonl

def test_load_jsonl():
    df = load_jsonl("examples/geotab.jsonl")
    assert not df.empty