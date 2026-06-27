# Current Phase Contract: P12

## Name
故障接管 timeline 与稳定性断言

## Goal
记录 failover 时间线并计算稳定性指标；不能只用最终 cluster_state ok 判断成功。

## Allowed Paths
- `harness/failover_timeline.py`
- `harness/failover_observer.py`
- `harness/stability_assertions.py`
- `harness/cluster_check.py`
- `harness/events.py`
- `tests/test_p12_failover_timeline.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P12/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/failover_timeline.py harness/failover_observer.py harness/stability_assertions.py harness/cluster_check.py`
- `python3 -m unittest discover -s tests -p 'test_p12_failover_timeline.py'`

## Required Artifacts
- `artifacts/phase-P12/result.json`
- `artifacts/phase-P12/notes.md`
- `artifacts/phase-P12/commands.log`
- `artifacts/phase-P12/commands.jsonl`
- `artifacts/phase-P12/changed_files.txt`
