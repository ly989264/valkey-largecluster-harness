# Current Phase Contract: P03

## Name
虚拟 AZ 拓扑规划

## Goal
实现 deterministic virtual AZ placement，支持 single_az、physical_aligned、uniform_interleaved、custom。

## Allowed Paths
- `harness/harnessctl.py`
- `harness/config.py`
- `harness/topology.py`
- `harness/planner.py`
- `tests/test_p03_virtual_az.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P03/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/topology.py harness/planner.py harness/harnessctl.py`
- `python3 -m unittest discover -s tests -p 'test_p03_virtual_az.py'`
- `python3 -m harness.harnessctl plan --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-single.json`
- `python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-two.json`
- `python3 -m harness.harnessctl plan --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-three.json`

## Required Artifacts
- `artifacts/phase-P03/result.json`
- `artifacts/phase-P03/notes.md`
- `artifacts/phase-P03/commands.log`
- `artifacts/phase-P03/commands.jsonl`
- `artifacts/phase-P03/changed_files.txt`
