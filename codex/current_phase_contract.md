# Current Phase Contract: P14

## Name
多 Mac SSH 编排

## Goal
让 controller 通过 SSH 编排多台 Mac；unit tests 使用 fake SSH，不要求真实多 Mac。

## Allowed Paths
- `harness/ssh_exec.py`
- `harness/remote_nodehost.py`
- `harness/deployer.py`
- `harness/scenario_runner.py`
- `harness/nodehost_client.py`
- `tests/test_p14_multi_mac_ssh.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P14/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/ssh_exec.py harness/remote_nodehost.py harness/deployer.py harness/scenario_runner.py`
- `python3 -m unittest discover -s tests -p 'test_p14_multi_mac_ssh.py'`

## Required Artifacts
- `artifacts/phase-P14/result.json`
- `artifacts/phase-P14/notes.md`
- `artifacts/phase-P14/commands.log`
- `artifacts/phase-P14/commands.jsonl`
- `artifacts/phase-P14/changed_files.txt`
