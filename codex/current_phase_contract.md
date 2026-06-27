# Current Phase Contract: P16

## Name
scale ladder 与最终 report pipeline

## Goal
固化 100/300/500/1000/2000 场景与 report pipeline；2000 是 best-effort empty-node smoke，不是生产能力背书。

## Allowed Paths
- `scenarios/**`
- `harness/report_builder.py`
- `harness/report_models.py`
- `harness/project_quality.py`
- `harness/harnessctl.py`
- `harness/artifacts.py`
- `harness/events.py`
- `harness/status.py`
- `harness/failover_timeline.py`
- `scripts/project_quality_gate.py`
- `tests/test_p16_report_and_scale.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `Makefile`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P16/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/report_builder.py harness/report_models.py harness/project_quality.py harness/harnessctl.py scripts/project_quality_gate.py`
- `python3 -m unittest discover -s tests -p 'test_p16_report_and_scale.py'`
- `python3 scripts/project_quality_gate.py --candidate-phase P16 --json`

## Required Artifacts
- `artifacts/phase-P16/result.json`
- `artifacts/phase-P16/notes.md`
- `artifacts/phase-P16/commands.log`
- `artifacts/phase-P16/commands.jsonl`
- `artifacts/phase-P16/changed_files.txt`
