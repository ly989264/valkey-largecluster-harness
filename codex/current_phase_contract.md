# Current Phase Contract: P08

## Name
Valkey 配置生成

## Goal
根据 ClusterPlan/NodeSpec 生成真实 Valkey cluster 配置文件；不启动集群。

## Allowed Paths
- `nodehost/valkey_config.py`
- `nodehost/config_writer.py`
- `nodehost/nodehostctl.py`
- `harness/cluster_plan.py`
- `tests/test_p08_valkey_config.py`
- `tests/helpers/**`
- `tests/conftest.py`
- `codex/loop_state.json`
- `codex/current_phase_contract.json`
- `codex/current_phase_contract.md`
- `artifacts/phase-P08/**`

## Pre-Gate Commands
- `python3 -m py_compile nodehost/valkey_config.py nodehost/config_writer.py nodehost/nodehostctl.py`
- `python3 -m unittest discover -s tests -p 'test_p08_valkey_config.py'`

## Required Artifacts
- `artifacts/phase-P08/result.json`
- `artifacts/phase-P08/notes.md`
- `artifacts/phase-P08/commands.log`
- `artifacts/phase-P08/commands.jsonl`
- `artifacts/phase-P08/changed_files.txt`
