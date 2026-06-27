# Current Phase Contract: P15

## Name
网络故障 backend 与 Linux 迁移能力

## Goal
建立网络故障接口：virtual AZ 隔离、时延、丢包；Darwin 能力不足必须明确 SKIPPED_RESOURCE，Linux tc/netem 路径必须可验证命令构造。

## Allowed Paths
- `harness/network_faults.py`
- `nodehost/faults_network.py`
- `harness/platform_adapter.py`
- `harness/platform_darwin.py`
- `harness/platform_linux.py`
- `harness/faults.py`
- `tests/test_p15_network_faults.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P15/**`

## Pre-Gate Commands
- `python3 -m py_compile harness/network_faults.py nodehost/faults_network.py harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py`
- `python3 -m unittest discover -s tests -p 'test_p15_network_faults.py'`

## Required Artifacts
- `artifacts/phase-P15/result.json`
- `artifacts/phase-P15/notes.md`
- `artifacts/phase-P15/commands.log`
- `artifacts/phase-P15/commands.jsonl`
- `artifacts/phase-P15/changed_files.txt`
