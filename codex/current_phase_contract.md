# Current Phase Contract: P09

## Name
cluster command executor 与 fake cluster 状态机

## Goal
实现可测试的 cluster management 状态机，显式建模 MEET、known_nodes 收敛、slot assignment、replicate、cluster_state ok。

## Allowed Paths
- `harness/valkey_cli.py`
- `harness/fake_cluster.py`
- `harness/cluster_create.py`
- `harness/cluster_check.py`
- `harness/slot_check.py`
- `harness/events.py`
- `tests/test_p09_cluster_state_machine.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P09/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/valkey_cli.py harness/fake_cluster.py harness/cluster_create.py harness/cluster_check.py harness/slot_check.py`
- `python3 -m unittest discover -s tests -p 'test_p09_cluster_state_machine.py'`

## Required Artifacts
- `artifacts/phase-P09/result.json`
- `artifacts/phase-P09/notes.md`
- `artifacts/phase-P09/commands.log`
- `artifacts/phase-P09/commands.jsonl`
- `artifacts/phase-P09/changed_files.txt`
