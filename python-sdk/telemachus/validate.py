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