"""Small schema checks used by the P02 config loader."""

import json
from pathlib import Path


class SchemaValidationError(ValueError):
    pass


def load_schema(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data, schema, *, path="$"):
    expected_type = schema.get("type")
    if expected_type:
        _check_type(data, expected_type, path)
    for key in schema.get("required", []):
        if not isinstance(data, dict) or key not in data:
            raise SchemaValidationError(f"{path}.{key} is required")
    if isinstance(data, dict):
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in data:
                validate_schema(data[key], subschema, path=f"{path}.{key}")
    if "enum" in schema and data not in schema["enum"]:
        raise SchemaValidationError(f"{path} must be one of {schema['enum']}")
    if isinstance(data, list) and "items" in schema:
        for idx, item in enumerate(data):
            validate_schema(item, schema["items"], path=f"{path}[{idx}]")
    return True


def _check_type(value, expected, path):
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
    }
    py_type = mapping[expected]
    if not isinstance(value, py_type) or (expected == "integer" and isinstance(value, bool)):
        raise SchemaValidationError(f"{path} must be {expected}")
