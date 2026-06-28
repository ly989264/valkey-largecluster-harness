# Codex Bootstrap Prompt

你是本仓库的工程 agent。你的任务是按照 `docs/codex/` 下的契约文档，从当前 phase 开始继续开发 Valkey 9.1.0 超大集群测试项目。不要依赖聊天上下文；仓库状态机、gate result、artifact、cleanup evidence 与 audit 是唯一事实来源。

本 prompt 必须支持无人工输入连续恢复：wrapper 会反复调用 `codex exec`，每轮都从仓库状态机判断当前 phase。当前 phase PASS 后，你必须更新 `state/codex_state.json.current_phase` 到下一 phase；下一轮 wrapper 会自动继续。

## 1. 启动时必须先做

先读取并理解：

1. `docs/codex/00_CODEX_MASTER_CONTRACT.md`
2. `docs/codex/01_PHASES_AND_GATES.md`
3. `docs/codex/02_HARNESS_AND_AUDIT.md`
4. `docs/codex/03_ARTIFACT_SCHEMA_AND_METRICS.md`
5. `docs/codex/04_STATE_MACHINE_AND_MEMORY.md`
6. `docs/codex/05_RUN_CODEX_LOOP.md`
7. `docs/codex/RUNBOOK_STATE.md`
8. `docs/codex/PHASE_LEDGER.md`
9. `docs/codex/DECISION_LOG.md`
10. `docs/codex/RISK_REGISTER.md`
11. `docs/codex/ARTIFACT_INDEX.md`
12. `docs/codex/HANDOFF.md`
13. `state/codex_state.json`
14. `state/cleanup_registry.json`

如果当前仓库尚未完成 P00，P00 必须创建并校验上述状态文件。P00 之后若这些文件缺失或不可解析，不要凭聊天记忆重建后继续；必须先恢复状态、写失败 artifact，或写明确 `BLOCKED_*`。

然后检查仓库当前状态、已有 artifact、已有 audit、已有 gate result，决定当前 phase。

## 2. 不可违反规则

1. 不默认运行 1000 节点。
2. 不修改物理机全局网络、防火墙、路由、DNS 或接口状态。
3. 不默认使用 `sudo` 修改系统级网络。
4. 不使用 Docker host port mapping / NAT 来证明 Valkey Cluster 真实网络语义。
5. 不使用 fake test 冒充真实 Valkey gate。
6. 不在没有 artifact 的情况下标记 PASS。
7. 不启动没有 cleanup 注册的进程、容器、网络、目录、PID 文件。
8. 不编造报告指标；缺失写结构化 `MISSING`、`SKIPPED_WITH_REASON` 或 `BLOCKED_*`。
9. 不依赖本 prompt 或聊天记录记忆上次进度；必须读仓库状态机。
10. 不跳过 phase gate。
11. 不只做 skeleton 后停止。
12. 没有真实多机配置和真实多机运行证据时，不声明 multi-host ready。

## 3. 每轮只做当前 phase

根据 `state/codex_state.json`、`PHASE_LEDGER.md`、`RUNBOOK_STATE.md` 与 artifact 判断当前 phase。只推进当前 phase，不要越级实现后续 phase 的大量能力。可以预留接口，但不要以过细实现步骤替代 phase gate。

每个 phase 必须满足该 phase 的七项要求：

1. 做什么。
2. 不做什么。
3. 必须真实验证什么。
4. 产物放哪里。
5. 失败怎么处理。
6. 状态如何记录。
7. 下一步如何判断。

## 4. 每轮结束前必须三选一

每次 `codex exec` 结束前必须满足以下三种状态之一，不允许无状态退出：

1. 当前 phase PASS：`state/codex_state.json.expected_gate_results` 已列出本 phase mandatory gate；所有 mandatory gate result 均为 machine-readable JSON 且 `status=PASS`；artifact schema validation、cleanup result、audit 全部存在且一致；audit 使用固定格式并写 `Decision: PASS`；更新 `last_completed_phase`；把 `current_phase` 推进到下一 phase；更新 `RUNBOOK_STATE.md`、`PHASE_LEDGER.md`、`ARTIFACT_INDEX.md`、`state/codex_state.json`、`HANDOFF.md`。
2. 当前 phase FAIL：写 machine-readable gate result 或 failure artifact；记录失败原因、下一次修复动作、attempt/no-progress 状态；保持 `current_phase` 不变；不得进入下一 phase。
3. 当前 phase BLOCKED：写 `BLOCKED_ENV`、`BLOCKED_RESOURCE`、`SAFETY_BLOCKED` 或 `BLOCKED_PROGRESS`；必须记录 `blocker_type`、证据路径、影响范围、下一步人工处理点；不得把 blocked 当 PASS。

写 PASS 前必须先自检 wrapper 语义级 postcheck 所需字段：gate result 的 `schema_version`、`phase_id`、`run_id`、`gate_type`、`required`、`status`、时间字段、`evidence`、`artifacts`；audit 的 `Phase`、`Run ID`、`Decision`、`Gate Results`、`Artifact Evidence`、`Cleanup Evidence`、`Reasons`；cleanup 的 `artifacts/runs/<run_id>/cleanup/cleanup_result.json`；以及 `ARTIFACT_INDEX.md` 中的 run_id/gate/artifact 索引。如果缺字段、字段不一致、P03+ 真实 Valkey gate 缺少真实网络语义字段，必须写 FAIL 或 `BLOCKED_*`，不得写 PASS。

如果只是写了代码或说明，但没有 gate result、artifact、audit、状态更新，不算完成本轮。

## 5. 实施方式

对当前 phase：

1. 恢复状态。
2. 校验状态一致性。
3. 写入或更新 phase plan。
4. 实现该 phase 所需最小完整能力。
5. 运行该 phase 的 mandatory gate。
6. 生成 machine-readable artifact。
7. 运行 artifact schema validation。
8. 运行 safety/memory/cleanup gate。
9. 写 audit 文件。
10. 若失败，在同一 phase 修复或回滚，不进入下一 phase。
11. 若 PASS，更新所有状态文件并推进下一 phase。

自动主路径从 P00 一直推进到 P13。P00 PASS 后不能等待人工发送“继续”；必须把 `current_phase` 写为 P01，由 wrapper 下一轮自动恢复。P13 的 final audit 通过后，才允许写 `phase_status=ALL_PHASES_PASS`。

## 6. 真实 Valkey gate 规则

P00-P02 可以使用 fake 作为开发辅助，但不能声明项目可用。P03 开始，真实 Valkey gate 必须存在。P06 以后，每个新增能力必须有至少一个真实 Valkey e2e 证明。scale phase 必须支持真实 10/30/50/100 节点阶梯 gate。

如果 Docker、Valkey 镜像、远端 host 或资源不足，记录 `BLOCKED_ENV` 或 `BLOCKED_RESOURCE`，不要用 fake 代替真实 gate。

## 7. Artifact 规则

每个 gate 必须写 artifact。mandatory gate 还必须在 `state/codex_state.json.expected_gate_results` 中声明，且 gate result 能被 wrapper 解析。至少包含：

- run manifest；
- normalized config；
- plan；
- events；
- metrics 或结构化 missing；
- gate result；
- cleanup result；
- audit。

P03 及之后真实 Valkey gate 的 evidence 必须包含 `valkey_version`、`node_count`、`cluster_state`、`slot_coverage`、`client_port_reachability`、`cluster_bus_reachability`、`runtime_mode`、`uses_host_port_mapping=false`。若缺任一字段，或依赖 Docker host port mapping/NAT 证明 cluster 语义，不能写 PASS。

没有 artifact，不能 PASS。mandatory gate 的 gate result 必须是 machine-readable JSON。audit 只能基于 artifact、gate result、cleanup evidence 与状态机判定。

## 8. Safety 规则

所有 fault injection 都必须限制在 sandbox 内。默认 backend 是 Docker/container namespace 或 run-owned proxy/namespace。禁止 host-global 网络修改。任何可能影响物理机网络的实现都必须被 safety gate 拒绝。

## 9. No-progress 与 attempt 规则

每次进入同一 phase 的修复或 gate 尝试，必须更新 `phase_attempt` 或 ledger attempt。若本轮没有新增 gate result、artifact、audit、cleanup evidence、状态修复记录或代码变更摘要，必须递增 `no_progress_count`。

达到 `max_attempts_per_phase` 或 `max_no_progress_rounds` 后，不得静默无限重试。若最后原因是环境、资源或安全问题，写对应 `BLOCKED_ENV`、`BLOCKED_RESOURCE` 或 `SAFETY_BLOCKED`；否则写 `phase_status=BLOCKED_PROGRESS`、`blocked=true`、`blocker_type=NO_PROGRESS|MAX_ATTEMPTS_EXCEEDED`，并在 `HANDOFF.md` 中记录最后进展摘要、重复失败 gate、最新 artifact 路径与建议人工检查点。

## 10. 输出要求

你的最终消息应该简短说明：

- 当前 phase；
- 做了什么；
- 跑了哪些 gate；
- artifact 路径；
- phase 状态；
- 下一步状态。

不要把未验证能力说成已完成。不要用自然语言报告替代 artifact。
