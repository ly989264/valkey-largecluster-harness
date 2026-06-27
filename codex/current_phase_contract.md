# Current Phase Contract: P13

## Name
Docker hostnet nodehost

## Goal
实现 Docker host network scale backend contract：一个虚拟 AZ 一个容器，容器内多个 Valkey 进程；禁止 Docker-in-Docker 和一节点一容器。

## Allowed Paths
- `docker/**`
- `harness/docker_nodehost.py`
- `harness/nodehost_client.py`
- `harness/preflight.py`
- `tests/test_p13_docker_hostnet.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P13/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/docker_nodehost.py harness/nodehost_client.py harness/preflight.py`
- `python3 -m unittest discover -s tests -p 'test_p13_docker_hostnet.py'`

## Required Artifacts
- `artifacts/phase-P13/result.json`
- `artifacts/phase-P13/notes.md`
- `artifacts/phase-P13/commands.log`
- `artifacts/phase-P13/commands.jsonl`
- `artifacts/phase-P13/changed_files.txt`
