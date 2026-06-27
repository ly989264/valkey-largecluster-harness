# Current Phase Contract: P06

## Name
事件、状态与 artifacts 基础设施

## Goal
让所有 harness 动作可审计，并使 report 可完全从磁盘 artifacts 重建。

## Allowed Paths
- `harness/artifacts.py`
- `harness/events.py`
- `harness/status.py`
- `harness/command_log.py`
- `tests/test_p06_artifacts_events.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P06/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/artifacts.py harness/events.py harness/status.py harness/command_log.py`
- `python3 -m unittest discover -s tests -p 'test_p06_artifacts_events.py'`

## Required Artifacts
- `artifacts/phase-P06/result.json`
- `artifacts/phase-P06/notes.md`
- `artifacts/phase-P06/commands.log`
- `artifacts/phase-P06/commands.jsonl`
- `artifacts/phase-P06/changed_files.txt`
