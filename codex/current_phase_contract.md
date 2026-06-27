# Current Phase Contract: P05

## Name
Mac/Linux 平台抽象

## Goal
集中 Darwin/Linux 差异，保持 planner、cluster_create、report 与平台命令解耦。

## Allowed Paths
- `harness/harnessctl.py`
- `harness/platform_adapter.py`
- `harness/platform_darwin.py`
- `harness/platform_linux.py`
- `harness/executor.py`
- `tests/test_p05_platform_adapter.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P05/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py harness/executor.py harness/harnessctl.py`
- `python3 -m unittest discover -s tests -p 'test_p05_platform_adapter.py'`
- `python3 -m harness.harnessctl doctor --dry-run --json`

## Required Artifacts
- `artifacts/phase-P05/result.json`
- `artifacts/phase-P05/notes.md`
- `artifacts/phase-P05/commands.log`
- `artifacts/phase-P05/commands.jsonl`
- `artifacts/phase-P05/changed_files.txt`
