# Harness、Gate 与 Audit 契约

本文件定义项目如何保证 Codex 在 goal-driven loop 中不会跑偏。核心原则：phase 不是靠 Codex 自我宣称完成，而是靠 harness、artifact 和 audit 决定。

## 1. Harness 分层

```text
+--------------------------------------------------+
| release audit / final gate                       |
+--------------------------------------------------+
| scale ladder: real 10 / 30 / 50 / 100 nodes      |
+--------------------------------------------------+
| real Valkey e2e: cluster/workload/fault/failover |
+--------------------------------------------------+
| Docker smoke: sandbox lifecycle / cleanup        |
+--------------------------------------------------+
| fake integration: deterministic orchestration    |
+--------------------------------------------------+
| contract/property tests: schema/planner/artifact |
+--------------------------------------------------+
| unit tests: pure logic/parser/metrics            |
+--------------------------------------------------+
| static/safety/memory checks                      |
+--------------------------------------------------+
```

## 2. Gate 类型

每个 gate result 必须明确写入 `gate_type`。

```text
STATIC_SAFETY
MEMORY_STATE
SCHEMA_CONTRACT
UNIT
PROPERTY
FAKE_INTEGRATION
DOCKER_SMOKE
REAL_VALKEY_E2E
REAL_VALKEY_FAULT
REAL_VALKEY_SCALE
ARTIFACT_REGRESSION
REPORT_VALIDATION
CLEANUP
AUDIT
```

fake gate 只能写 `FAKE_INTEGRATION`，不得写 `REAL_VALKEY_E2E`、`REAL_VALKEY_FAULT` 或 `REAL_VALKEY_SCALE`。每个 mandatory gate 都必须在 `state/codex_state.json.expected_gate_results` 中声明，并在 `artifacts/runs/<run_id>/gate_results/` 写 machine-readable JSON；没有 gate result JSON，phase 不能 PASS。phase、audit、wrapper 后置检查都只能依据该 JSON、artifact、状态文件和命令证据做判断，不能依据 Codex 自述“已通过”。

mandatory gate result JSON 至少必须能被 wrapper 校验这些字段：`schema_version`、`phase_id`、`run_id`、`gate_type`、`required`、`status`、`started_at`、`finished_at` 或 `ended_at`、`evidence`、`artifacts`。缺字段时，gate status 不得为 `PASS`。

## 3. Gate Result 状态

```text
PASS
FAIL
BLOCKED_ENV
BLOCKED_RESOURCE
SAFETY_BLOCKED
BLOCKED_PROGRESS
SKIPPED_WITH_REASON
MISSING
```

规则：

- mandatory gate 不允许用 `SKIPPED_WITH_REASON` 代替 PASS。
- 环境缺失只能是 `BLOCKED_ENV`，不等于 PASS。
- 资源不足只能是 `BLOCKED_RESOURCE`，不等于 PASS。
- 安全违规是 `SAFETY_BLOCKED`，必须先修复或回滚。连续无进展或最大尝试次数耗尽是 `BLOCKED_PROGRESS`，不等于 PASS。
- mandatory gate 没有 machine-readable gate result 时等同 `MISSING`，phase 不得 PASS。
- 缺失指标或缺失证据必须结构化写 `MISSING`、`SKIPPED_WITH_REASON` 或 `BLOCKED_*`；不得写 0、空数组、空表或自然语言句子来掩盖缺失。

## 4. 静态安全 gate

静态安全 gate 必须检查：

1. 默认路径无 `sudo` 系统网络修改。
2. 默认路径无 host `pfctl`、host `iptables`、host `nft`、host `route`、host `ip route`、host `ifconfig down`、host `networksetup`。
3. 默认路径不使用 Docker host network。
4. 默认真实 cluster 不依赖 Docker 端口映射/NAT。
5. 默认 make/loop/CI 不会运行 1000 节点。
6. fault executor 明确作用域：container namespace、run-owned proxy、run-owned sandbox；不能是 host-global。
7. 进程、容器、网络、目录、PID 文件均有 run_id 与 cleanup 注册。
8. 报告不能引用不存在的 artifact 字段。

允许 sandbox 内使用网络工具，但必须满足：

- 命令在 run-owned container/namespace 内执行；
- artifact 记录作用域、目标、前后状态；
- host safety audit 证明物理机未被修改；
- cleanup 验证故障状态已清除。

## 5. Schema 与 contract gate

必须验证：

1. 配置 schema 接受有效配置。
2. 配置 schema 拒绝危险配置。
3. artifact schema 校验所有 sample。
4. 缺失指标用结构化 `MISSING`，并包含 `reason`、`source`、`impact`。
5. 跳过能力用结构化 `SKIPPED_WITH_REASON`，并包含 `reason`、`scope`、`whether_blocks_release`。
6. gate result 能被 machine 解析。
7. 缺失或跳过字段不得用 `0`、空数组、空 CSV、空图表或自然语言含糊带过。
8. schema version 可追踪。
9. 旧 baseline artifact 能被兼容读取或被明确迁移。

## 6. Unit 与 property gate

Unit gate 覆盖：

- 配置归一化；
- placement 计算；
- AZ anti-affinity；
- scale limit；
- artifact writer；
- Valkey CLI/INFO/CLUSTER 输出 parser；
- metrics summary；
- failover timeline；
- split-brain detector；
- cleanup registry；
- memory state parser。

Property gate 至少覆盖：

- 随机 shard/replica/AZ/host 输入下的 placement invariant；
- 端口、目录、container name 唯一性；
- 1000 默认拒绝；
- missing/skipped artifact 表达；
- fault target selector 不越界。

## 7. Fake integration gate

fake integration 用于验证 orchestration，不用于真实能力结论。fake artifact 必须显式写：

```json
{
  "evidence_kind": "FAKE_INTEGRATION",
  "real_valkey": false
}
```

P03 以后 fake gate 可以继续存在，但只能辅助回归，不能满足 mandatory real gate。

## 8. Docker smoke gate

Docker smoke 不等于真实 Valkey e2e。它只验证 sandbox mechanics：

1. run-owned network/container 创建与删除；
2. label-based cleanup；
3. no host network；
4. no published Valkey cluster ports in default profile；
5. container exec/log collection；
6. optional sandbox capability check；
7. cleanup idempotency。

## 9. Real Valkey e2e gate

真实 gate 必须包含：

1. Valkey server 版本证据。
2. 镜像 digest 或 source tag。
3. cluster 节点数与 planner 一致。
4. `cluster_state=ok` 或预期故障场景的明确状态。
5. 16384 slot coverage，除非测试场景预期中断且已标注。
6. primary/replica/AZ/host mapping 与 plan 对齐。
7. workload 或操作的真实结果。
8. raw evidence：cluster info、cluster nodes、events、metrics、logs index。
9. cleanup report。
10. gate result JSON。

P03-P05 必须引入真实 gate；P06 以后每个能力必须至少一次真实 gate 证明。

P03 及之后所有真实 Valkey gate result 必须在 top-level 或 `evidence` 中包含并可被 wrapper 解析：

```json
{
  "valkey_version": "9.1.0",
  "node_count": 6,
  "cluster_state": "ok",
  "slot_coverage": 16384,
  "client_port_reachability": "PASS",
  "cluster_bus_reachability": "PASS",
  "runtime_mode": "docker_container_namespace",
  "uses_host_port_mapping": false
}
```

`client_port_reachability` 验证客户端端口连通性；`cluster_bus_reachability` 验证 cluster bus 连通性。若 `uses_host_port_mapping=true`，或 runtime 依赖 Docker host port mapping/NAT 来证明 cluster 语义，该 gate 不得 `PASS`。若上述字段任一缺失，必须写结构化 `MISSING` 与 `missing_reason`，且 mandatory real gate status 不能是 `PASS`。

## 10. Fault gate

每个 fault gate 至少验证：

1. fault plan 可解释。
2. target selector 不越界。
3. fault injection 在 sandbox 内执行。
4. fault active state 可观测。
5. Valkey cluster 或 workload 观测到预期影响。
6. fault recovery 执行。
7. fault cleanup 后状态干净。
8. host safety audit 通过。

如果某 backend 不支持某类网络故障，不得伪造结果；必须写 `SKIPPED_WITH_REASON`，并在 capability matrix 中标注未验证。

## 11. Scale gate

Scale gate 必须按 10、30、50、100 节点分别运行。每一级 gate 包含：

```text
resource preflight
  -> plan
  -> sandbox start
  -> cluster create/check
  -> workload smoke
  -> metrics sample
  -> analysis
  -> cleanup
  -> artifact validation
```

资源不足时输出 `BLOCKED_RESOURCE`，不得把较小规模 gate 当作较大规模 PASS。

## 12. Artifact regression gate

每次修改 artifact schema、metrics、analysis、report 后，必须运行 artifact regression：

- baseline artifact 可读取；
- schema version 处理正确；
- derived metric 稳定或变化有迁移记录；
- report 不引用缺失字段；
- charts 可由 artifact 重新生成。

## 13. Cleanup gate

任何启动资源的 phase 都必须有 cleanup gate。cleanup gate 检查：

1. run-owned containers = 0 或符合预期保留。
2. run-owned networks = 0 或符合预期保留。
3. run-owned processes = 0。
4. run-owned PID files 清理。
5. run-owned temp dirs 清理或归档。
6. fault state 清除。
7. artifact 写入 cleanup result。

cleanup 失败时，即使业务 gate 通过，phase 也不得 PASS。

## 14. Audit 规则

每个 phase 必须写 `audits/Pxx.md`。audit 不应只是总结文字，必须检查证据。audit 的判定只能来自 artifact、gate result、cleanup result、状态机文件与代码检查结果；不能因为 Codex 的自然语言总结说“已通过”就判定 PASS。

Audit 必须至少核对：`state/codex_state.json` 中的 phase/run_id、`PHASE_LEDGER.md` 最新记录、`ARTIFACT_INDEX.md` 中的 run_id、mandatory gate result JSON、cleanup result、phase 对应 `audits/Pxx.md` 自身。任一项缺失或不一致，audit 只能写 FAIL 或 `BLOCKED_*`。

### 14.1 Audit 文件最小固定格式

每个 `audits/Pxx.md` 必须包含以下固定字段。wrapper 可以读取这些字段；缺字段、字段为空或 `Decision` 不是允许值时，audit 不具备门禁效力。

```markdown
# Pxx Audit

Phase: Pxx
Run ID: <run_id>
Decision: PASS | FAIL | BLOCKED_ENV | BLOCKED_RESOURCE | SAFETY_BLOCKED | BLOCKED_PROGRESS

## Gate Results
| gate_id | gate_type | required | status | gate_result_path |
|---|---|---:|---|---|

## Artifact Evidence
| artifact | schema | status | hash_or_ref |
|---|---|---|---|

## Cleanup Evidence
- cleanup_result: artifacts/runs/<run_id>/cleanup/cleanup_result.json
- cleanup_status: PASS | FAIL | SKIPPED_WITH_REASON
- active_resources_after_cleanup: 0

## Reasons
- Decision reason:
- Missing / skipped / blocked evidence:
- Risks:
```

`Decision` 只能是 `PASS`、`FAIL`、`BLOCKED_ENV`、`BLOCKED_RESOURCE`、`SAFETY_BLOCKED`、`BLOCKED_PROGRESS`。`Decision: PASS` 必须引用当前 run_id、所有 mandatory gate result、artifact evidence 与 cleanup evidence。audit 为空、没有 `Decision: PASS`、没有引用 run_id/gate/artifact/cleanup 时，wrapper 必须停止，不得继续推进。

### 14.2 Mandatory gate 判定规则

mandatory gate 判定必须采用 artifact-first 规则：

1. gate result JSON 的 `required` 必须为 `true`。
2. gate result JSON 的 `status` 必须是 `PASS`，且不能来自 fake gate 冒充。
3. gate result JSON 必须通过语义字段检查：`schema_version`、`phase_id`、`run_id`、`gate_type`、时间字段、`evidence`、`artifacts` 完整。
4. gate result JSON 的 `artifacts` 中列出的路径必须存在，并被 `ARTIFACT_INDEX.md` 索引。
5. P03 及之后真实 Valkey gate 必须通过真实 Valkey 字段检查，且 `uses_host_port_mapping=false`。
6. cleanup result 必须存在且状态为 PASS，或明确记录无资源可清理的结构化说明。
7. audit 必须使用固定格式、`Decision: PASS`，并引用上述证据路径。

自然语言说明只能作为辅助，不具备通过 gate 的效力。

## 15. 失败与修复策略

### 15.1 普通 gate FAIL

记录失败 artifact，在同一 phase 修复，重跑失败 gate 及相关回归。不能跳到下一 phase。

### 15.2 Safety failure

立即进入 `SAFETY_BLOCKED`，停止新增功能。修复或回滚后必须重跑 safety gate。

### 15.3 Flaky gate

不得直接忽略。需要记录 flake 证据，找出原因或把 gate 标为不稳定且 phase 不 PASS。关键真实 gate 建议连续多次通过后再记录稳定。

### 15.4 Resource blocker

资源不足时记录 `BLOCKED_RESOURCE` artifact。不得降级规模后声明原 gate PASS。

### 15.5 Environment blocker

缺少 Docker、缺少远端 host、无法拉取镜像等属于 `BLOCKED_ENV`。不得用 fake 替代。

### 15.6 No-progress blocker

自动 loop 允许同一 phase 多次修复，但不能无限循环。同一 phase 达到 `max_attempts_per_phase`，或连续 `max_no_progress_rounds` 次没有新增 gate result、artifact、audit、cleanup evidence 或明确修复记录时，必须写入明确 blocker：

- 如果最后一个真实原因是环境缺失，保留 `phase_status = "BLOCKED_ENV"`。
- 如果最后一个真实原因是资源不足，保留 `phase_status = "BLOCKED_RESOURCE"`。
- 如果最后一个真实原因是安全风险，保留 `phase_status = "SAFETY_BLOCKED"`。
- 如果只是实现无法收敛，写 `phase_status = "FAIL"`、`blocked = true`、`blocker_type = "NO_PROGRESS"` 或 `"MAX_ATTEMPTS_EXCEEDED"`。
- `last_progress_summary` 写最后一次真实进展，`HANDOFF.md` 写下一步需要人工判断的最小信息。

No-progress blocker 不是 PASS；wrapper 必须停止自动循环。

## 16. No-progress 与重试门禁

自动 loop 允许同一 phase 多次修复，但不能无限循环。wrapper 与 `MEMORY_STATE` gate 至少检查：

1. `state/codex_state.json.phase_attempt` 是否超过 `max_attempts_per_phase`。
2. `no_progress_count` 是否达到 `max_no_progress_rounds`。
3. `last_progress_summary` 是否能说明本轮相对上一轮新增了 artifact、gate result、测试通过项、cleanup 改善或明确 blocker。
4. 如果没有新增可验证事实，只能进行有限次数修复；达到阈值后必须写 `BLOCKED_ENV`、`BLOCKED_RESOURCE` 或 `SAFETY_BLOCKED`；若只是实现无法收敛，则写 `phase_status=BLOCKED_PROGRESS`、`blocked=true`、`blocker_type=NO_PROGRESS|MAX_ATTEMPTS_EXCEEDED`，并在 `HANDOFF.md` 中写明人工需要处理的阻塞。

达到阈值后继续无状态重试属于 loop failure。

## 17. CI 门禁建议

CI 可分 profile：

1. `fast`: static、schema、unit、property、fake integration。
2. `docker-smoke`: Docker lifecycle 与 cleanup。
3. `real-small`: 真实 6/10 节点 Valkey gate。
4. `fault`: 真实 fault/failover gate。
5. `scale`: 10/30/50/100 gate，资源充足时运行。
6. `1000-dry-run`: 仅 opt-in dry-run，不真实启动 1000。

CI 不得默认执行 1000 真实节点。
