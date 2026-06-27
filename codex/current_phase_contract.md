# Current Phase Contract: P01

## Name
最小 Python 工程与 harnessctl CLI 壳

## Goal
建立可导入的 Python 包、harnessctl 入口、统一 JSON 输出和 CLI smoke tests；不实现配置、拓扑、节点或集群管理。

## Allowed Paths
- `pyproject.toml`
- `Makefile`
- `harness/__init__.py`
- `harness/harnessctl.py`
- `harness/errors.py`
- `harness/jsonio.py`
- `tests/test_p01_cli.py`
- `tests/helpers/**`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P01/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/__init__.py harness/harnessctl.py harness/errors.py harness/jsonio.py`
- `python3 -m unittest discover -s tests -p 'test_p01_cli.py'`
- `python3 -m harness.harnessctl version --json`
- `python3 -m harness.harnessctl doctor --dry-run --json`
- `python3 -m harness.harnessctl validate --help`
- `python3 -m harness.harnessctl plan --help`
- `python3 -m harness.harnessctl run-scenario --help`
- `python3 -m harness.harnessctl report --help`

## Required Artifacts
- `artifacts/phase-P01/result.json`
- `artifacts/phase-P01/notes.md`
- `artifacts/phase-P01/commands.log`
- `artifacts/phase-P01/commands.jsonl`
- `artifacts/phase-P01/changed_files.txt`
