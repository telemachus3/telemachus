import json
import jsonschema

def validate(path: str, schema_path: str = "schemas/telemachus.schema.json"):
    with open(schema_path) as f:
        schema = json.load(f)
    with open(path) as f:
        data = [json.loads(line) for line in f]
    validator = jsonschema.Draft7Validator(schema)
    errors = [list(validator.iter_errors(d)) for d in data]
    return errors