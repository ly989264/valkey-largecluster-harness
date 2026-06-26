# Architecture Overview

The harness is organized around explicit separation of inventory, scenario, execution, metrics, validation, artifact writing, and reporting responsibilities. This keeps cluster behavior reusable across N Mac hosts first while leaving room for Linux host adapters later.

## Core Boundaries

- `harness`: owns scenario planning, validation flow, artifact contracts, report generation, and orchestration interfaces.
- `nodehost`: owns host-level adapters for platform-specific operations such as process control, filesystem access, metrics collection, and command execution.
- `inventories`: will hold host, hardware, network, storage, and access configuration supplied by users.
- `scenarios`: will hold validation intent, including node counts, traffic profiles, durations, topology size, and virtual AZ placement intent.
- `artifacts`: will hold generated JSONL events and final reports for local runs or caller-provided output directories.

## Data Flow

1. Inventory data describes available host resources and required hardware facts.
2. Scenario data describes the requested validation run and node count parameters.
3. The planner combines inventory and scenario data into an idempotent execution plan.
4. Execution adapters apply the plan through platform-specific host operations.
5. Collectors emit measured metrics as timestamped JSONL events.
6. Validators evaluate configured values, measured values, skipped checks, failed checks, and `MISSING` metrics.
7. The reporter writes a final human-readable report for the run, including partial results on failure.

No real Valkey control logic is implemented in this skeleton.
