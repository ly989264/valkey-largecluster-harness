# Current Phase Contract: P04

## Name
节点、端口、slot 与 replica 规划

## Goal
把 virtual AZ placement 扩展成完整 ClusterPlan，包含 NodeSpec、client/bus ports、slot ranges、primary/replica 关系与 placement warnings。

## Allowed Paths
- `harness/harnessctl.py`
- `harness/config.py`
- `harness/topology.py`
- `harness/planner.py`
- `harness/cluster_plan.py`
- `harness/port_allocator.py`
- `harness/slot_allocator.py`
- `tests/test_p04_cluster_plan.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P04/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/cluster_plan.py harness/port_allocator.py harness/slot_allocator.py harness/planner.py harness/harnessctl.py`
- `python3 -m unittest discover -s tests -p 'test_p04_cluster_plan.py'`
- `python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/cluster-plan.json`

## Required Artifacts
- `artifacts/phase-P04/result.json`
- `artifacts/phase-P04/notes.md`
- `artifacts/phase-P04/commands.log`
- `artifacts/phase-P04/commands.jsonl`
- `artifacts/phase-P04/changed_files.txt`
