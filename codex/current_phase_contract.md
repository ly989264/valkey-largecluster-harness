# Current Phase Contract: P02

## Name
配置契约：inventory 与 scenario

## Goal
让 inventory 与 scenario 成为唯一输入源，覆盖物理主机、平台、虚拟 AZ、拓扑模式、端口、runtime 与 cluster scale。

## Allowed Paths
- `harness/harnessctl.py`
- `harness/config.py`
- `harness/inventory.py`
- `harness/scenario.py`
- `harness/mini_yaml.py`
- `harness/schema_validator.py`
- `schemas/**`
- `inventories/**`
- `scenarios/**`
- `tests/test_p02_config.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P02/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/config.py harness/inventory.py harness/scenario.py harness/mini_yaml.py harness/schema_validator.py harness/harnessctl.py`
- `python3 -m unittest discover -s tests -p 'test_p02_config.py'`
- `python3 -m harness.harnessctl validate --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json`
- `python3 -m harness.harnessctl validate --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json`
- `python3 -m harness.harnessctl validate --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json`

## Required Artifacts
- `artifacts/phase-P02/result.json`
- `artifacts/phase-P02/notes.md`
- `artifacts/phase-P02/commands.log`
- `artifacts/phase-P02/commands.jsonl`
- `artifacts/phase-P02/changed_files.txt`
