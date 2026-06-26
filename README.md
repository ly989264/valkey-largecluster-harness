# Valkey Large-Cluster Harness

This repository is the skeleton for a reusable Valkey 9.x large-cluster validation harness. The target architecture is Mac hosts first, with platform-specific behavior isolated so Linux hosts can be added later without reshaping scenario logic.

The harness will validate user-defined cluster scenarios against explicit host inventories, produce append-safe JSONL artifacts, and write a human-readable final report for every run path. Real Valkey orchestration, schemas, collectors, validators, and report generation are intentionally not implemented yet.

## Configuration Model

The harness will be driven by two user-owned files:

- `inventory.yaml`: describes the available hosts, access method, hardware, operating system, network, storage, and other measured or configured host properties. Hardware details must come from inventory data rather than scenario logic.
- `scenario.yaml`: describes the validation intent, including node counts, topology size, validation duration, traffic profile, and virtual AZ placement intent.

Inventory answers what resources exist. Scenario answers what validation run should be planned on those resources.

## Development

Install development dependencies in your preferred Python environment:

```sh
python -m pip install -e ".[dev]"
```

Run the test suite:

```sh
make test
```

Direct pytest invocation is also supported:

```sh
python -m pytest
```

## Status

This is an initial repository skeleton. It deliberately does not include Valkey control logic, schemas, Dockerfiles, generated artifacts, private inventories, or host-specific assumptions.
