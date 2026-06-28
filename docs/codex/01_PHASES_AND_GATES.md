# Phase 划分与 Gate 规则

每个 phase 必须明确：做什么、不做什么、必须真实验证什么、产物放哪里、失败怎么处理、状态如何记录、下一步如何判断。

## 0. Phase 状态机

```text
NOT_STARTED
  -> IN_PROGRESS
  -> GATE_RUNNING
  -> PASS
  -> FAIL
  -> FIXING
  -> ROLLED_BACK
  -> BLOCKED_ENV
  -> BLOCKED_RESOURCE
  -> SAFETY_BLOCKED
```

规则：

- `PASS` 只允许在 mandatory gate 全部通过后写入。
- `BLOCKED_*` 是真实状态，不是 PASS。
- `SKIPPED_WITH_REASON` 只能用于 optional gate 或非当前环境可验证的能力，不得用于逃避 mandatory real gate。
- `SAFETY_BLOCKED` 必须先修复或回滚，不能继续开发新能力。
- 每个 phase 的 mandatory gate 都必须在 `state/codex_state.json.expected_gate_results` 中声明，并生成 machine-readable gate result，路径登记到 `ARTIFACT_INDEX.md`，并被 `audits/Pxx.md` 引用。
- phase PASS 的判定必须同时满足：`expected_gate_results` 对应的 mandatory gate 全部 `status=PASS`、audit `Decision: PASS`、cleanup result PASS 或结构化无资源说明、`ARTIFACT_INDEX.md` 与 gate result 路径一致。自然语言总结不能作为 PASS 依据。
- audit 只能基于 artifact、gate result、状态文件与实际命令证据判定，不能基于 Codex 自然语言总结判定。
- P03 及之后的真实 Valkey gate result 必须包含 `valkey_version`、`node_count`、`cluster_state`、`slot_coverage`、`client_port_reachability`、`cluster_bus_reachability`、`runtime_mode`、`uses_host_port_mapping`。若 `uses_host_port_mapping=true`，该 gate 不得作为真实 Valkey Cluster gate PASS。
- phase PASS 后必须更新 `last_completed_phase`，并把 `current_phase` 推进到下一 phase；终局完成才允许写 `ALL_PHASES_PASS`。
- phase FAIL 后可以在同一 phase 修复；达到 `state/codex_state.json` 中定义的最大尝试次数或连续无进展阈值后，必须写入明确 blocker：环境问题写 `BLOCKED_ENV`，资源问题写 `BLOCKED_RESOURCE`，安全问题写 `SAFETY_BLOCKED`，实现无法收敛则写 `phase_status=BLOCKED_PROGRESS`、`blocked=true`、`blocker_type=NO_PROGRESS|MAX_ATTEMPTS_EXCEEDED`。不得静默无限重试。


### 0.1 Machine-readable gate 完整性

每个 phase 至少要让 wrapper 能回答四个问题：本 phase 期望哪些 mandatory gate；这些 gate 的 JSON 在哪里；这些 gate 是否都 `status=PASS`；audit 和 cleanup 是否引用同一 run_id 与证据链。Codex 不能通过修改 `phase_status` 绕过这些检查。

P03-P12 必须至少有一个真实 Valkey 相关 gate 或引用真实 Valkey run 的 gate。fake gate、空 gate JSON、只含自然语言摘要的 gate JSON、缺少真实网络连通性字段的 gate JSON，都不能满足 P03 之后的真实 gate 语义。

`ALL_PHASES_PASS` 只能在 P00-P13 均有 PASS ledger、mandatory gate result PASS、audit PASS、artifact index 一致和 cleanup evidence 完整时写入；否则 final release postcheck 必须失败。

---

## P00 — 项目契约、仓库骨架、状态机

### 做什么

建立项目初始结构、Codex 工程契约、phase ledger、runbook state、decision log、risk register、artifact index、cleanup registry、基础安全检查入口。P00 的目标是让后续 loop 不依赖聊天记忆，并完成首轮状态机初始化闭环。

### 不做什么

- 不启动 Valkey。
- 不实现 runtime。
- 不声明项目可用。
- 不创建会影响 host 网络的脚本。
- 不让状态只停留在聊天记录里。

### 必须真实验证什么

- 仓库存在并校验以下状态文件：`docs/codex/RUNBOOK_STATE.md`、`docs/codex/PHASE_LEDGER.md`、`docs/codex/DECISION_LOG.md`、`docs/codex/RISK_REGISTER.md`、`docs/codex/ARTIFACT_INDEX.md`、`docs/codex/HANDOFF.md`、`state/codex_state.json`、`state/cleanup_registry.json`。
- phase ledger 可追加。
- artifact 根目录存在。
- safety rule 文档化并能被检查脚本引用。
- 最小 self-check 能运行。
- P00 gate result、audit 与 artifact index 一致。

### 产物放哪里

```text
docs/codex/RUNBOOK_STATE.md
docs/codex/PHASE_LEDGER.md
docs/codex/DECISION_LOG.md
docs/codex/RISK_REGISTER.md
docs/codex/ARTIFACT_INDEX.md
docs/codex/HANDOFF.md
state/codex_state.json
state/cleanup_registry.json
state/gate_index.json
state/latest_run.json
artifacts/runs/.gitkeep
artifacts/runs/<run_id>/gate_results/P00_state_bootstrap.json
audits/P00.md
```

### 失败怎么处理

缺少状态文件、状态 JSON 不可解析、ledger 不可追加、artifact 根目录缺失、安全规则不可追踪、P00 gate result 缺失或与 artifact index 不一致时，phase FAIL。发现默认 host 网络修改路径时，标记 `SAFETY_BLOCKED` 并移除或隔离相关路径。

### 状态如何记录

`PHASE_LEDGER.md` 追加 P00 记录；`RUNBOOK_STATE.md` 写当前 phase、已完成事项、下一步；`state/codex_state.json` 写 machine-readable 状态、attempt 计数、last progress 摘要、gate/audit 路径与下一 phase。

### 下一步如何判断

P00 PASS 后必须把 `state/codex_state.json.current_phase` 更新为 P01，并让 wrapper 下一轮自动继续。进入条件是：Codex 可以只靠仓库文件恢复当前工程状态，且 P00 audit、gate result、artifact index、cleanup registry 一致。

---

## P01 — 配置 Schema 与 Artifact Schema

### 做什么

定义配置 schema 与 artifact schema。配置必须覆盖 physical hosts、virtual AZ、Valkey cluster、workload、fault plan、safety limits、output/report。artifact 必须覆盖 run manifest、plan、events、metrics、operation result、fault result、analysis result、gate result。

### 不做什么

- 不启动 Valkey。
- 不写假指标。
- 不让未知配置字段静默通过，除非明确放入 extension 区域。
- 不把图表当作原始数据。

### 必须真实验证什么

本 phase 允许 fake-only，但必须验证：

- 有效配置通过。
- 危险配置被拒绝。
- 1000 节点默认不能执行。
- `1 primary + 1 replica + 3 AZ` 的约束可表达。
- artifact 示例能被 schema 校验。

### 产物放哪里

```text
schemas/config.schema.json
schemas/artifacts/*.schema.json
examples/configs/*.yaml
examples/artifacts/*
artifacts/runs/<run_id>/schema_validation.json
audits/P01.md
```

### 失败怎么处理

schema 接受危险配置、无法表达安全边界、无法校验 artifact 示例时，phase FAIL。若 1000 节点存在默认执行路径，标记 `SAFETY_BLOCKED`。

### 状态如何记录

记录 schema 版本、示例配置、被拒绝的危险配置、artifact sample 校验结果。

### 下一步如何判断

P01 PASS 后进入 P02。进入条件是：planner 可以把归一化配置作为唯一输入；所有 mandatory schema gate 都有 machine-readable gate result，且缺失字段只能以结构化 `MISSING` / `SKIPPED_WITH_REASON` / `BLOCKED_*` 表达。

---

## P02 — Placement Planner、资源预检、Dry-run

### 做什么

根据配置生成 cluster plan：node count、shard、primary/replica、virtual AZ、physical host、端口、目录、container name、资源估算、scale verdict。支持 10/30/50/100 planning 与 1000 opt-in dry-run planning。

### 不做什么

- 不启动 Valkey。
- 不占用端口。
- 不创建进程。
- 不把 1000 dry-run 当成真实运行。
- 不因资源不足静默降低用户请求规模。

### 必须真实验证什么

- 单 host 单 AZ plan。
- 单 host 多 AZ plan。
- 多 host 多 AZ plan。
- primary/replica AZ anti-affinity。
- 节点均匀分布。
- 端口/目录/container name 无冲突。
- 默认拒绝 1000 真实运行。
- opt-in 1000 只输出 dry-run 与资源估算。

### 产物放哪里

```text
artifacts/runs/<run_id>/plan/cluster_plan.json
artifacts/runs/<run_id>/plan/placement.json
artifacts/runs/<run_id>/plan/resource_estimate.json
artifacts/runs/<run_id>/plan/safety_verdict.json
audits/P02.md
```

### 失败怎么处理

anti-affinity 失败、资源冲突、scale verdict 错误、1000 默认执行路径存在时，不得进入 P03。

### 状态如何记录

记录已验证规模、AZ/host 组合、资源预检结果、dry-run run_id、planner 风险。

### 下一步如何判断

P02 PASS 后进入 P03。进入条件是：真实 runtime 可以安全消费 planner 输出。

---

## P03 — 本地 Docker/Container Namespace Runtime 与真实 Valkey 小集群

### 做什么

引入真实 Valkey gate。在本地 Docker/container namespace sandbox 中拉起真实 Valkey 9.1.0 6 节点 cluster，验证 cluster 语义和 cleanup。

### 不做什么

- 不用 fake Valkey 满足 gate。
- 不使用 host network 作为默认路径。
- 不使用 host 端口映射/NAT 来证明 cluster 网络语义。
- 不修改 host 网络、防火墙、路由。
- 不只启动单节点。

### 必须真实验证什么

- Valkey 版本证据。
- 6 节点 cluster 创建。
- `cluster_state=ok`。
- 16384 slots 完整覆盖。
- primary/replica 与 planner 一致。
- primary/replica 位于不同 virtual AZ。
- sandbox 内 client 能读写跨 slot key。
- cleanup 无残留。

### 产物放哪里

```text
artifacts/runs/<run_id>/runtime/node_manifest.json
artifacts/runs/<run_id>/runtime/container_manifest.json
artifacts/runs/<run_id>/evidence/valkey_version.txt
artifacts/runs/<run_id>/evidence/cluster_info.txt
artifacts/runs/<run_id>/evidence/cluster_nodes.txt
artifacts/runs/<run_id>/gate_results/P03_real_valkey_cluster.json
audits/P03.md
```

### 失败怎么处理

版本不符、cluster state 非 OK、slot 不完整、主备/AZ 不一致、cleanup 失败均为 phase FAIL。发现 host 网络副作用则 `SAFETY_BLOCKED`。

### 状态如何记录

记录 run_id、镜像 digest 或 source tag、节点数、slot coverage、cleanup result、真实 gate 证据路径。

### 下一步如何判断

P03 PASS 后进入 P04。进入条件是：真实小集群可以重复创建、验证、销毁。

---

## P04 — 生命周期管理与 Cleanup 严格化

### 做什么

完善 start/status/stop/restart/destroy/cleanup/orphan detection。所有资源必须由 run_id 管理，包括容器、网络、目录、端口、PID、日志、artifact。

### 不做什么

- 不允许无 run_id 资源。
- 不允许共享不可追踪目录。
- 不允许 cleanup 失败后 PASS。
- 不允许端口/PID/目录混乱。

### 必须真实验证什么

真实 6 节点 cluster 上验证：start、status、stop、restart、destroy、重复 cleanup、异常中断 cleanup、orphan detection。

### 产物放哪里

```text
artifacts/runs/<run_id>/lifecycle/lifecycle_events.jsonl
artifacts/runs/<run_id>/lifecycle/resource_ledger.json
artifacts/runs/<run_id>/lifecycle/cleanup_result.json
artifacts/runs/<run_id>/gate_results/P04_lifecycle.json
audits/P04.md
```

### 失败怎么处理

发现 orphan、cleanup 不可重入、资源 ledger 不完整、stop/destroy 状态不一致时，phase FAIL。

### 状态如何记录

记录 lifecycle gate run_id、cleanup 残留数、已修复泄漏、风险项。

### 下一步如何判断

P04 PASS 后进入 P05。进入条件是：后续 workload 与 fault gate 可以安全启动与清理真实集群。

---

## P05 — Workload 与基础观测

### 做什么

实现 workload 模型与基础观测。支持读写比例、均匀 QPS、热点 QPS、pipeline、连接数、负载时机。采集客户端指标、Valkey cluster 状态、资源快照、事件流。

### 不做什么

- 不只输出人类文本。
- 不忽略客户端错误。
- 不把 fake workload 当真实 workload。
- 不在指标缺失时静默 PASS。

### 必须真实验证什么

真实 Valkey cluster 上验证：均匀 QPS、热点 QPS、读写混合、pipeline、至少一种负载时机、metrics artifact 完整性。

### 产物放哪里

```text
artifacts/runs/<run_id>/workload/workload_plan.json
artifacts/runs/<run_id>/workload/workload_events.jsonl
artifacts/runs/<run_id>/metrics/client_metrics.jsonl
artifacts/runs/<run_id>/metrics/cluster_samples.jsonl
artifacts/runs/<run_id>/gate_results/P05_workload_observability.json
audits/P05.md
```

### 失败怎么处理

workload profile 无法回溯、客户端错误未记录、指标缺失未标记、cleanup 被 workload 破坏，均为 phase FAIL。

### 状态如何记录

记录已验证 workload profile、指标覆盖率、缺失字段、真实 gate artifact。

### 下一步如何判断

P05 PASS 后进入 P06。进入条件是：管理操作可以在有/无 workload 下被测量。

---

## P06 — 管理操作测试矩阵 MVP

### 做什么

实现管理操作矩阵 MVP：cluster create/check、add/remove node、add/remove replica、reshard/rebalance、manual failover、rolling restart、recover。每个操作记录耗时、成功率、cluster convergence、slot consistency、client impact。

### 不做什么

- 不把单个 happy path 当完整矩阵。
- 不跳过真实 Valkey gate。
- 不在操作失败时产出 PASS。
- 不隐藏未覆盖矩阵项。

### 必须真实验证什么

真实 Valkey 上至少验证：一个 reshard、一个 replica 变更、一个节点移除或恢复、一次 manual failover 或等价受控接管、至少一次有 workload 的管理操作。

### 产物放哪里

```text
artifacts/runs/<run_id>/operations/operation_matrix.json
artifacts/runs/<run_id>/operations/operation_results.jsonl
artifacts/runs/<run_id>/analysis/management_performance.json
artifacts/runs/<run_id>/gate_results/P06_management_matrix.json
audits/P06.md
```

### 失败怎么处理

操作失败、cluster convergence 超时、slot mismatch、mandatory 指标缺失，均不允许进入 P07。

### 状态如何记录

记录已覆盖操作、未覆盖操作、失败操作、修复记录、矩阵缺口。

### 下一步如何判断

P06 PASS 后进入 P07。进入条件是：fault 注入可以复用管理操作、workload、observability。

---

## P07 — Sandbox 故障注入底座

### 做什么

实现故障注入底座，覆盖 node process、node network、AZ network、flap、delay、loss、partition candidate。每个 fault 有 plan、inject、verify active、recover、verify clean、analyze 生命周期。

### 不做什么

- 不改 host 网络。
- 不使用 host interface 操作。
- 不影响非项目资源。
- 不把“命令返回 0”当作故障生效证明。
- 不跳过 cleanup verification。

### 必须真实验证什么

真实 Valkey 上至少验证：单节点进程故障、单节点网络隔离或等价 sandbox 隔离、virtual AZ 间断开/延迟/丢包中的至少一种、故障恢复、host safety audit。

### 产物放哪里

```text
artifacts/runs/<run_id>/faults/fault_plan.json
artifacts/runs/<run_id>/faults/fault_events.jsonl
artifacts/runs/<run_id>/faults/fault_effects.json
artifacts/runs/<run_id>/safety/host_network_audit.json
artifacts/runs/<run_id>/gate_results/P07_fault_injection.json
audits/P07.md
```

### 失败怎么处理

故障未生效、作用域越界、恢复失败、cleanup 失败、host safety audit 失败，均不允许 PASS。

### 状态如何记录

记录每类 fault 的验证状态、sandbox backend、隔离证据、未验证故障类型与风险。

### 下一步如何判断

P07 PASS 后进入 P08。进入条件是：failover/脑裂测试能依赖 fault event 生成可审计时间线。

---

## P08 — Failover、脑裂、恢复效能分析

### 做什么

实现 failover 和 split-brain 分析。量化故障注入到检测、检测到晋升、晋升到 slot 恢复、客户端错误窗口、RTO/RPO 近似、dual-primary/view divergence 指标。

### 不做什么

- 不只看最终恢复成功。
- 不编造 RTO/RPO。
- 不在证据不足时声称发生脑裂。
- 不把 minority/majority 视角混在一起。

### 必须真实验证什么

真实 Valkey 上至少验证：primary 故障触发接管、primary 网络隔离场景、virtual AZ partition candidate、workload 全程运行下 failover 影响、恢复后 cluster convergence。

### 产物放哪里

```text
artifacts/runs/<run_id>/failover/failover_timeline.json
artifacts/runs/<run_id>/failover/split_brain_analysis.json
artifacts/runs/<run_id>/analysis/failover_efficiency.json
artifacts/runs/<run_id>/gate_results/P08_failover_split_brain.json
audits/P08.md
```

### 失败怎么处理

时间线无法对齐、failover 证据缺失、脑裂结论无证据、workload 数据缺失且为 mandatory 场景，均为 phase FAIL。

### 状态如何记录

记录场景覆盖、指标完整性、raw event 引用、无法判定指标与原因。

### 下一步如何判断

P08 PASS 后进入 P09。进入条件是：稳定性测试可以复用 failover/fault/workload/analysis。

---

## P09 — 稳定性、Soak、Invariant Checker

### 做什么

实现稳定性测试与 invariant checker：cluster state、slot coverage、primary/replica、资源漂移、错误率、latency、reconnect、event completeness、cleanup residue。

### 不做什么

- 不把短启动测试当稳定性测试。
- 不忽略资源泄漏。
- 不只看最终状态。
- 不默认跑超长 soak；长 soak 可 opt-in，但必须有最小真实 stability gate。

### 必须真实验证什么

真实 Valkey 上至少验证：最小 stability run、持续 workload、周期 cluster sampling、invariant checker、结束后 cleanup 零残留。

### 产物放哪里

```text
artifacts/runs/<run_id>/stability/stability_plan.json
artifacts/runs/<run_id>/stability/invariant_results.jsonl
artifacts/runs/<run_id>/stability/resource_drift.json
artifacts/runs/<run_id>/analysis/stability_summary.json
artifacts/runs/<run_id>/gate_results/P09_stability.json
audits/P09.md
```

### 失败怎么处理

invariant violation、资源泄漏、mandatory 指标中断、cleanup 残留，均不允许 PASS。

### 状态如何记录

记录 run 时长、节点数、workload、invariant 结果、资源漂移、失败与修复。

### 下一步如何判断

P09 PASS 后进入 P10。进入条件是：单机 runtime 与分析链路足够稳定，可扩展到多机调度。

---

## P10 — 多机调度能力

### 做什么

提供多 Mac、多 Linux 调度能力。控制机基于 host 配置对其他机器进行拉起、注入、停止、artifact 汇聚。必须复用 placement、runtime、fault、cleanup、artifact schema。

### 不做什么

- 不假设远端机器存在。
- 不把本地 mock remote 称为真实多机 ready。
- 不在远端修改全局网络。
- 不留下远端残留资源。
- 不让 artifact 分散在远端无法汇总。

### 必须真实验证什么

分两层：

1. mandatory local scheduler gate：在单机上用真实 sandbox runtime 验证调度抽象、host manifest、artifact 汇聚、cleanup。
2. real multi-host gate：当至少两台真实 host 可配置时，验证跨 host 拉起、状态检查、停止、artifact 汇聚与真实 Valkey gate。

未通过 real multi-host gate 时，不得声明多机 ready，只能记录 `BLOCKED_ENV` 或 capability-level `SKIPPED_WITH_REASON`。P10 必须区分三种状态：`local_path_completion`（本地调度抽象已验证）、`multi_host_capability_planned`（多机能力已设计但未真实验证）、`multi_host_real_gate_passed`（真实多机 gate 通过）。只有第三种状态才能写入 multi-host ready。

### 产物放哪里

```text
artifacts/runs/<run_id>/scheduler/host_manifest.json
artifacts/runs/<run_id>/scheduler/dispatch_plan.json
artifacts/runs/<run_id>/scheduler/remote_results.jsonl
artifacts/runs/<run_id>/scheduler/artifact_collection.json
artifacts/runs/<run_id>/gate_results/P10_scheduler.json
audits/P10.md
```

### 失败怎么处理

远端不可达记录 `BLOCKED_ENV`；远端 cleanup 失败、artifact 未汇总、host safety audit 失败，phase FAIL 或 `SAFETY_BLOCKED`。

### 状态如何记录

记录 host 数、OS/arch、调度 backend、远端 gate 状态、`local_path_completion`、`multi_host_capability_planned`、`multi_host_real_gate_passed`、未验证能力、阻塞原因。

### 下一步如何判断

P10 在默认 local-only 主路径下可以只以 `local_path_completion=PASS` 继续；此时必须写 `multi_host_real_gate_passed=false` 与 capability-level `SKIPPED_WITH_REASON`，最终报告不得声明 multi-host ready。只有存在真实多机配置与真实多机 gate evidence 时，才能把 `multi_host_real_gate_passed=true` 并声明 multi-host ready。

---

## P11 — 分析、图表、报告、Artifact 回归

### 做什么

实现完整分析与展示。所有表格、图表、曲线、报告均从 artifact 生成。建立 artifact regression baseline，验证 schema、字段、指标、分析结果变化。

### 不做什么

- 不手工填图表数据。
- 不隐藏 `MISSING`。
- 不把报告 PASS 当测试 PASS。
- 不让图表绕过 machine-readable artifact。

### 必须真实验证什么

基于真实 Valkey run artifact 验证 management performance、failover、stability、missing metric 标注、图表生成、baseline regression。

### 产物放哪里

```text
artifacts/runs/<run_id>/analysis/*.json
artifacts/runs/<run_id>/reports/report.md
artifacts/runs/<run_id>/reports/tables/*.csv
artifacts/runs/<run_id>/reports/charts/*
artifacts/baselines/<baseline_id>/manifest.json
artifacts/runs/<run_id>/gate_results/P11_analysis_report.json
audits/P11.md
```

### 失败怎么处理

报告指标无法回溯 source artifact、baseline 无法发现破坏性变化、缺失指标未标注，phase FAIL。

### 状态如何记录

记录 baseline id、report run_id、分析覆盖范围、缺失指标、图表清单。

### 下一步如何判断

P11 PASS 后进入 P12。进入条件是：scale ladder 的真实 run 可以自动产出完整分析与报告。

---

## P12 — Scale Ladder：10/30/50/100 节点真实 Gate

### 做什么

执行真实 10、30、50、100 节点阶梯 gate。每一级包含资源预检、placement、cluster create、workload smoke、metrics、至少一个管理操作或状态验证、analysis、cleanup。

### 不做什么

- 不默认运行 1000。
- 不跳过资源预检。
- 不以小规模 gate 替代大规模 gate。
- 不在资源不足时静默降级 PASS。
- 不让 scale run 缺少 cleanup。

### 必须真实验证什么

- 10 节点真实 gate。
- 30 节点真实 gate。
- 50 节点真实 gate。
- 100 节点真实 gate。
- 每级 artifact schema 校验。
- 每级 cleanup 零残留。
- 默认路径没有运行 1000 节点。

### 产物放哪里

```text
artifacts/runs/<run_id>/scale/scale_level.json
artifacts/runs/<run_id>/scale/resource_preflight.json
artifacts/runs/<run_id>/scale/scale_summary.json
artifacts/runs/<run_id>/gate_results/P12_scale_<N>.json
artifacts/runs/<run_id>/reports/scale_report.md
audits/P12.md
```

### 失败怎么处理

资源不足记录 `BLOCKED_RESOURCE`，不能 PASS；任一级真实 gate 失败则 P12 不 PASS；cleanup 残留则该级 gate FAIL。

### 状态如何记录

记录每一级 run_id、节点数、资源预检、cluster status、workload smoke、analysis、cleanup、阻塞原因。

### 下一步如何判断

P12 PASS 后进入 P13。进入条件是：默认安全上限 100 内的 scale 能力有真实证据。

---

## P13 — 1000 节点 Opt-in Profile 与最终 Release Audit

### 做什么

实现 1000 节点 opt-in profile 的资源检查、配置校验、placement、dry-run、artifact、风险报告。最终做 release audit，确认所有 phase、gate、artifact、state、safety、report 一致。

### 不做什么

- 不默认真实运行 1000 节点。
- 不让 CI/普通 loop 触发 1000 执行。
- 不把 1000 dry-run 当真实性能结果。
- 不跳过最终 audit。

### 必须真实验证什么

默认必须验证：

- 1000 未显式 opt-in 时被拒绝。
- 1000 opt-in dry-run 生成完整 plan 与资源估算。
- 默认 make/loop/CI 不会执行 1000 真实节点。
- final audit 能索引 P03-P12 所有真实 evidence。

1000 真实执行不是默认要求；若用户显式开启，必须生成单独受控 run 与 audit。

### 产物放哪里

```text
artifacts/runs/<run_id>/scale_1000/dry_run_plan.json
artifacts/runs/<run_id>/scale_1000/resource_risk_report.json
artifacts/runs/<run_id>/gate_results/P13_1000_dry_run.json
audits/P13_final_release.md
```

### 失败怎么处理

任何默认路径可运行 1000、资源报告缺失、dry-run artifact 不完整、final audit 无法索引真实 evidence，均不允许 release PASS。

### 状态如何记录

记录 1000 profile 状态、dry-run run_id、风险、最终 release verdict、未验证项。

### 下一步如何判断

P13 PASS 表示项目在契约内完成。写入 `ALL_PHASES_PASS` 前必须执行最终一致性检查：P00-P13 mandatory gate result 均存在且 PASS、P03-P12 真实 Valkey evidence 可索引、artifact schema 通过、cleanup registry 无残留、final audit 能回溯所有关键 artifact。若有 `BLOCKED_ENV`、`BLOCKED_RESOURCE`、`SAFETY_BLOCKED` 或未验证多机/条件型规模能力，最终状态必须明确标注，不得伪装完成。
