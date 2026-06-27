# 给 Codex 的阶段 Manifest 源：Valkey 9.x Large-Cluster Harness（v2 fixed）

本文件包含唯一规范化阶段定义。P00 必须把下面 JSON block 精确复制为 `codex/phase_manifest.json`，不得手工改写字段含义。

如果本文件后续人类可读阶段卡片与 JSON block 不一致，以 JSON block 为准。

## Canonical phase manifest JSON

<!-- BEGIN_CANONICAL_PHASE_MANIFEST_JSON -->
```json
{
  "version": 2,
  "project": "Valkey 9.x large-cluster validation harness",
  "canonical_source": "codex_valkey_loop_md_bundle_v2_fixed/01_阶段Manifest源_ValkeyHarness.md",
  "phase_ids": [
    "P00",
    "P01",
    "P02",
    "P03",
    "P04",
    "P05",
    "P06",
    "P07",
    "P08",
    "P09",
    "P10",
    "P11",
    "P12",
    "P13",
    "P14",
    "P15",
    "P16"
  ],
  "global_allowed_control_paths": [
    "codex/loop_state.json",
    "codex/current_phase_contract.json",
    "codex/current_phase_contract.md",
    "artifacts/phase-${PHASE}/**"
  ],
  "artifact_contract": {
    "required_artifacts": [
      "artifacts/phase-${PHASE}/result.json",
      "artifacts/phase-${PHASE}/notes.md",
      "artifacts/phase-${PHASE}/commands.log",
      "artifacts/phase-${PHASE}/commands.jsonl",
      "artifacts/phase-${PHASE}/changed_files.txt"
    ],
    "commands_jsonl_schema": {
      "required_fields": [
        "phase",
        "command",
        "exit_code",
        "started_at",
        "finished_at"
      ],
      "success_exit_code": 0,
      "exact_command_match_required": true
    },
    "result_json_required_fields": [
      "phase",
      "status",
      "attempt",
      "manifest_sha256",
      "phase_card_sha256",
      "summary",
      "expected_outputs",
      "verified_outputs",
      "commands",
      "changed_files",
      "risks"
    ],
    "valid_result_status": [
      "PASS",
      "FAIL",
      "BLOCKED",
      "SKIPPED_RESOURCE"
    ],
    "phase_gate_command_is_not_a_required_command": true
  },
  "phase_gate_command_template": "python3 scripts/phase_gate.py check --phase ${PHASE} --json",
  "post_gate_pass_command_template": "python3 scripts/codex_next.py pass --phase ${PHASE} --json",
  "vcs_checkpoint": {
    "required_after_phase_pass": true,
    "branch": "single_loop_harness",
    "commit_message_template": "${PHASE}: ${PHASE_NAME}",
    "push_required": true,
    "block_if_push_fails": true
  },
  "phases": [
    {
      "id": "P00",
      "order": 0,
      "name": "自动 NEXT、Gate 与防遗忘脚手架",
      "required": true,
      "goal": "建立受脚本控制的 loop-engineering 状态机、phase manifest、阶段卡片、diff/artifact/status/forbidden/project gates；不实现 Valkey 业务 harness。",
      "allowed_paths": [
        "AGENTS.md",
        "CODEX_LOOP.md",
        "codex/**",
        "scripts/codex_next.py",
        "scripts/phase_gate.py",
        "scripts/diff_guard.py",
        "scripts/artifact_guard.py",
        "scripts/status_guard.py",
        "scripts/forbidden_guard.py",
        "scripts/project_quality_gate.py",
        "tests/test_p00_loop_control.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P00/**"
      ],
      "required_outputs": [
        "codex/phase_manifest.json copied exactly from the canonical JSON block in 01_阶段Manifest源_ValkeyHarness.md",
        "codex/phase_cards/P00.md ... codex/phase_cards/P16.md generated from the manifest",
        "codex/loop_state.json initialized with P00 IN_PROGRESS/PENDING semantics and all later phases PENDING",
        "scripts/codex_next.py with next/status/claim/progress/pass/fail/block/explain and --json support",
        "scripts/phase_gate.py with check/explain/list and --json support",
        "scripts/diff_guard.py, artifact_guard.py, status_guard.py, forbidden_guard.py",
        "scripts/project_quality_gate.py strict stub with --candidate-phase support for later P16 completion",
        "AGENTS.md and CODEX_LOOP.md summarizing the execution contract",
        "P00 artifacts: result.json, notes.md, commands.log, commands.jsonl, changed_files.txt"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile scripts/codex_next.py scripts/phase_gate.py scripts/diff_guard.py scripts/artifact_guard.py scripts/status_guard.py scripts/forbidden_guard.py scripts/project_quality_gate.py",
        "python3 tests/test_p00_loop_control.py",
        "python3 scripts/codex_next.py status --json",
        "python3 scripts/codex_next.py next --json",
        "python3 scripts/phase_gate.py list --json",
        "python3 scripts/diff_guard.py allowed-files --phase P00 --json"
      ],
      "acceptance": [
        "P00 allowed_paths includes every file P00 is required to create, including scripts/project_quality_gate.py and tests/test_p00_loop_control.py",
        "No pre_gate_commands entry contains phase_gate.py check; this avoids bootstrap/self-gate recursion",
        "codex_next.py pass --phase P00 internally reruns phase_gate.py check --phase P00 before writing PASS to loop_state.json",
        "diff_guard includes untracked, modified, deleted, renamed and already-committed-in-phase files by comparing against the phase base ref recorded in loop_state.json",
        "phase_gate trusts manifest/result/commands/artifacts, not natural-language claims"
      ],
      "forbidden": [
        "Do not create harness/, nodehost/, docker/, inventories/, scenarios/ business functionality in P00",
        "Do not weaken gate checks to make P00 pass",
        "Do not edit the Markdown spec bundle"
      ],
      "required_artifacts": [
        "artifacts/phase-P00/result.json",
        "artifacts/phase-P00/notes.md",
        "artifacts/phase-P00/commands.log",
        "artifacts/phase-P00/commands.jsonl",
        "artifacts/phase-P00/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P01",
      "order": 1,
      "name": "最小 Python 工程与 harnessctl CLI 壳",
      "required": true,
      "goal": "建立可导入的 Python 包、harnessctl 入口、统一 JSON 输出和 CLI smoke tests；不实现配置、拓扑、节点或集群管理。",
      "allowed_paths": [
        "pyproject.toml",
        "Makefile",
        "harness/__init__.py",
        "harness/harnessctl.py",
        "harness/errors.py",
        "harness/jsonio.py",
        "tests/test_p01_cli.py",
        "tests/helpers/**",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P01/**"
      ],
      "required_outputs": [
        "harness package importable",
        "python3 -m harness.harnessctl version --json returns stable JSON",
        "doctor --dry-run --json returns stable JSON without touching Docker/SSH/Valkey",
        "validate/plan/run-scenario/report subcommands expose help or explicit NOT_IMPLEMENTED",
        "Makefile targets: test, gate, lint-lite or equivalent standard-library friendly checks"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/__init__.py harness/harnessctl.py harness/errors.py harness/jsonio.py",
        "python3 -m unittest discover -s tests -p 'test_p01_cli.py'",
        "python3 -m harness.harnessctl version --json",
        "python3 -m harness.harnessctl doctor --dry-run --json",
        "python3 -m harness.harnessctl validate --help",
        "python3 -m harness.harnessctl plan --help",
        "python3 -m harness.harnessctl run-scenario --help",
        "python3 -m harness.harnessctl report --help"
      ],
      "acceptance": [
        "All listed CLI commands terminate deterministically with exit code 0 unless explicitly testing an error path",
        "JSON output contains status, command, version or reason fields as applicable",
        "No Docker, SSH, Valkey binary, or network access is attempted"
      ],
      "forbidden": [
        "Do not implement config loader or planner in P01",
        "Do not introduce non-declared runtime dependencies"
      ],
      "required_artifacts": [
        "artifacts/phase-P01/result.json",
        "artifacts/phase-P01/notes.md",
        "artifacts/phase-P01/commands.log",
        "artifacts/phase-P01/commands.jsonl",
        "artifacts/phase-P01/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P02",
      "order": 2,
      "name": "配置契约：inventory 与 scenario",
      "required": true,
      "goal": "让 inventory 与 scenario 成为唯一输入源，覆盖物理主机、平台、虚拟 AZ、拓扑模式、端口、runtime 与 cluster scale。",
      "allowed_paths": [
        "harness/harnessctl.py",
        "harness/config.py",
        "harness/inventory.py",
        "harness/scenario.py",
        "harness/mini_yaml.py",
        "harness/schema_validator.py",
        "schemas/**",
        "inventories/**",
        "scenarios/**",
        "tests/test_p02_config.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P02/**"
      ],
      "required_outputs": [
        "Inventory and Scenario dataclasses or typed models with explicit defaults",
        "Strict loader for .json/.yaml/.yml using standard library only; optional PyYAML may be used only as enhancement, not requirement",
        "schemas/inventory.schema.json and schemas/scenario.schema.json used by code, not decorative",
        "Sample inventories: single-mac-dev, two-mac-physical-aligned, three-mac-uniform-interleaved",
        "Sample scenarios: smoke-6 and scale-100",
        "harnessctl validate wired to config validation"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/config.py harness/inventory.py harness/scenario.py harness/mini_yaml.py harness/schema_validator.py harness/harnessctl.py",
        "python3 -m unittest discover -s tests -p 'test_p02_config.py'",
        "python3 -m harness.harnessctl validate --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json",
        "python3 -m harness.harnessctl validate --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json",
        "python3 -m harness.harnessctl validate --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json"
      ],
      "acceptance": [
        "Valid samples pass",
        "Missing physical_hosts, illegal topology_mode, overlapping client/bus ports, total_nodes <= 0, and invalid replica settings fail with clear JSON errors",
        "Config layer owns defaults; later planner phases must not invent hidden defaults"
      ],
      "forbidden": [
        "Do not plan topology in P02",
        "Do not silently coerce invalid config into valid config"
      ],
      "required_artifacts": [
        "artifacts/phase-P02/result.json",
        "artifacts/phase-P02/notes.md",
        "artifacts/phase-P02/commands.log",
        "artifacts/phase-P02/commands.jsonl",
        "artifacts/phase-P02/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P03",
      "order": 3,
      "name": "虚拟 AZ 拓扑规划",
      "required": true,
      "goal": "实现 deterministic virtual AZ placement，支持 single_az、physical_aligned、uniform_interleaved、custom。",
      "allowed_paths": [
        "harness/harnessctl.py",
        "harness/config.py",
        "harness/topology.py",
        "harness/planner.py",
        "tests/test_p03_virtual_az.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P03/**"
      ],
      "required_outputs": [
        "VirtualAZPlacement model",
        "Topology planner with deterministic ordering: physical_host_id, virtual_az_id, node_index",
        "virtual_az_host_matrix in plan output",
        "co-location and durability warnings when isolation is weak",
        "harnessctl plan produces JSON topology draft"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/topology.py harness/planner.py harness/harnessctl.py",
        "python3 -m unittest discover -s tests -p 'test_p03_virtual_az.py'",
        "python3 -m harness.harnessctl plan --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-single.json",
        "python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-two.json",
        "python3 -m harness.harnessctl plan --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-three.json"
      ],
      "acceptance": [
        "single_az creates one virtual AZ and emits explicit warning",
        "physical_aligned supports 2 physical hosts / 3 virtual AZs without pretending physical isolation is perfect",
        "uniform_interleaved emits every physical host x virtual AZ matrix entry",
        "custom follows explicit mapping/weights exactly",
        "Repeated plan command on same inputs gives byte-stable JSON after stable key ordering"
      ],
      "forbidden": [
        "Do not allocate ports or slots in P03",
        "Do not use randomness or wall-clock time in planning"
      ],
      "required_artifacts": [
        "artifacts/phase-P03/result.json",
        "artifacts/phase-P03/notes.md",
        "artifacts/phase-P03/commands.log",
        "artifacts/phase-P03/commands.jsonl",
        "artifacts/phase-P03/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P04",
      "order": 4,
      "name": "节点、端口、slot 与 replica 规划",
      "required": true,
      "goal": "把 virtual AZ placement 扩展成完整 ClusterPlan，包含 NodeSpec、client/bus ports、slot ranges、primary/replica 关系与 placement warnings。",
      "allowed_paths": [
        "harness/harnessctl.py",
        "harness/config.py",
        "harness/topology.py",
        "harness/planner.py",
        "harness/cluster_plan.py",
        "harness/port_allocator.py",
        "harness/slot_allocator.py",
        "tests/test_p04_cluster_plan.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P04/**"
      ],
      "required_outputs": [
        "ClusterPlan, NodeSpec, SlotRange, ReplicaPlacement or equivalent typed models",
        "Unique client ports and unique bus ports with no overlap",
        "Complete 0..16383 slot coverage with single primary owner per slot",
        "Replica anti-affinity against primary virtual AZ when possible; explicit warning when impossible",
        "harnessctl plan emits full ClusterPlan JSON"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/cluster_plan.py harness/port_allocator.py harness/slot_allocator.py harness/planner.py harness/harnessctl.py",
        "python3 -m unittest discover -s tests -p 'test_p04_cluster_plan.py'",
        "python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/cluster-plan.json"
      ],
      "acceptance": [
        "smoke-6 yields exactly 3 primaries and 3 replicas",
        "Slots cover 0..16383 without gap or overlap",
        "Port allocator fails on insufficient or overlapping ranges",
        "total_nodes not divisible by role/topology requirements fails rather than truncating"
      ],
      "forbidden": [
        "Do not let cluster_create or runtime recompute slot/replica layout later",
        "Do not hide anti-affinity violations"
      ],
      "required_artifacts": [
        "artifacts/phase-P04/result.json",
        "artifacts/phase-P04/notes.md",
        "artifacts/phase-P04/commands.log",
        "artifacts/phase-P04/commands.jsonl",
        "artifacts/phase-P04/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P05",
      "order": 5,
      "name": "Mac/Linux 平台抽象",
      "required": true,
      "goal": "集中 Darwin/Linux 差异，保持 planner、cluster_create、report 与平台命令解耦。",
      "allowed_paths": [
        "harness/harnessctl.py",
        "harness/platform_adapter.py",
        "harness/platform_darwin.py",
        "harness/platform_linux.py",
        "harness/executor.py",
        "tests/test_p05_platform_adapter.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P05/**"
      ],
      "required_outputs": [
        "PlatformAdapter interface",
        "Darwin and Linux adapters",
        "FakeExecutor and SubprocessExecutor",
        "Methods: detect_platform, check_port_available, process_exists, read_process_rss, count_process_fds, list_sockets, supports_host_network, supports_network_fault_injection, network_fault_backend_hint",
        "doctor --dry-run can report capabilities through adapter without changing system state"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py harness/executor.py harness/harnessctl.py",
        "python3 -m unittest discover -s tests -p 'test_p05_platform_adapter.py'",
        "python3 -m harness.harnessctl doctor --dry-run --json"
      ],
      "acceptance": [
        "Core planner imports no platform_darwin/platform_linux module",
        "Platform adapters are mockable and unit tests do not require real lsof/ps/docker/tc",
        "Linux migration path is explicit, even when current machine is Darwin"
      ],
      "forbidden": [
        "Do not scatter os.system/subprocess platform commands through core modules",
        "Do not claim unsupported network fault support on Darwin"
      ],
      "required_artifacts": [
        "artifacts/phase-P05/result.json",
        "artifacts/phase-P05/notes.md",
        "artifacts/phase-P05/commands.log",
        "artifacts/phase-P05/commands.jsonl",
        "artifacts/phase-P05/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P06",
      "order": 6,
      "name": "事件、状态与 artifacts 基础设施",
      "required": true,
      "goal": "让所有 harness 动作可审计，并使 report 可完全从磁盘 artifacts 重建。",
      "allowed_paths": [
        "harness/artifacts.py",
        "harness/events.py",
        "harness/status.py",
        "harness/command_log.py",
        "tests/test_p06_artifacts_events.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P06/**"
      ],
      "required_outputs": [
        "ArtifactLayout based on run_id and root directory",
        "EventRecorder writing JSONL, one valid JSON object per line",
        "RunStatusWriter and CommandLogWriter",
        "Readers tolerate corrupted JSONL lines by marking them invalid instead of crashing report",
        "Event taxonomy includes run, command, node, cluster, fault, failover, metric, assertion events"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/artifacts.py harness/events.py harness/status.py harness/command_log.py",
        "python3 -m unittest discover -s tests -p 'test_p06_artifacts_events.py'"
      ],
      "acceptance": [
        "events.jsonl supports append and replay",
        "artifacts paths are isolated per run_id",
        "Corrupted event line is represented as invalid evidence, not swallowed silently"
      ],
      "forbidden": [
        "Do not make report depend on live in-memory objects",
        "Do not let one run overwrite another run's artifacts"
      ],
      "required_artifacts": [
        "artifacts/phase-P06/result.json",
        "artifacts/phase-P06/notes.md",
        "artifacts/phase-P06/commands.log",
        "artifacts/phase-P06/commands.jsonl",
        "artifacts/phase-P06/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P07",
      "order": 7,
      "name": "本地进程 nodehost 与 fake runtime",
      "required": true,
      "goal": "支持单 Mac 小集群开发路径；真实 Valkey 缺失时 unit/fake path 仍可验证 nodehost contract。",
      "allowed_paths": [
        "nodehost/**",
        "harness/nodehost_client.py",
        "harness/artifacts.py",
        "harness/events.py",
        "tests/test_p07_nodehost_local.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P07/**"
      ],
      "required_outputs": [
        "nodehost/nodehostctl.py CLI with status/prepare/start/stop/cleanup/metrics",
        "nodehost/local_process.py local process manager",
        "nodehost/fake_valkey.py fake runtime",
        "nodehost/process_table.py run-scoped process table",
        "harness/nodehost_client.py client contract",
        "Idempotent start/stop/cleanup behavior"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile nodehost/nodehostctl.py nodehost/local_process.py nodehost/fake_valkey.py nodehost/process_table.py harness/nodehost_client.py",
        "python3 -m unittest discover -s tests -p 'test_p07_nodehost_local.py'",
        "python3 -m nodehost.nodehostctl status --json"
      ],
      "acceptance": [
        "No Valkey binary is needed for unit tests",
        "cleanup only removes state for the specified run_id",
        "Fake runtime can represent multiple node states and metrics"
      ],
      "forbidden": [
        "Do not require sudo or real Valkey in P07",
        "Do not use global process state without run_id scoping"
      ],
      "required_artifacts": [
        "artifacts/phase-P07/result.json",
        "artifacts/phase-P07/notes.md",
        "artifacts/phase-P07/commands.log",
        "artifacts/phase-P07/commands.jsonl",
        "artifacts/phase-P07/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P08",
      "order": 8,
      "name": "Valkey 配置生成",
      "required": true,
      "goal": "根据 ClusterPlan/NodeSpec 生成真实 Valkey cluster 配置文件；不启动集群。",
      "allowed_paths": [
        "nodehost/valkey_config.py",
        "nodehost/config_writer.py",
        "nodehost/nodehostctl.py",
        "harness/cluster_plan.py",
        "tests/test_p08_valkey_config.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P08/**"
      ],
      "required_outputs": [
        "ValkeyConfigRenderer",
        "ConfigWriter creating isolated node directories",
        "Rendered fields: port, cluster-enabled yes, cluster-config-file, cluster-node-timeout, cluster-announce-ip, cluster-announce-port, cluster-announce-bus-port, cluster-port, appendonly no, save \"\", protected-mode no, bind, loglevel, logfile, dir, pidfile",
        "Announce IP/port derived from NodeSpec only",
        "Tests proving no port remap or hard-coded IP assumption"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile nodehost/valkey_config.py nodehost/config_writer.py nodehost/nodehostctl.py",
        "python3 -m unittest discover -s tests -p 'test_p08_valkey_config.py'"
      ],
      "acceptance": [
        "Every config value is traceable to ClusterPlan/NodeSpec or explicit scenario config",
        "Each node directory is independent",
        "Renderer performs rendering only, not planning"
      ],
      "forbidden": [
        "Do not calculate ports in config renderer",
        "Do not hard-code localhost when NodeSpec has announce_ip"
      ],
      "required_artifacts": [
        "artifacts/phase-P08/result.json",
        "artifacts/phase-P08/notes.md",
        "artifacts/phase-P08/commands.log",
        "artifacts/phase-P08/commands.jsonl",
        "artifacts/phase-P08/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P09",
      "order": 9,
      "name": "cluster command executor 与 fake cluster 状态机",
      "required": true,
      "goal": "实现可测试的 cluster management 状态机，显式建模 MEET、known_nodes 收敛、slot assignment、replicate、cluster_state ok。",
      "allowed_paths": [
        "harness/valkey_cli.py",
        "harness/fake_cluster.py",
        "harness/cluster_create.py",
        "harness/cluster_check.py",
        "harness/slot_check.py",
        "harness/events.py",
        "tests/test_p09_cluster_state_machine.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P09/**"
      ],
      "required_outputs": [
        "ValkeyCli interface and fake implementation",
        "FakeCluster state machine",
        "ClusterCreator executing ClusterPlan without replanning",
        "ClusterChecker and SlotChecker distinguishing known_nodes_missing, slots_missing, replica_missing, cluster_fail",
        "Events for meet, known_nodes sampling, slots assigned, replica configured, cluster ok/fail"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/valkey_cli.py harness/fake_cluster.py harness/cluster_create.py harness/cluster_check.py harness/slot_check.py",
        "python3 -m unittest discover -s tests -p 'test_p09_cluster_state_machine.py'"
      ],
      "acceptance": [
        "Create flow follows plan order deterministically",
        "Creator does not call planner or recalculate slots/replicas",
        "Checker surfaces incomplete convergence as structured failure"
      ],
      "forbidden": [
        "Do not shell out to valkey-cli in unit tests",
        "Do not use valkey-cli --cluster create as the only model"
      ],
      "required_artifacts": [
        "artifacts/phase-P09/result.json",
        "artifacts/phase-P09/notes.md",
        "artifacts/phase-P09/commands.log",
        "artifacts/phase-P09/commands.jsonl",
        "artifacts/phase-P09/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P10",
      "order": 10,
      "name": "单 Mac 6 节点 smoke runner",
      "required": true,
      "goal": "跑通 smoke-6 fake-run/dry-run 的完整路径：validate、plan、nodehost、cluster create/check、cleanup、artifacts。",
      "allowed_paths": [
        "harness/scenario_runner.py",
        "harness/preflight.py",
        "harness/harnessctl.py",
        "harness/nodehost_client.py",
        "harness/cluster_create.py",
        "harness/cluster_check.py",
        "harness/artifacts.py",
        "harness/events.py",
        "harness/status.py",
        "tests/test_p10_single_mac_smoke.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P10/**"
      ],
      "required_outputs": [
        "run-scenario CLI wired to ScenarioRunner",
        "smoke-6 fake backend path",
        "run artifacts directory containing events.jsonl, run_status.json, cluster_plan.json, command log",
        "cleanup in finally path",
        "Optional real Valkey path reports SKIPPED_RESOURCE when binary is absent; fake path must PASS"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/scenario_runner.py harness/preflight.py harness/harnessctl.py",
        "python3 -m unittest discover -s tests -p 'test_p10_single_mac_smoke.py'",
        "python3 -m harness.harnessctl run-scenario --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --run-id p10-smoke --backend fake --json"
      ],
      "acceptance": [
        "Fake smoke run returns PASS and writes auditable artifacts",
        "Cleanup executes on failure and success",
        "Failures are written as events/status, not swallowed"
      ],
      "forbidden": [
        "Do not require real Valkey for P10 pass",
        "Do not mark optional real integration as PASS when skipped"
      ],
      "required_artifacts": [
        "artifacts/phase-P10/result.json",
        "artifacts/phase-P10/notes.md",
        "artifacts/phase-P10/commands.log",
        "artifacts/phase-P10/commands.jsonl",
        "artifacts/phase-P10/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P11",
      "order": 11,
      "name": "进程故障与虚拟 AZ 故障",
      "required": true,
      "goal": "支持 node 级与 virtual AZ 级进程/fake fault：kill、pause、resume、restart；不做网络故障。",
      "allowed_paths": [
        "harness/faults.py",
        "nodehost/faults_process.py",
        "nodehost/process_table.py",
        "harness/scenario_runner.py",
        "harness/events.py",
        "tests/test_p11_process_faults.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P11/**"
      ],
      "required_outputs": [
        "FaultPlan model",
        "FaultExecutor and ProcessFaultBackend",
        "Virtual AZ target selector reading ClusterPlan",
        "Fault events with before/after timestamps",
        "Idempotent resume/restart semantics"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/faults.py nodehost/faults_process.py harness/scenario_runner.py",
        "python3 -m unittest discover -s tests -p 'test_p11_process_faults.py'"
      ],
      "acceptance": [
        "Fault selection is based on ClusterPlan node virtual_az_id",
        "Repeating resume/restart does not corrupt state",
        "Fault code does not recompute topology"
      ],
      "forbidden": [
        "Do not implement network latency/loss in P11",
        "Do not select targets by ad hoc hostnames when ClusterPlan has explicit IDs"
      ],
      "required_artifacts": [
        "artifacts/phase-P11/result.json",
        "artifacts/phase-P11/notes.md",
        "artifacts/phase-P11/commands.log",
        "artifacts/phase-P11/commands.jsonl",
        "artifacts/phase-P11/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P12",
      "order": 12,
      "name": "故障接管 timeline 与稳定性断言",
      "required": true,
      "goal": "记录 failover 时间线并计算稳定性指标；不能只用最终 cluster_state ok 判断成功。",
      "allowed_paths": [
        "harness/failover_timeline.py",
        "harness/failover_observer.py",
        "harness/stability_assertions.py",
        "harness/cluster_check.py",
        "harness/events.py",
        "tests/test_p12_failover_timeline.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P12/**"
      ],
      "required_outputs": [
        "FailoverTimeline with fault_injected_at, first_pfail_observed_at, first_fail_observed_at, replica_promoted_at, slots_recovered_at, cluster_ok_at, client_success_restored_at",
        "Metric calculation: pfail_detection_ms, fail_confirmation_ms, promotion_ms, slot_recovery_ms, cluster_recovery_ms, client_recovery_ms, unavailable_slots_count_max, stale_owner_duration_ms",
        "FailoverObserver reconstructing timeline from events",
        "StabilityAssertions returning PASS/FAIL/INCONCLUSIVE with reasons",
        "Tests for missing PFAIL, missing promotion, client not recovered, stale owner"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/failover_timeline.py harness/failover_observer.py harness/stability_assertions.py harness/cluster_check.py",
        "python3 -m unittest discover -s tests -p 'test_p12_failover_timeline.py'"
      ],
      "acceptance": [
        "Complete timeline computes all metrics",
        "Missing critical evidence yields INCONCLUSIVE, not PASS",
        "cluster_state ok alone cannot satisfy failover success"
      ],
      "forbidden": [
        "Do not synthesize missing timestamps",
        "Do not turn INCONCLUSIVE into PASS for report cosmetics"
      ],
      "required_artifacts": [
        "artifacts/phase-P12/result.json",
        "artifacts/phase-P12/notes.md",
        "artifacts/phase-P12/commands.log",
        "artifacts/phase-P12/commands.jsonl",
        "artifacts/phase-P12/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P13",
      "order": 13,
      "name": "Docker hostnet nodehost",
      "required": true,
      "goal": "实现 Docker host network scale backend contract：一个虚拟 AZ 一个容器，容器内多个 Valkey 进程；禁止 Docker-in-Docker 和一节点一容器。",
      "allowed_paths": [
        "docker/**",
        "harness/docker_nodehost.py",
        "harness/nodehost_client.py",
        "harness/preflight.py",
        "tests/test_p13_docker_hostnet.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P13/**"
      ],
      "required_outputs": [
        "docker/nodehost.Dockerfile",
        "docker/nodehost-entrypoint.sh",
        "DockerNodehostClient",
        "Docker command builder grouping by virtual_az_id",
        "Capability handling when host networking or docker CLI is unavailable",
        "Contract tests proving no one-node-one-container loop"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/docker_nodehost.py harness/nodehost_client.py harness/preflight.py",
        "python3 -m unittest discover -s tests -p 'test_p13_docker_hostnet.py'"
      ],
      "acceptance": [
        "docker run commands are per virtual AZ, not per node",
        "No docker:dind, privileged dockerd, or DOCKER_HOST=tcp:// dependency appears",
        "Unavailable Docker capability returns structured SKIPPED_RESOURCE for integration, while unit contract still passes"
      ],
      "forbidden": [
        "Do not implement Docker-in-Docker",
        "Do not make planner aware of Docker internals",
        "Do not create one container per Valkey node"
      ],
      "required_artifacts": [
        "artifacts/phase-P13/result.json",
        "artifacts/phase-P13/notes.md",
        "artifacts/phase-P13/commands.log",
        "artifacts/phase-P13/commands.jsonl",
        "artifacts/phase-P13/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P14",
      "order": 14,
      "name": "多 Mac SSH 编排",
      "required": true,
      "goal": "让 controller 通过 SSH 编排多台 Mac；unit tests 使用 fake SSH，不要求真实多 Mac。",
      "allowed_paths": [
        "harness/ssh_exec.py",
        "harness/remote_nodehost.py",
        "harness/deployer.py",
        "harness/scenario_runner.py",
        "harness/nodehost_client.py",
        "tests/test_p14_multi_mac_ssh.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P14/**"
      ],
      "required_outputs": [
        "SSHExecutor and FakeSSHExecutor",
        "RemoteNodehostClient",
        "Deployer supporting preflight, sync/package, start virtual AZ runtime, run nodehostctl, collect artifacts, cleanup",
        "Multi-host dispatch tests based on ClusterPlan"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/ssh_exec.py harness/remote_nodehost.py harness/deployer.py harness/scenario_runner.py",
        "python3 -m unittest discover -s tests -p 'test_p14_multi_mac_ssh.py'"
      ],
      "acceptance": [
        "Fake SSH verifies exact command dispatch and host targeting",
        "Real SSH absence does not fail unit tests",
        "Remote orchestration reads ClusterPlan and does not re-plan topology"
      ],
      "forbidden": [
        "Do not couple SSH implementation to Docker implementation",
        "Do not require password prompts or interactive SSH in tests"
      ],
      "required_artifacts": [
        "artifacts/phase-P14/result.json",
        "artifacts/phase-P14/notes.md",
        "artifacts/phase-P14/commands.log",
        "artifacts/phase-P14/commands.jsonl",
        "artifacts/phase-P14/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P15",
      "order": 15,
      "name": "网络故障 backend 与 Linux 迁移能力",
      "required": true,
      "goal": "建立网络故障接口：virtual AZ 隔离、时延、丢包；Darwin 能力不足必须明确 SKIPPED_RESOURCE，Linux tc/netem 路径必须可验证命令构造。",
      "allowed_paths": [
        "harness/network_faults.py",
        "nodehost/faults_network.py",
        "harness/platform_adapter.py",
        "harness/platform_darwin.py",
        "harness/platform_linux.py",
        "harness/faults.py",
        "tests/test_p15_network_faults.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P15/**"
      ],
      "required_outputs": [
        "NetworkFaultBackend interface",
        "UnsupportedNetworkFaultBackend",
        "LinuxNetemBackend command construction boundaries for tc/netem and firewall selectors",
        "Darwin capability detection returning capability-limited result",
        "Targets include cluster bus ports, not only client ports",
        "Tests for isolate/heal/delay/loss/clear command plans"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/network_faults.py nodehost/faults_network.py harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py",
        "python3 -m unittest discover -s tests -p 'test_p15_network_faults.py'"
      ],
      "acceptance": [
        "Unsupported environment returns SKIPPED_RESOURCE with reason/evidence",
        "Linux migration path is explicit and unit-tested by command construction",
        "Network fault targeting covers cluster bus traffic"
      ],
      "forbidden": [
        "Do not claim precise Mac network fault injection unless capability check proves it",
        "Do not execute tc/pf/iptables in unit tests"
      ],
      "required_artifacts": [
        "artifacts/phase-P15/result.json",
        "artifacts/phase-P15/notes.md",
        "artifacts/phase-P15/commands.log",
        "artifacts/phase-P15/commands.jsonl",
        "artifacts/phase-P15/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    },
    {
      "id": "P16",
      "order": 16,
      "name": "scale ladder 与最终 report pipeline",
      "required": true,
      "goal": "固化 100/300/500/1000/2000 场景与 report pipeline；2000 是 best-effort empty-node smoke，不是生产能力背书。",
      "allowed_paths": [
        "scenarios/**",
        "harness/report_builder.py",
        "harness/report_models.py",
        "harness/project_quality.py",
        "harness/harnessctl.py",
        "harness/artifacts.py",
        "harness/events.py",
        "harness/status.py",
        "harness/failover_timeline.py",
        "scripts/project_quality_gate.py",
        "tests/test_p16_report_and_scale.py",
        "tests/helpers/**",
        "tests/conftest.py",
        "Makefile",
        "codex/loop_state.json",
        "codex/current_phase_contract.json",
        "codex/current_phase_contract.md",
        "artifacts/phase-P16/**"
      ],
      "required_outputs": [
        "scenarios/scale-300.yaml, scale-500.yaml, scale-1000.yaml, scale-2000-empty.yaml",
        "Report models and builder reconstructing report from artifacts",
        "Report sections: summary, environment, virtual AZ topology, ClusterPlan, test matrix, cluster create, fault/failover timeline, migration/CLUSTERSCAN if implemented, resource metrics, stability gates, verified/unverified, failures/skips/inconclusive, reproduce commands, raw artifacts index",
        "project_quality_gate.py finalized and strict",
        "Fixture report artifacts for unit tests"
      ],
      "pre_gate_commands": [
        "python3 -m py_compile harness/report_builder.py harness/report_models.py harness/project_quality.py harness/harnessctl.py scripts/project_quality_gate.py",
        "python3 -m unittest discover -s tests -p 'test_p16_report_and_scale.py'",
        "python3 scripts/project_quality_gate.py --candidate-phase P16 --json"
      ],
      "acceptance": [
        "Scale ladder is configuration-driven, not branchy hard-coded code paths",
        "Report explicitly represents MISSING, INCONCLUSIVE, NOT_VALIDATED, SKIPPED_RESOURCE and FAIL",
        "scale-2000-empty clearly does not validate throughput, production latency, production RTO, or physical 3-AZ durability",
        "project_quality_gate validates manifest consistency, all prior phases, forbidden patterns, runnable tests, and report honesty"
      ],
      "forbidden": [
        "Do not beautify failures into pass",
        "Do not claim production validation from fake/empty-node runs"
      ],
      "required_artifacts": [
        "artifacts/phase-P16/result.json",
        "artifacts/phase-P16/notes.md",
        "artifacts/phase-P16/commands.log",
        "artifacts/phase-P16/commands.jsonl",
        "artifacts/phase-P16/changed_files.txt"
      ],
      "allow_phase_level_skipped_resource": false,
      "max_repair_attempts": 3
    }
  ]
}
```
<!-- END_CANONICAL_PHASE_MANIFEST_JSON -->

## 人类可读阶段卡片（由同一 manifest 生成）

这些卡片帮助 Codex 理解阶段意图；字段级约束仍以 canonical JSON 为准。


## P00：自动 NEXT、Gate 与防遗忘脚手架

### 目标

建立受脚本控制的 loop-engineering 状态机、phase manifest、阶段卡片、diff/artifact/status/forbidden/project gates；不实现 Valkey 业务 harness。

### 允许修改范围

```text
AGENTS.md
CODEX_LOOP.md
codex/**
scripts/codex_next.py
scripts/phase_gate.py
scripts/diff_guard.py
scripts/artifact_guard.py
scripts/status_guard.py
scripts/forbidden_guard.py
scripts/project_quality_gate.py
tests/test_p00_loop_control.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P00/**
```

### 必须产出

```text
- codex/phase_manifest.json copied exactly from the canonical JSON block in 01_阶段Manifest源_ValkeyHarness.md
- codex/phase_cards/P00.md ... codex/phase_cards/P16.md generated from the manifest
- codex/loop_state.json initialized with P00 IN_PROGRESS/PENDING semantics and all later phases PENDING
- scripts/codex_next.py with next/status/claim/progress/pass/fail/block/explain and --json support
- scripts/phase_gate.py with check/explain/list and --json support
- scripts/diff_guard.py, artifact_guard.py, status_guard.py, forbidden_guard.py
- scripts/project_quality_gate.py strict stub with --candidate-phase support for later P16 completion
- AGENTS.md and CODEX_LOOP.md summarizing the execution contract
- P00 artifacts: result.json, notes.md, commands.log, commands.jsonl, changed_files.txt
```

### Pre-gate commands

```bash
python3 -m py_compile scripts/codex_next.py scripts/phase_gate.py scripts/diff_guard.py scripts/artifact_guard.py scripts/status_guard.py scripts/forbidden_guard.py scripts/project_quality_gate.py
python3 tests/test_p00_loop_control.py
python3 scripts/codex_next.py status --json
python3 scripts/codex_next.py next --json
python3 scripts/phase_gate.py list --json
python3 scripts/diff_guard.py allowed-files --phase P00 --json
```

### 通过条件

```text
- P00 allowed_paths includes every file P00 is required to create, including scripts/project_quality_gate.py and tests/test_p00_loop_control.py
- No pre_gate_commands entry contains phase_gate.py check; this avoids bootstrap/self-gate recursion
- codex_next.py pass --phase P00 internally reruns phase_gate.py check --phase P00 before writing PASS to loop_state.json
- diff_guard includes untracked, modified, deleted, renamed and already-committed-in-phase files by comparing against the phase base ref recorded in loop_state.json
- phase_gate trusts manifest/result/commands/artifacts, not natural-language claims
```

### 禁止事项

```text
- Do not create harness/, nodehost/, docker/, inventories/, scenarios/ business functionality in P00
- Do not weaken gate checks to make P00 pass
- Do not edit the Markdown spec bundle
```

## P01：最小 Python 工程与 harnessctl CLI 壳

### 目标

建立可导入的 Python 包、harnessctl 入口、统一 JSON 输出和 CLI smoke tests；不实现配置、拓扑、节点或集群管理。

### 允许修改范围

```text
pyproject.toml
Makefile
harness/__init__.py
harness/harnessctl.py
harness/errors.py
harness/jsonio.py
tests/test_p01_cli.py
tests/helpers/**
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P01/**
```

### 必须产出

```text
- harness package importable
- python3 -m harness.harnessctl version --json returns stable JSON
- doctor --dry-run --json returns stable JSON without touching Docker/SSH/Valkey
- validate/plan/run-scenario/report subcommands expose help or explicit NOT_IMPLEMENTED
- Makefile targets: test, gate, lint-lite or equivalent standard-library friendly checks
```

### Pre-gate commands

```bash
python3 -m py_compile harness/__init__.py harness/harnessctl.py harness/errors.py harness/jsonio.py
python3 -m unittest discover -s tests -p 'test_p01_cli.py'
python3 -m harness.harnessctl version --json
python3 -m harness.harnessctl doctor --dry-run --json
python3 -m harness.harnessctl validate --help
python3 -m harness.harnessctl plan --help
python3 -m harness.harnessctl run-scenario --help
python3 -m harness.harnessctl report --help
```

### 通过条件

```text
- All listed CLI commands terminate deterministically with exit code 0 unless explicitly testing an error path
- JSON output contains status, command, version or reason fields as applicable
- No Docker, SSH, Valkey binary, or network access is attempted
```

### 禁止事项

```text
- Do not implement config loader or planner in P01
- Do not introduce non-declared runtime dependencies
```

## P02：配置契约：inventory 与 scenario

### 目标

让 inventory 与 scenario 成为唯一输入源，覆盖物理主机、平台、虚拟 AZ、拓扑模式、端口、runtime 与 cluster scale。

### 允许修改范围

```text
harness/harnessctl.py
harness/config.py
harness/inventory.py
harness/scenario.py
harness/mini_yaml.py
harness/schema_validator.py
schemas/**
inventories/**
scenarios/**
tests/test_p02_config.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P02/**
```

### 必须产出

```text
- Inventory and Scenario dataclasses or typed models with explicit defaults
- Strict loader for .json/.yaml/.yml using standard library only; optional PyYAML may be used only as enhancement, not requirement
- schemas/inventory.schema.json and schemas/scenario.schema.json used by code, not decorative
- Sample inventories: single-mac-dev, two-mac-physical-aligned, three-mac-uniform-interleaved
- Sample scenarios: smoke-6 and scale-100
- harnessctl validate wired to config validation
```

### Pre-gate commands

```bash
python3 -m py_compile harness/config.py harness/inventory.py harness/scenario.py harness/mini_yaml.py harness/schema_validator.py harness/harnessctl.py
python3 -m unittest discover -s tests -p 'test_p02_config.py'
python3 -m harness.harnessctl validate --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json
python3 -m harness.harnessctl validate --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json
python3 -m harness.harnessctl validate --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json
```

### 通过条件

```text
- Valid samples pass
- Missing physical_hosts, illegal topology_mode, overlapping client/bus ports, total_nodes <= 0, and invalid replica settings fail with clear JSON errors
- Config layer owns defaults; later planner phases must not invent hidden defaults
```

### 禁止事项

```text
- Do not plan topology in P02
- Do not silently coerce invalid config into valid config
```

## P03：虚拟 AZ 拓扑规划

### 目标

实现 deterministic virtual AZ placement，支持 single_az、physical_aligned、uniform_interleaved、custom。

### 允许修改范围

```text
harness/harnessctl.py
harness/config.py
harness/topology.py
harness/planner.py
tests/test_p03_virtual_az.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P03/**
```

### 必须产出

```text
- VirtualAZPlacement model
- Topology planner with deterministic ordering: physical_host_id, virtual_az_id, node_index
- virtual_az_host_matrix in plan output
- co-location and durability warnings when isolation is weak
- harnessctl plan produces JSON topology draft
```

### Pre-gate commands

```bash
python3 -m py_compile harness/topology.py harness/planner.py harness/harnessctl.py
python3 -m unittest discover -s tests -p 'test_p03_virtual_az.py'
python3 -m harness.harnessctl plan --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-single.json
python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-two.json
python3 -m harness.harnessctl plan --inventory inventories/three-mac-uniform-interleaved.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/plan-three.json
```

### 通过条件

```text
- single_az creates one virtual AZ and emits explicit warning
- physical_aligned supports 2 physical hosts / 3 virtual AZs without pretending physical isolation is perfect
- uniform_interleaved emits every physical host x virtual AZ matrix entry
- custom follows explicit mapping/weights exactly
- Repeated plan command on same inputs gives byte-stable JSON after stable key ordering
```

### 禁止事项

```text
- Do not allocate ports or slots in P03
- Do not use randomness or wall-clock time in planning
```

## P04：节点、端口、slot 与 replica 规划

### 目标

把 virtual AZ placement 扩展成完整 ClusterPlan，包含 NodeSpec、client/bus ports、slot ranges、primary/replica 关系与 placement warnings。

### 允许修改范围

```text
harness/harnessctl.py
harness/config.py
harness/topology.py
harness/planner.py
harness/cluster_plan.py
harness/port_allocator.py
harness/slot_allocator.py
tests/test_p04_cluster_plan.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P04/**
```

### 必须产出

```text
- ClusterPlan, NodeSpec, SlotRange, ReplicaPlacement or equivalent typed models
- Unique client ports and unique bus ports with no overlap
- Complete 0..16383 slot coverage with single primary owner per slot
- Replica anti-affinity against primary virtual AZ when possible; explicit warning when impossible
- harnessctl plan emits full ClusterPlan JSON
```

### Pre-gate commands

```bash
python3 -m py_compile harness/cluster_plan.py harness/port_allocator.py harness/slot_allocator.py harness/planner.py harness/harnessctl.py
python3 -m unittest discover -s tests -p 'test_p04_cluster_plan.py'
python3 -m harness.harnessctl plan --inventory inventories/two-mac-physical-aligned.yaml --scenario scenarios/smoke-6.yaml --json > /tmp/cluster-plan.json
```

### 通过条件

```text
- smoke-6 yields exactly 3 primaries and 3 replicas
- Slots cover 0..16383 without gap or overlap
- Port allocator fails on insufficient or overlapping ranges
- total_nodes not divisible by role/topology requirements fails rather than truncating
```

### 禁止事项

```text
- Do not let cluster_create or runtime recompute slot/replica layout later
- Do not hide anti-affinity violations
```

## P05：Mac/Linux 平台抽象

### 目标

集中 Darwin/Linux 差异，保持 planner、cluster_create、report 与平台命令解耦。

### 允许修改范围

```text
harness/harnessctl.py
harness/platform_adapter.py
harness/platform_darwin.py
harness/platform_linux.py
harness/executor.py
tests/test_p05_platform_adapter.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P05/**
```

### 必须产出

```text
- PlatformAdapter interface
- Darwin and Linux adapters
- FakeExecutor and SubprocessExecutor
- Methods: detect_platform, check_port_available, process_exists, read_process_rss, count_process_fds, list_sockets, supports_host_network, supports_network_fault_injection, network_fault_backend_hint
- doctor --dry-run can report capabilities through adapter without changing system state
```

### Pre-gate commands

```bash
python3 -m py_compile harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py harness/executor.py harness/harnessctl.py
python3 -m unittest discover -s tests -p 'test_p05_platform_adapter.py'
python3 -m harness.harnessctl doctor --dry-run --json
```

### 通过条件

```text
- Core planner imports no platform_darwin/platform_linux module
- Platform adapters are mockable and unit tests do not require real lsof/ps/docker/tc
- Linux migration path is explicit, even when current machine is Darwin
```

### 禁止事项

```text
- Do not scatter os.system/subprocess platform commands through core modules
- Do not claim unsupported network fault support on Darwin
```

## P06：事件、状态与 artifacts 基础设施

### 目标

让所有 harness 动作可审计，并使 report 可完全从磁盘 artifacts 重建。

### 允许修改范围

```text
harness/artifacts.py
harness/events.py
harness/status.py
harness/command_log.py
tests/test_p06_artifacts_events.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P06/**
```

### 必须产出

```text
- ArtifactLayout based on run_id and root directory
- EventRecorder writing JSONL, one valid JSON object per line
- RunStatusWriter and CommandLogWriter
- Readers tolerate corrupted JSONL lines by marking them invalid instead of crashing report
- Event taxonomy includes run, command, node, cluster, fault, failover, metric, assertion events
```

### Pre-gate commands

```bash
python3 -m py_compile harness/artifacts.py harness/events.py harness/status.py harness/command_log.py
python3 -m unittest discover -s tests -p 'test_p06_artifacts_events.py'
```

### 通过条件

```text
- events.jsonl supports append and replay
- artifacts paths are isolated per run_id
- Corrupted event line is represented as invalid evidence, not swallowed silently
```

### 禁止事项

```text
- Do not make report depend on live in-memory objects
- Do not let one run overwrite another run's artifacts
```

## P07：本地进程 nodehost 与 fake runtime

### 目标

支持单 Mac 小集群开发路径；真实 Valkey 缺失时 unit/fake path 仍可验证 nodehost contract。

### 允许修改范围

```text
nodehost/**
harness/nodehost_client.py
harness/artifacts.py
harness/events.py
tests/test_p07_nodehost_local.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P07/**
```

### 必须产出

```text
- nodehost/nodehostctl.py CLI with status/prepare/start/stop/cleanup/metrics
- nodehost/local_process.py local process manager
- nodehost/fake_valkey.py fake runtime
- nodehost/process_table.py run-scoped process table
- harness/nodehost_client.py client contract
- Idempotent start/stop/cleanup behavior
```

### Pre-gate commands

```bash
python3 -m py_compile nodehost/nodehostctl.py nodehost/local_process.py nodehost/fake_valkey.py nodehost/process_table.py harness/nodehost_client.py
python3 -m unittest discover -s tests -p 'test_p07_nodehost_local.py'
python3 -m nodehost.nodehostctl status --json
```

### 通过条件

```text
- No Valkey binary is needed for unit tests
- cleanup only removes state for the specified run_id
- Fake runtime can represent multiple node states and metrics
```

### 禁止事项

```text
- Do not require sudo or real Valkey in P07
- Do not use global process state without run_id scoping
```

## P08：Valkey 配置生成

### 目标

根据 ClusterPlan/NodeSpec 生成真实 Valkey cluster 配置文件；不启动集群。

### 允许修改范围

```text
nodehost/valkey_config.py
nodehost/config_writer.py
nodehost/nodehostctl.py
harness/cluster_plan.py
tests/test_p08_valkey_config.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P08/**
```

### 必须产出

```text
- ValkeyConfigRenderer
- ConfigWriter creating isolated node directories
- Rendered fields: port, cluster-enabled yes, cluster-config-file, cluster-node-timeout, cluster-announce-ip, cluster-announce-port, cluster-announce-bus-port, cluster-port, appendonly no, save "", protected-mode no, bind, loglevel, logfile, dir, pidfile
- Announce IP/port derived from NodeSpec only
- Tests proving no port remap or hard-coded IP assumption
```

### Pre-gate commands

```bash
python3 -m py_compile nodehost/valkey_config.py nodehost/config_writer.py nodehost/nodehostctl.py
python3 -m unittest discover -s tests -p 'test_p08_valkey_config.py'
```

### 通过条件

```text
- Every config value is traceable to ClusterPlan/NodeSpec or explicit scenario config
- Each node directory is independent
- Renderer performs rendering only, not planning
```

### 禁止事项

```text
- Do not calculate ports in config renderer
- Do not hard-code localhost when NodeSpec has announce_ip
```

## P09：cluster command executor 与 fake cluster 状态机

### 目标

实现可测试的 cluster management 状态机，显式建模 MEET、known_nodes 收敛、slot assignment、replicate、cluster_state ok。

### 允许修改范围

```text
harness/valkey_cli.py
harness/fake_cluster.py
harness/cluster_create.py
harness/cluster_check.py
harness/slot_check.py
harness/events.py
tests/test_p09_cluster_state_machine.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P09/**
```

### 必须产出

```text
- ValkeyCli interface and fake implementation
- FakeCluster state machine
- ClusterCreator executing ClusterPlan without replanning
- ClusterChecker and SlotChecker distinguishing known_nodes_missing, slots_missing, replica_missing, cluster_fail
- Events for meet, known_nodes sampling, slots assigned, replica configured, cluster ok/fail
```

### Pre-gate commands

```bash
python3 -m py_compile harness/valkey_cli.py harness/fake_cluster.py harness/cluster_create.py harness/cluster_check.py harness/slot_check.py
python3 -m unittest discover -s tests -p 'test_p09_cluster_state_machine.py'
```

### 通过条件

```text
- Create flow follows plan order deterministically
- Creator does not call planner or recalculate slots/replicas
- Checker surfaces incomplete convergence as structured failure
```

### 禁止事项

```text
- Do not shell out to valkey-cli in unit tests
- Do not use valkey-cli --cluster create as the only model
```

## P10：单 Mac 6 节点 smoke runner

### 目标

跑通 smoke-6 fake-run/dry-run 的完整路径：validate、plan、nodehost、cluster create/check、cleanup、artifacts。

### 允许修改范围

```text
harness/scenario_runner.py
harness/preflight.py
harness/harnessctl.py
harness/nodehost_client.py
harness/cluster_create.py
harness/cluster_check.py
harness/artifacts.py
harness/events.py
harness/status.py
tests/test_p10_single_mac_smoke.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P10/**
```

### 必须产出

```text
- run-scenario CLI wired to ScenarioRunner
- smoke-6 fake backend path
- run artifacts directory containing events.jsonl, run_status.json, cluster_plan.json, command log
- cleanup in finally path
- Optional real Valkey path reports SKIPPED_RESOURCE when binary is absent; fake path must PASS
```

### Pre-gate commands

```bash
python3 -m py_compile harness/scenario_runner.py harness/preflight.py harness/harnessctl.py
python3 -m unittest discover -s tests -p 'test_p10_single_mac_smoke.py'
python3 -m harness.harnessctl run-scenario --inventory inventories/single-mac-dev.yaml --scenario scenarios/smoke-6.yaml --run-id p10-smoke --backend fake --json
```

### 通过条件

```text
- Fake smoke run returns PASS and writes auditable artifacts
- Cleanup executes on failure and success
- Failures are written as events/status, not swallowed
```

### 禁止事项

```text
- Do not require real Valkey for P10 pass
- Do not mark optional real integration as PASS when skipped
```

## P11：进程故障与虚拟 AZ 故障

### 目标

支持 node 级与 virtual AZ 级进程/fake fault：kill、pause、resume、restart；不做网络故障。

### 允许修改范围

```text
harness/faults.py
nodehost/faults_process.py
nodehost/process_table.py
harness/scenario_runner.py
harness/events.py
tests/test_p11_process_faults.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P11/**
```

### 必须产出

```text
- FaultPlan model
- FaultExecutor and ProcessFaultBackend
- Virtual AZ target selector reading ClusterPlan
- Fault events with before/after timestamps
- Idempotent resume/restart semantics
```

### Pre-gate commands

```bash
python3 -m py_compile harness/faults.py nodehost/faults_process.py harness/scenario_runner.py
python3 -m unittest discover -s tests -p 'test_p11_process_faults.py'
```

### 通过条件

```text
- Fault selection is based on ClusterPlan node virtual_az_id
- Repeating resume/restart does not corrupt state
- Fault code does not recompute topology
```

### 禁止事项

```text
- Do not implement network latency/loss in P11
- Do not select targets by ad hoc hostnames when ClusterPlan has explicit IDs
```

## P12：故障接管 timeline 与稳定性断言

### 目标

记录 failover 时间线并计算稳定性指标；不能只用最终 cluster_state ok 判断成功。

### 允许修改范围

```text
harness/failover_timeline.py
harness/failover_observer.py
harness/stability_assertions.py
harness/cluster_check.py
harness/events.py
tests/test_p12_failover_timeline.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P12/**
```

### 必须产出

```text
- FailoverTimeline with fault_injected_at, first_pfail_observed_at, first_fail_observed_at, replica_promoted_at, slots_recovered_at, cluster_ok_at, client_success_restored_at
- Metric calculation: pfail_detection_ms, fail_confirmation_ms, promotion_ms, slot_recovery_ms, cluster_recovery_ms, client_recovery_ms, unavailable_slots_count_max, stale_owner_duration_ms
- FailoverObserver reconstructing timeline from events
- StabilityAssertions returning PASS/FAIL/INCONCLUSIVE with reasons
- Tests for missing PFAIL, missing promotion, client not recovered, stale owner
```

### Pre-gate commands

```bash
python3 -m py_compile harness/failover_timeline.py harness/failover_observer.py harness/stability_assertions.py harness/cluster_check.py
python3 -m unittest discover -s tests -p 'test_p12_failover_timeline.py'
```

### 通过条件

```text
- Complete timeline computes all metrics
- Missing critical evidence yields INCONCLUSIVE, not PASS
- cluster_state ok alone cannot satisfy failover success
```

### 禁止事项

```text
- Do not synthesize missing timestamps
- Do not turn INCONCLUSIVE into PASS for report cosmetics
```

## P13：Docker hostnet nodehost

### 目标

实现 Docker host network scale backend contract：一个虚拟 AZ 一个容器，容器内多个 Valkey 进程；禁止 Docker-in-Docker 和一节点一容器。

### 允许修改范围

```text
docker/**
harness/docker_nodehost.py
harness/nodehost_client.py
harness/preflight.py
tests/test_p13_docker_hostnet.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P13/**
```

### 必须产出

```text
- docker/nodehost.Dockerfile
- docker/nodehost-entrypoint.sh
- DockerNodehostClient
- Docker command builder grouping by virtual_az_id
- Capability handling when host networking or docker CLI is unavailable
- Contract tests proving no one-node-one-container loop
```

### Pre-gate commands

```bash
python3 -m py_compile harness/docker_nodehost.py harness/nodehost_client.py harness/preflight.py
python3 -m unittest discover -s tests -p 'test_p13_docker_hostnet.py'
```

### 通过条件

```text
- docker run commands are per virtual AZ, not per node
- No docker:dind, privileged dockerd, or DOCKER_HOST=tcp:// dependency appears
- Unavailable Docker capability returns structured SKIPPED_RESOURCE for integration, while unit contract still passes
```

### 禁止事项

```text
- Do not implement Docker-in-Docker
- Do not make planner aware of Docker internals
- Do not create one container per Valkey node
```

## P14：多 Mac SSH 编排

### 目标

让 controller 通过 SSH 编排多台 Mac；unit tests 使用 fake SSH，不要求真实多 Mac。

### 允许修改范围

```text
harness/ssh_exec.py
harness/remote_nodehost.py
harness/deployer.py
harness/scenario_runner.py
harness/nodehost_client.py
tests/test_p14_multi_mac_ssh.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P14/**
```

### 必须产出

```text
- SSHExecutor and FakeSSHExecutor
- RemoteNodehostClient
- Deployer supporting preflight, sync/package, start virtual AZ runtime, run nodehostctl, collect artifacts, cleanup
- Multi-host dispatch tests based on ClusterPlan
```

### Pre-gate commands

```bash
python3 -m py_compile harness/ssh_exec.py harness/remote_nodehost.py harness/deployer.py harness/scenario_runner.py
python3 -m unittest discover -s tests -p 'test_p14_multi_mac_ssh.py'
```

### 通过条件

```text
- Fake SSH verifies exact command dispatch and host targeting
- Real SSH absence does not fail unit tests
- Remote orchestration reads ClusterPlan and does not re-plan topology
```

### 禁止事项

```text
- Do not couple SSH implementation to Docker implementation
- Do not require password prompts or interactive SSH in tests
```

## P15：网络故障 backend 与 Linux 迁移能力

### 目标

建立网络故障接口：virtual AZ 隔离、时延、丢包；Darwin 能力不足必须明确 SKIPPED_RESOURCE，Linux tc/netem 路径必须可验证命令构造。

### 允许修改范围

```text
harness/network_faults.py
nodehost/faults_network.py
harness/platform_adapter.py
harness/platform_darwin.py
harness/platform_linux.py
harness/faults.py
tests/test_p15_network_faults.py
tests/helpers/**
tests/conftest.py
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P15/**
```

### 必须产出

```text
- NetworkFaultBackend interface
- UnsupportedNetworkFaultBackend
- LinuxNetemBackend command construction boundaries for tc/netem and firewall selectors
- Darwin capability detection returning capability-limited result
- Targets include cluster bus ports, not only client ports
- Tests for isolate/heal/delay/loss/clear command plans
```

### Pre-gate commands

```bash
python3 -m py_compile harness/network_faults.py nodehost/faults_network.py harness/platform_adapter.py harness/platform_darwin.py harness/platform_linux.py
python3 -m unittest discover -s tests -p 'test_p15_network_faults.py'
```

### 通过条件

```text
- Unsupported environment returns SKIPPED_RESOURCE with reason/evidence
- Linux migration path is explicit and unit-tested by command construction
- Network fault targeting covers cluster bus traffic
```

### 禁止事项

```text
- Do not claim precise Mac network fault injection unless capability check proves it
- Do not execute tc/pf/iptables in unit tests
```

## P16：scale ladder 与最终 report pipeline

### 目标

固化 100/300/500/1000/2000 场景与 report pipeline；2000 是 best-effort empty-node smoke，不是生产能力背书。

### 允许修改范围

```text
scenarios/**
harness/report_builder.py
harness/report_models.py
harness/project_quality.py
harness/harnessctl.py
harness/artifacts.py
harness/events.py
harness/status.py
harness/failover_timeline.py
scripts/project_quality_gate.py
tests/test_p16_report_and_scale.py
tests/helpers/**
tests/conftest.py
Makefile
codex/loop_state.json
codex/current_phase_contract.json
codex/current_phase_contract.md
artifacts/phase-P16/**
```

### 必须产出

```text
- scenarios/scale-300.yaml, scale-500.yaml, scale-1000.yaml, scale-2000-empty.yaml
- Report models and builder reconstructing report from artifacts
- Report sections: summary, environment, virtual AZ topology, ClusterPlan, test matrix, cluster create, fault/failover timeline, migration/CLUSTERSCAN if implemented, resource metrics, stability gates, verified/unverified, failures/skips/inconclusive, reproduce commands, raw artifacts index
- project_quality_gate.py finalized and strict
- Fixture report artifacts for unit tests
```

### Pre-gate commands

```bash
python3 -m py_compile harness/report_builder.py harness/report_models.py harness/project_quality.py harness/harnessctl.py scripts/project_quality_gate.py
python3 -m unittest discover -s tests -p 'test_p16_report_and_scale.py'
python3 scripts/project_quality_gate.py --candidate-phase P16 --json
```

### 通过条件

```text
- Scale ladder is configuration-driven, not branchy hard-coded code paths
- Report explicitly represents MISSING, INCONCLUSIVE, NOT_VALIDATED, SKIPPED_RESOURCE and FAIL
- scale-2000-empty clearly does not validate throughput, production latency, production RTO, or physical 3-AZ durability
- project_quality_gate validates manifest consistency, all prior phases, forbidden patterns, runnable tests, and report honesty
```

### 禁止事项

```text
- Do not beautify failures into pass
- Do not claim production validation from fake/empty-node runs
```

