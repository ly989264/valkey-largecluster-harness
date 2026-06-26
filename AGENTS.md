# AGENTS.md

## Project Goal

Build a reusable Valkey 9.x large-cluster validation harness for N Mac hosts first, with fast migration to Linux hosts later.

The harness must validate large Valkey clusters across user-defined scenarios, inventories, and node counts while producing machine-readable artifacts and a human-readable final report for every run.

## Repo Layout

This repository is currently in the guidance phase. Do not create code, scripts, package manifests, fixtures, or generated artifacts until implementation work is explicitly requested.

When implementation starts, use this layout unless the codebase grows a clearly better local convention:

- `AGENTS.md`: repository-wide engineering rules and review contract.
- `README.md`: user-facing overview and quickstart.
- `docs/`: user-facing design notes, operations guides, and scenario documentation. Use `virtual AZ` in user-facing text.
- `inventories/`: host, hardware, network, and access configuration. Hardware details must be injected from inventory files.
- `scenarios/`: scenario definitions, including node counts and validation parameters.
- `src/` or `harness/`: harness implementation, orchestration logic, collectors, validators, and report generation.
- `scripts/`: thin idempotent command wrappers only. Keep logic in the main implementation.
- `tests/`: unit, integration, inventory validation, scenario validation, and report validation tests.
- `artifacts/`: local run outputs. Generated JSONL artifacts and final reports belong here or under a caller-provided output directory.
- `tmp/`: local scratch data. Nothing here should be required for correctness.

Generated artifacts, host-specific inventories, secrets, private keys, logs, temporary files, and large binaries must not be committed unless explicitly documented as safe test fixtures.

## Ownership Rules

- Keep project behavior reusable across N Mac hosts first and Linux hosts later.
- Treat Mac-specific behavior as a platform adapter, not as a permanent assumption in core logic.
- Keep inventory, scenario, execution, metrics, validation, artifact writing, and reporting responsibilities separate.
- Hardware details must come from inventory files. Do not hard-code host counts, CPU layout, memory size, disk layout, NIC names, IP ranges, or OS-specific paths in scenario logic.
- Node counts must be scenario parameters. Do not bake node counts into implementation defaults, test fixtures, or documentation examples without marking them as examples.
- Use English for all code identifiers, filenames, command names, JSON keys, and config keys.
- Use Chinese comments only where they materially clarify non-obvious implementation details.
- Do not use Docker-in-Docker.
- Do not run one container per Valkey node.
- Use `virtual AZ` as the user-facing term in docs, CLI output, reports, and examples.
- Missing metrics must be emitted and reported as `MISSING`. Never infer, synthesize, or silently omit missing metric values.

## Build And Test Commands

No build or test tooling exists yet. Until implementation is requested, do not add placeholder code just to make these commands work.

When tooling is added, expose these idempotent commands or documented equivalents:

- `make fmt`: format repository files.
- `make lint`: run static checks.
- `make test`: run the default test suite.
- `make test-unit`: run unit tests only.
- `make test-integration`: run integration tests that do not require destructive host changes.
- `make validate-inventory INVENTORY=<path>`: validate inventory shape and required hardware data.
- `make validate-scenario SCENARIO=<path>`: validate scenario shape, including node count parameters.
- `make plan INVENTORY=<path> SCENARIO=<path> OUT_DIR=<path>`: produce an idempotent execution plan without changing hosts.
- `make run INVENTORY=<path> SCENARIO=<path> OUT_DIR=<path>`: run a validation scenario and emit JSONL artifacts plus a final report.
- `make clean OUT_DIR=<path> --apply`: remove generated local outputs only when `--apply` is present.

All commands must be safe to retry. Commands that modify hosts, remove data, reset state, stop services, kill processes, or delete artifacts must require an explicit `--apply` flag and must support a non-destructive plan or dry-run mode.

## Implementation Constraints

- Design for multi-host operation from the start. Local-only execution may exist for tests, but it must not shape the public architecture.
- Keep host inventory external and explicit. The harness should fail validation when required inventory data is absent.
- Keep scenario files responsible for node counts, topology size, validation duration, traffic profile, and virtual AZ placement intent.
- Prefer structured configuration and structured parsing over shell text scraping.
- Use stable, idempotent command semantics. Re-running a command with the same inventory, scenario, and output path must not corrupt previous results.
- Every run must emit JSONL artifacts and a final report, even on failure. Failure reports should include the failure phase, partial artifacts, and missing data marked as `MISSING`.
- JSONL events must be append-safe, timestamped, and include enough run identity to correlate events with the final report.
- Reports must distinguish measured values, configured values, skipped checks, failed checks, and `MISSING` metrics.
- Do not invent metrics, capacities, host properties, Valkey versions, cluster state, or timing data.
- Do not rely on Docker-in-Docker or one-container-per-node designs.
- Keep destructive behavior behind `--apply`, with clear planned actions before execution.
- Keep secrets out of command output, artifacts, reports, and committed files.
- Design platform-specific operations behind adapters so Mac host support can be followed by Linux host support without rewriting scenario logic.

## Completion Criteria

A change is complete only when:

- It preserves the hard rules in this file.
- It updates documentation when user-facing behavior changes.
- It includes focused tests for changed behavior, or explains why tests are not applicable.
- It keeps commands idempotent and verifies destructive paths require `--apply`.
- It validates inventory-driven hardware data and scenario-driven node counts.
- It emits JSONL artifacts and a final report for each run path touched by the change.
- It reports missing metrics as `MISSING`.
- It does not introduce Docker-in-Docker or one-container-per-node assumptions.
- It does not expose secrets in logs, artifacts, reports, or docs.

## Review Checklist

Before approving or merging a change, verify:

- Only intended files changed.
- User-facing docs and CLI output use `virtual AZ`.
- Hardware details are read from inventory files.
- Node counts are scenario parameters.
- Commands are idempotent and retry-safe.
- Destructive operations require `--apply`.
- Every run path emits JSONL artifacts and a final report.
- Missing metrics are represented exactly as `MISSING`.
- Metrics and report values are measured or configured, not invented.
- Mac-first behavior is isolated from core logic where Linux migration will need a different adapter.
- No Docker-in-Docker design was added.
- No one-container-per-node design was added.
- Tests cover the behavior changed, including failure and missing-metric paths when relevant.
- Generated artifacts, secrets, local inventories, and temporary files are not committed accidentally.
