# Telemachus Python SDK

Python SDK for loading and validating **Telemachus Core** data.  
Provides easy conversion to DataFrame, Parquet, and GeoJSON.

## Quickstart

```bash
pip install -e .
```

```python
from telemachus import load_jsonl, validate

df = load_jsonl("examples/geotab.jsonl")
report = validate("examples/geotab.jsonl")
print(df.head())
print(report)
```

## License
AGPL-3.0
