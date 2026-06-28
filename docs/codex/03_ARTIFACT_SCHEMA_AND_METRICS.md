# Artifact Schema 与 Metrics 契约

本项目的事实来源是 machine-readable artifact。任何报告、图表、表格、结论都必须从 artifact 生成。

## 1. Artifact 目录结构

每次运行必须生成唯一 `run_id`。推荐目录：

```text
artifacts/runs/<run_id>/
  manifest.json
  config/
    input.yaml
    normalized.yaml
    config_hash.txt
  plan/
    cluster_plan.json
    placement.json
    resource_estimate.json
    safety_verdict.json
  runtime/
    node_manifest.json
    container_manifest.json
    resource_ledger.json
  events/
    events.jsonl
    lifecycle_events.jsonl
  metrics/
    client_metrics.jsonl
    cluster_samples.jsonl
    valkey_info_samples.jsonl
    docker_stats.jsonl
    metrics_summary.json
  operations/
    operation_matrix.json
    operation_results.jsonl
  faults/
    fault_plan.json
    fault_events.jsonl
    fault_effects.json
  failover/
    failover_timeline.json
    split_brain_analysis.json
  stability/
    invariant_results.jsonl
    resource_drift.json
    stability_summary.json
  analysis/
    management_performance.json
    failover_efficiency.json
    stability_summary.json
    missing_metrics.json
  reports/
    report.md
    report.html
    tables/*.csv
    charts/*
  gate_results/
    *.json
  safety/
    host_network_audit.json
  cleanup/
    cleanup_result.json
  logs/
    index.json
```

## 2. 通用字段

所有 JSON/JSONL 记录建议包含：

```json
{
  "schema_version": "...",
  "run_id": "...",
  "phase_id": "Pxx",
  "created_at": "ISO-8601",
  "monotonic_ms": 0,
  "status": "PASS|FAIL|MISSING|SKIPPED_WITH_REASON|BLOCKED_ENV|BLOCKED_RESOURCE|SAFETY_BLOCKED|BLOCKED_PROGRESS",
  "source": "component-name"
}
```

缺失值必须显式，不能用 `0`、`null`、空数组、空表或自然语言句子代替。只有真实测得的数值才可以写入数值字段：

```json
{
  "metric": "container_cpu_percent",
  "status": "MISSING",
  "reason": "docker stats unavailable in this runtime profile"
}
```

跳过必须显式，并说明是 optional capability、条件型 capability，还是环境未配置导致无法验证：

```json
{
  "capability": "az.network.delay",
  "status": "SKIPPED_WITH_REASON",
  "reason": "sandbox backend lacks safe delay injection support on this host",
  "whether_blocks_release": false
}
```

阻塞必须显式：

```json
{
  "capability": "real_multi_host_gate",
  "status": "BLOCKED_ENV",
  "reason": "no multi-host configuration was provided",
  "required_for_all_phases_pass": false
}
```

mandatory gate 的阻塞不能被报告层改写成 PASS。

### 2.1 缺失与阻塞的结构化规则

所有 artifact schema 都必须允许并校验以下结构化状态：

```json
{
  "status": "MISSING|SKIPPED_WITH_REASON|BLOCKED_ENV|BLOCKED_RESOURCE|SAFETY_BLOCKED|BLOCKED_PROGRESS",
  "reason": "human-readable but specific reason",
  "source": "component or gate id",
  "impact": "what analysis/report/gate is affected",
  "whether_blocks_phase": true
}
```

真实观测值为 0 时才允许写 0，并且必须能回溯 raw evidence。缺失指标、未运行能力、环境阻塞、资源阻塞、安全阻塞、无进展阻塞必须用上述结构表达。

## 3. manifest.json

`manifest.json` 是 run 的入口索引。

必备字段：

```json
{
  "schema_version": "valkey9-harness.run_manifest.v1",
  "run_id": "...",
  "phase_id": "Pxx",
  "status": "PASS|FAIL|...",
  "started_at": "...",
  "ended_at": "...",
  "duration_ms": 0,
  "git": {
    "commit": "...",
    "dirty": true
  },
  "valkey": {
    "target_version": "9.1.0",
    "observed_versions": [],
    "image": "...",
    "image_digest": "..."
  },
  "environment": {
    "controller_os": "macos|linux",
    "controller_arch": "arm64|amd64|unknown",
    "docker_available": true
  },
  "artifacts": [],
  "gate_results": [],
  "cleanup_result": "cleanup/cleanup_result.json"
}
```

## 4. cluster_plan.json

必须表达：

- physical hosts；
- virtual AZs；
- shards；
- primary/replica；
- node count；
- slot assignment；
- runtime backend；
- scale safety verdict；
- resource estimates；
- forbidden default paths rejected。

主备/AZ 示例：

```json
{
  "shard_id": "s-0001",
  "nodes": [
    {"node_id": "n-0001", "role": "primary", "virtual_az": "az-a", "host_id": "mac-1"},
    {"node_id": "n-0002", "role": "replica", "virtual_az": "az-b", "host_id": "mac-1"}
  ],
  "anti_affinity": "PASS"
}
```

## 5. events.jsonl

事件流用于建立时间线。

事件类型至少包括：

```text
lifecycle.*
cluster.*
workload.*
operation.*
fault.*
failover.*
metrics.*
cleanup.*
gate.*
safety.*
```

每条事件必须包含 `wall_time` 与 `monotonic_ms`。failover 分析优先使用 monotonic timeline，wall time 用于人类阅读。

## 6. Gate result schema

每个 gate result 必须包含可被 wrapper 语义校验的字段：

```json
{
  "schema_version": "valkey9-harness.gate_result.v1",
  "gate_id": "P03.real_valkey_6node_cluster",
  "phase_id": "P03",
  "run_id": "20260627T000000Z-P03-real-small",
  "gate_type": "REAL_VALKEY_E2E",
  "required": true,
  "status": "PASS",
  "started_at": "...",
  "finished_at": "...",
  "commands": [],
  "artifacts": [
    "runtime/node_manifest.json",
    "evidence/cluster_info.txt",
    "cleanup/cleanup_result.json"
  ],
  "evidence": {
    "real_valkey": true,
    "valkey_version": "9.1.0",
    "node_count": 6,
    "cluster_state": "ok",
    "slot_coverage": 16384,
    "client_port_reachability": "PASS",
    "cluster_bus_reachability": "PASS",
    "runtime_mode": "docker_container_namespace",
    "uses_host_port_mapping": false
  },
  "missing": [],
  "skipped": [],
  "blocked": [],
  "failure": null,
  "audit_ref": "audits/P03.md"
}
```

必须字段包括 `schema_version`、`gate_id`、`phase_id`、`run_id`、`gate_type`、`required`、`status`、`started_at`、`finished_at` 或等价结束时间字段、`artifacts`、`evidence`。mandatory 字段缺失时，gate status 不能为 `PASS`。

gate result 中的 `missing`、`skipped`、`blocked` 必须使用结构化对象，至少包含 `field_or_capability`、`status`、`reason` 或 `missing_reason`，可用时包含 `source_refs`。缺失 mandatory 字段时 gate status 必须是 `FAIL` 或 `BLOCKED_*`，不能是 `PASS`。不得用 `0`、空数组、空表或自然语言含糊句子代替缺失字段。

P03 及之后真实 Valkey gate 的 `evidence` 中必须包含 `valkey_version`、`node_count`、`cluster_state`、`slot_coverage`、`client_port_reachability`、`cluster_bus_reachability`、`runtime_mode`、`uses_host_port_mapping`。若 `uses_host_port_mapping=true`，不得作为真实 Valkey Cluster gate PASS。

## 7. Metrics 维度

### 7.1 集群管理性能

必须尽量覆盖：

- plan latency；
- sandbox start latency；
- per-node startup latency；
- cluster create latency；
- cluster convergence latency；
- slot coverage convergence latency；
- `CLUSTER INFO` latency；
- `CLUSTER NODES` latency 与 parse latency；
- add/remove node latency；
- add/remove replica latency；
- reshard/rebalance latency；
- manual failover latency；
- rolling restart latency；
- cleanup latency；
- residue count；
- manager CPU/memory if available。

### 7.2 管理操作测试矩阵

矩阵轴至少包括：

- node count：6、10、30、50、100；
- shards；
- replicas per primary：0、1、可选 2；
- virtual AZ count：1、3、可选 5；
- host count：1、N；
- workload：none、read-heavy、write-heavy、mixed、hot-key；
- workload timing：before、during、after、whole-run；
- operation：create、check、add、remove、reshard、rebalance、failover、restart、recover；
- fault：none、node、AZ、network delay/loss/flap/partition。

### 7.3 故障接管效能

必须支持或显式缺失：

- fault injected time；
- first failure observed time；
- election/promotion start；
- new primary observed；
- cluster state recovered；
- slot coverage recovered；
- workload recovered；
- client error window；
- RTO；
- observed RPO approximation；
- acknowledged write missing count；
- MOVED/ASK/TRYAGAIN/CLUSTERDOWN/error count；
- stale/incorrect read evidence if validation enabled。

### 7.4 脑裂指标

必须从证据中推导，不得凭场景名称编造。

- same slot multiple primaries；
- same shard multiple primaries；
- conflicting cluster views；
- config epoch conflict；
- minority partition accepted writes；
- divergent values observed by clients；
- split window duration；
- convergence after heal。

### 7.5 稳定性

必须支持或显式缺失：

- cluster_state_ok_ratio；
- slot_coverage_ok_ratio；
- workload_success_ratio；
- latency p50/p95/p99/p999/max；
- ops/sec avg/min/max；
- resource RSS/CPU trends；
- file descriptor count if available；
- reconnect count；
- cluster state flaps；
- node restarts；
- log error/warn count；
- cleanup residue count。

## 8. Analysis artifact

`analysis/*.json` 必须保存 derived metric 与 source reference。

示例：

```json
{
  "metric": "failover_detection_ms",
  "value": 3200,
  "unit": "ms",
  "source_refs": [
    "faults/fault_events.jsonl#event_id=fault.injected.1",
    "metrics/cluster_samples.jsonl#event_id=cluster.fail.observed.7"
  ],
  "status": "PASS"
}
```

## 9. Report 规则

报告必须包含：

1. run summary；
2. config summary；
3. topology/placement；
4. workload；
5. management operation matrix；
6. fault/failover timeline；
7. split-brain indicators；
8. stability summary；
9. missing/skipped metrics；
10. artifact index；
11. risk/limitations。

每个报告数字必须能回溯 artifact。若无法回溯，report gate FAIL。报告必须展示 `MISSING`、`SKIPPED_WITH_REASON` 与 `BLOCKED_*`，不得把缺失数据当成 0、不得用空图表暗示指标正常、不得用自然语言含糊带过。
