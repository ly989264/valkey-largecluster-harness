# Codex 工程契约：Valkey 9.1.0 超大集群测试项目

本文件是 Codex 进入项目后的第一入口。Codex 必须先读取本文件，再读取同目录下所有 `0x_*.md` 文件，然后才能修改代码。本文不是普通需求说明，而是工程契约：phase、harness、artifact、状态机共同决定项目是否可以推进。

## 1. 项目目标

构建一个本地优先、可扩展到多机的 Valkey 9.1.0 集群测试项目，用于验证 Valkey 9.1.0 在超大集群场景下的集群管理性能、管理操作矩阵、故障接管效能、脑裂指标、稳定性、可观测性、数据分析与展示。

项目默认开发规模最大 100 个 Valkey 节点；1000 节点只属于 opt-in scale profile，用于资源检查、规划、dry-run 与受控执行，绝不能由普通 Codex loop 默认触发。

自动 loop 的默认主路径是 local-only：从 P00 开始，由 `scripts/run_codex_loop.sh` 反复调用 `codex exec`。Codex 每轮从仓库状态机恢复，只处理当前 phase；完成实现、mandatory gate、artifact、cleanup、audit 后，PASS 则自动把 `current_phase` 推进到下一 phase。多机能力必须通过配置显式开启；没有真实多机配置和真实多机 gate 证据时，只能记录 capability-level `SKIPPED_WITH_REASON` 或 `BLOCKED_ENV`，不能声明 multi-host ready。

每次真实运行必须产出 machine-readable artifact。图表、表格、曲线图只是 artifact 的展示层，不能成为唯一事实来源。

## 2. 不可违反边界

以下规则优先级高于所有实现便利性。

1. 不允许默认运行 1000 节点。
2. 不允许修改物理机全局网络配置。
3. 不允许修改物理机全局防火墙规则。
4. 不允许 kill、down、reset 物理机网络接口。
5. 不允许默认使用 `sudo` 修改系统级网络、路由、防火墙。
6. 不允许把 host network 当成默认 runtime。
7. 不允许把 Docker 端口映射/NAT 当成真实 Valkey Cluster 网络语义 gate。
8. 不允许 fake test 冒充真实 Valkey gate。
9. 不允许没有 artifact 的 PASS。
10. 不允许没有清理逻辑的进程、容器、端口、目录、PID 文件。
11. 不允许端口、目录、PID、container name、node id 混乱或不可追踪。
12. 不允许报告中编造指标；缺失必须结构化标记为 `MISSING`、`SKIPPED_WITH_REASON`、`BLOCKED_ENV`、`BLOCKED_RESOURCE`、`SAFETY_BLOCKED` 或 `BLOCKED_PROGRESS`，不能用 `0`、空表或含糊自然语言代替。
13. 不允许 Codex 只完成 skeleton/P00 后停止。
14. 不允许 Codex 依赖聊天上下文记忆推进；必须依赖仓库状态机与 harness。
15. 不允许把 `BLOCKED_*` 当成 PASS。
16. 没有真实多机配置和真实多机运行证据时，不允许声明 `multi-host ready`。

## 3. 基本术语

### 3.1 local

local 表示非云端环境，可以是单机 Mac、N 台 Mac、单机 Linux、N 台 Linux。

### 3.2 physical host

physical host 是真实机器。故障注入不得影响 physical host 的正常网络、进程与其他服务。

### 3.3 Valkey node

一个 Valkey server 实例。默认要求每个 Valkey node 拥有独立网络身份，不能只靠同一 host 上不同 localhost 端口来假装真实集群网络。

### 3.4 virtual AZ

virtual AZ 是项目内部的逻辑可用区标签。它用于 placement、故障注入、分析维度和报告聚合，不是云厂商真实 AZ。

### 3.5 real Valkey gate

real Valkey gate 是使用真实 Valkey 9.1.0 server 完成的端到端验证。它必须记录 Valkey 版本、node count、cluster state、slot coverage、artifact 路径、清理结果和 gate status。

### 3.6 fake

fake 包括 fake Valkey、mock runtime、mock scheduler、mock fault injector、mock metrics。fake 可用于 P00-P02 与单元测试，但不能满足 P03 之后真实能力的 PASS。

## 4. 默认架构边界

默认 runtime 必须采用 sandbox 方案：Mac 优先 Docker/container namespace，Linux 也优先 Docker/container namespace。每个 Valkey node 在 sandbox 内拥有独立网络身份，故障注入只作用于 Valkey 节点、run-owned proxy/namespace 或 run-owned container。

```text
+---------------- physical host ----------------+
|                                                |
|  Codex / control process                       |
|        |                                       |
|        v                                       |
|  +------------- Docker sandbox -------------+  |
|  |                                           |  |
|  |  +---------+   +---------+   +---------+  |  |
|  |  | node-1  |   | node-2  |   | client  |  |  |
|  |  | netns   |<->| netns   |<->| driver  |  |  |
|  |  +---------+   +---------+   +---------+  |  |
|  |       ^             ^                     |  |
|  |       | container-only fault scope        |  |
|  +-------|-------------|---------------------+  |
|          |             |                        |
|      host network must remain unchanged         |
+------------------------------------------------+
```

允许 Codex 选择具体 sandbox backend，但必须满足：

- default path 不修改 host 网络；
- fault executor 能证明作用域；
- cleanup 可验证；
- artifact 能记录 backend、权限、资源、故障生效证据。

## 5. virtual AZ placement 规则

1. 单 virtual AZ：所有节点在同一 AZ，不注入 AZ 级网络问题。
2. 多 virtual AZ：每台 physical host 上都可以拥有所有 virtual AZ，节点均匀落入各 AZ。
3. 每个分片的 primary 与 replica 必须位于不同 virtual AZ。
4. 例：`1 primary + 1 replica`，`az_count=3` 时，一个分片只能覆盖 2 个 AZ，不能强行覆盖 3 个 AZ。
5. 多分片整体应在 AZ 间均衡，单分片则遵守主备 anti-affinity。
6. planner 必须输出并验证 host/AZ/role/shard/node 映射。

## 6. 必须覆盖的能力

项目最终必须覆盖以下能力层：

1. 配置 schema 与配置归一化。
2. physical host 与 virtual AZ placement planner。
3. 资源预检、规模限制、dry-run。
4. Docker/container namespace runtime。
5. 真实 Valkey Cluster bootstrap、status、stop、cleanup。
6. 管理操作：create、check、add/remove node、add/remove replica、reshard、rebalance、manual failover、rolling restart、recover。
7. workload：读写比例、均匀 QPS、热点 QPS、pipeline、连接数、负载时机。
8. 故障注入：node process、node network、AZ network、AZ down、flap、delay、loss、partition candidate。
9. failover 效能分析：检测、晋升、恢复、client error window、RTO/RPO 近似、slot coverage。
10. split-brain 指标分析：dual-primary、view divergence、minority write acceptance、epoch/slot 冲突。
11. 稳定性：soak、资源漂移、错误率、latency、cluster state flap、cleanup residue。
12. artifact-first 分析与展示：JSON/JSONL/CSV/Parquet 优先，图表只从 artifact 生成。
13. harness：unit、contract、property、fake integration、Docker smoke、real Valkey e2e、scale ladder、artifact regression、safety scan、audit。

## 7. phase 策略

| 阶段 | fake-only 是否允许 | 真实 Valkey 要求 |
|---|---:|---|
| P00-P02 | 允许 fake，但不能声明项目可用 | 不要求真实 Valkey |
| P03-P05 | 不允许 fake-only | 必须引入真实 Valkey gate |
| P06 以后 | 不允许 fake-only | 每个新增能力至少一个真实 Valkey e2e 证明 |
| scale 阶段 | 不允许 fake-only | 必须真实 10/30/50/100 节点阶梯 gate |
| 1000 profile | 不默认执行 | opt-in、资源检查、dry-run、受控执行 |

## 8. 通过标准

整个项目完成必须同时满足：

1. 所有 phase 的 mandatory gate 通过。
2. 每个 mandatory gate 都有 machine-readable gate result，且 gate result 被 `ARTIFACT_INDEX.md` 索引。
3. 每个 phase 都有 `audits/Pxx.md`，audit 只能基于 artifact、gate result 和状态机判定，不能基于 Codex 自然语言总结判定。
4. P03 之后的能力都有真实 Valkey 证据。
5. 10/30/50/100 scale ladder 都有真实 gate artifact；若资源不足，只能记录 blocker，不能 PASS。
6. 1000 节点 profile 默认只 dry-run；没有默认真实运行路径。
7. artifact schema 校验全部通过。
8. safety scan 全部通过。
9. cleanup gate 全部通过。
10. `docs/codex/` 与 `state/` 中的状态机文件能恢复项目进度。
11. 报告中的所有数字均能回溯 artifact；缺失数据必须结构化标记为 `MISSING`、`SKIPPED_WITH_REASON` 或 `BLOCKED_*`。

`ALL_PHASES_PASS` 只能在所有 mandatory local gates、P03 之后真实 Valkey gates、artifact schema gate、cleanup gate、audit gate、final release audit 全部通过后写入。若多机或条件型大规模能力未被当前环境真实验证，最终报告必须显式标注 `multi_host_status`、`scale_status` 与对应 `SKIPPED_WITH_REASON` 或 `BLOCKED_*`，不得把未验证能力写成 ready。

### 8.1 Strong harness 最低标准

本项目中的 strong harness 不是“文档写了 gate”，而是证据链可以被机器和 audit 双重校验。最低标准为：

1. 每个 phase 在 `state/codex_state.json.expected_gate_results` 中声明 mandatory gate。
2. 每个 mandatory gate 都有 machine-readable gate result JSON，且能被 wrapper 解析。
3. wrapper 必须做语义级 postcheck：gate schema、phase_id、run_id、gate_type、status、时间字段、evidence/artifact 引用、cleanup evidence、audit decision 必须一致。
4. audit 必须明确 `Decision: PASS`，且引用当前 run_id、gate result、artifact 与 cleanup evidence。
5. P03 之后真实 Valkey gate 必须包含真实 Valkey 网络语义证据；fake、Docker host port mapping/NAT 或空 artifact 不能满足真实 gate。
6. cleanup result 必须存在并通过；cleanup registry 不能有未解释 active resource。
7. `ALL_PHASES_PASS` 必须通过 final release postcheck：P00-P13 ledger PASS、对应 audit/gate/artifact/cleanup 证据完整。

缺少以上任一项，不能称为 phase 完成或项目完成。

## 9. Codex 执行原则

Codex 不应被要求逐行照做具体实现步骤。Codex 的自由度在实现层，约束在契约层：每个 phase 必须交付规定能力、通过规定 gate、产出规定 artifact、记录规定状态。

Codex 每轮都必须从仓库状态机恢复上下文：读取 phase ledger、runbook state、decision log、risk register、artifact manifest，再判断当前 phase。聊天上下文只能辅助，不能作为事实来源。

每次 `codex exec` 结束前必须满足三选一：当前 phase PASS 并把 `state/codex_state.json.current_phase` 推进到下一 phase；当前 phase FAIL 并写入 gate result、failure artifact 与下一次修复动作；当前 phase `BLOCKED_*`/`SAFETY_BLOCKED`/`BLOCKED_PROGRESS` 并写入 blocker。不得无状态退出，不得只写说明或 skeleton 后停止。
