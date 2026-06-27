"""Config loading and validation for inventory/scenario inputs."""

import json
from pathlib import Path

from harness.inventory import inventory_from_dict
from harness.mini_yaml import MiniYamlError, parse as parse_yaml
from harness.scenario import scenario_from_dict
from harness.schema_validator import SchemaValidationError, load_schema, validate_schema


ROOT = Path(__file__).resolve().parents[1]


class ConfigError(ValueError):
    pass


def load_document(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        if path.suffix not in {".yaml", ".yml"}:
            raise ConfigError(f"{path}: invalid JSON: {json_error}") from json_error
        try:
            return parse_yaml(text)
        except MiniYamlError as yaml_error:
            raise ConfigError(f"{path}: invalid YAML: {yaml_error}") from yaml_error


def load_inventory(path):
    data = load_document(path)
    schema = load_schema(ROOT / "schemas" / "inventory.schema.json")
    try:
        validate_schema(data, schema)
        return inventory_from_dict(data)
    except (SchemaValidationError, ValueError) as exc:
        raise ConfigError(f"inventory validation failed: {exc}") from exc


def load_scenario(path):
    data = load_document(path)
    schema = load_schema(ROOT / "schemas" / "scenario.schema.json")
    try:
        validate_schema(data, schema)
        return scenario_from_dict(data)
    except (SchemaValidationError, ValueError) as exc:
        raise ConfigError(f"scenario validation failed: {exc}") from exc


def validate_config(inventory_path, scenario_path):
    inventory = load_inventory(inventory_path)
    scenario = load_scenario(scenario_path)
    return {
        "inventory": inventory.to_dict(),
        "scenario": scenario.to_dict(),
        "defaults": {
            "backend": scenario.backend,
            "runtime": inventory.runtime,
            "node_timeout_ms": scenario.cluster.node_timeout_ms,
            "replicas_per_primary": scenario.cluster.replicas_per_primary,
        },
    }
