# Current Phase Contract: P10

## Name
单 Mac 6 节点 smoke runner

## Goal
跑通 smoke-6 fake-run/dry-run 的完整路径：validate、plan、nodehost、cluster create/check、cleanup、artifacts。

## Allowed Paths
- `harness/scenario_runner.py`
- `harness/preflight.py`
- `harness/harnessctl.py`
- `harness/nodehost_client.py`
- `harness/cluster_create.py`
- `harness/cluster_check.py`
- `harness/artifacts.py`
- `harness/events.py`
- `harness/status.py`
- `tests/test_p10_single_mac_smoke.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P10/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/scenario_runner.py harness/preflight.py harness/harnessctl.py`
- `python3 -m unittest discover -s tests -p 'test_p10_single_mac_smoke.py'`
- `python3 -m harness.harnessctl run-scenario --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --run-id p10-smoke --backend fake --json`

## Required Artifacts
- `artifacts/phase-P10/result.json`
- `artifacts/phase-P10/notes.md`
- `artifacts/phase-P10/commands.log`
- `artifacts/phase-P10/commands.jsonl`
- `artifacts/phase-P10/changed_files.txt`
