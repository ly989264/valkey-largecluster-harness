# Current Phase Contract: P00

## Name
自动 NEXT、Gate 与防遗忘脚手架

## Goal
建立受脚本控制的 loop-engineering 状态机、phase manifest、阶段卡片、diff/artifact/status/forbidden/project gates；不实现 Valkey 业务 harness。

## Allowed Paths
- `AGENTS.md`
- `CODEX_LOOP.md`
- `codex/**`
- `scripts/codex_next.py`
- `scripts/phase_gate.py`
- `scripts/diff_guard.py`
- `scripts/artifact_guard.py`
- `scripts/status_guard.py`
- `scripts/forbidden_guard.py`
- `scripts/project_quality_gate.py`
- `tests/test_p00_loop_control.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P00/**`

## Pre-Gate Commands
- `python3 -m py_compile scripts/codex_next.py scripts/phase_gate.py scripts/diff_guard.py scripts/artifact_guard.py scripts/status_guard.py scripts/forbidden_guard.py scripts/project_quality_gate.py`
- `python3 tests/test_p00_loop_control.py`
- `python3 scripts/codex_next.py status --json`
- `python3 scripts/codex_next.py next --json`
- `python3 scripts/phase_gate.py list --json`
- `python3 scripts/diff_guard.py allowed-files --phase P00 --json`

## Required Artifacts
- `artifacts/phase-P00/result.json`
- `artifacts/phase-P00/notes.md`
- `artifacts/phase-P00/commands.log`
- `artifacts/phase-P00/commands.jsonl`
- `artifacts/phase-P00/changed_files.txt`
