# 仓库状态机与长期 Loop 记忆契约

本项目的长期 loop 不能依赖 Codex 的聊天上下文。Codex 每轮必须通过仓库内状态机、artifact、gate result 与 audit 恢复上下文，再执行当前 phase。

## 1. 为什么需要状态机

Codex 的上下文窗口可能变化，长时间开发会跨多轮会话。所有关键事实必须落在仓库文件和 artifact 中：当前 phase、已通过 gate、失败原因、风险、决策、artifact、下一步。

```text
+---------------- chat context ----------------+
| temporary, lossy, not source of truth         |
+--------------------+-------------------------+
                     |
                     v
+---------------- repository state ----------------+
| RUNBOOK_STATE / PHASE_LEDGER / artifacts / audit |
| canonical, resumable, reviewable                 |
+--------------------------------------------------+
```

## 2. 必须维护的状态文件

```text
docs/codex/
  RUNBOOK_STATE.md
  PHASE_LEDGER.md
  DECISION_LOG.md
  RISK_REGISTER.md
  ARTIFACT_INDEX.md
  HANDOFF.md
state/
  codex_state.json
  latest_run.json
  cleanup_registry.json
  gate_index.json
```

### 2.1 RUNBOOK_STATE.md

人类可读的当前状态。必须包含：

```markdown
# RUNBOOK_STATE

## Current phase
Pxx - name

## Phase status
IN_PROGRESS | PASS | FAIL | BLOCKED_*

## Last completed phase
Pxx

## Active objective
...

## Last gate results
| gate | status | artifact |

## Current blockers
...

## Next action
...

## Safety notes
...

## Artifact references
...
```

### 2.2 PHASE_LEDGER.md

phase 账本，必须追加记录，不依赖聊天。

```markdown
| time | phase | attempt | status | run_id | gates | audit | notes |
|---|---|---:|---|---|---|---|---|
```

修正历史记录时，不直接删除原记录；追加 correction entry。

### 2.3 DECISION_LOG.md

记录工程决策：

```markdown
## D-0001: decision title
- Date:
- Phase:
- Decision:
- Alternatives:
- Reason:
- Consequences:
- Revisit trigger:
```

任何改变安全边界、artifact schema、phase gate、runtime backend、scale policy 的行为都必须写入 decision log。

### 2.4 RISK_REGISTER.md

记录风险：

```markdown
| risk_id | phase | risk | severity | mitigation | status | owner |
|---|---|---|---|---|---|---|
```

风险不能只写在聊天中。

### 2.5 ARTIFACT_INDEX.md

索引所有重要 artifact：

```markdown
| run_id | phase | artifact | schema | status | hash | notes |
|---|---|---|---|---|---|---|
```

### 2.6 HANDOFF.md

这是 Codex 每轮结束前必须更新的短上下文，用于下一轮快速恢复：

```markdown
# HANDOFF

## Must read first
- 00_CODEX_MASTER_CONTRACT.md
- RUNBOOK_STATE.md
- PHASE_LEDGER.md

## Current exact state
...

## Last commands/gates
...

## Known failures
...

## Next safe action
...
```

### 2.7 codex_state.json

机器可读状态，至少包含：

```json
{
  "schema_version": "codex_state.v1",
  "current_phase": "Pxx",
  "phase_status": "IN_PROGRESS",
  "last_completed_phase": "Pxx",
  "active_run_id": "...",
  "last_completed_run_id": "...",
  "last_gate_status": "PASS|FAIL|...",
  "expected_audit": "audits/Pxx.md",
  "expected_gate_results": {
    "Pxx": [
      {
        "gate_id": "Pxx.required_gate_name",
        "gate_type": "SCHEMA_CONTRACT|REAL_VALKEY_E2E|...",
        "required": true,
        "path": "artifacts/runs/<run_id>/gate_results/<gate>.json"
      }
    ]
  },
  "last_completed_gate_results": [],
  "phase_attempt": 1,
  "max_attempts_per_phase": 8,
  "no_progress_count": 0,
  "max_no_progress_rounds": 3,
  "last_progress_at": "...",
  "last_progress_summary": "...",
  "progress_fingerprint": "hash-of-phase-run-gates-artifacts-audit",
  "blocked": false,
  "blocker_type": null,
  "blocker_reason": null,
  "next_action": "...",
  "updated_at": "..."
}
```

`expected_gate_results` 是 wrapper 语义 postcheck 的输入，不是普通说明文字。它必须列出每个 phase 的 mandatory gate；每个 gate 至少包含 `gate_id`、`gate_type`、`required=true`，在 gate 执行后必须包含或可解析到 gate result `path`。phase 处于 PASS 推进状态时，Codex 必须把已完成 phase 的 gate 快照写入 `last_completed_gate_results`，并保留 `expected_gate_results` 供 final release postcheck 校验 P00-P13。

P03 及之后的真实 Valkey gate 在 `expected_gate_results` 中必须声明为 `REAL_VALKEY_E2E`、`REAL_VALKEY_FAULT` 或 `REAL_VALKEY_SCALE` 中的合适类型；fake gate 不能作为 mandatory real gate。

`phase_status` 是主状态。attempt/no-progress 字段只用于自动 loop 防止无限重试，不构成另一套状态系统。达到阈值后必须写入 `blocked=true` 和最准确的 `phase_status`：`BLOCKED_ENV`、`BLOCKED_RESOURCE` 或 `SAFETY_BLOCKED`；若只是实现无法收敛，保持当前 phase 并写 `phase_status=BLOCKED_PROGRESS`、`blocker_type=NO_PROGRESS|MAX_ATTEMPTS_EXCEEDED`、`blocker_reason` 与 `next_action`。

### 2.8 P00 首轮初始化闭环

P00 不能只写“若不存在则创建”。当 `state/codex_state.json` 或任一必需状态文件不存在时，Codex 只能执行 P00 bootstrap，不能跳到 P01 或后续 phase。

P00 必须创建并校验：

```text
docs/codex/RUNBOOK_STATE.md
docs/codex/PHASE_LEDGER.md
docs/codex/DECISION_LOG.md
docs/codex/RISK_REGISTER.md
docs/codex/ARTIFACT_INDEX.md
docs/codex/HANDOFF.md
state/codex_state.json
state/cleanup_registry.json
```

若项目同时维护 `state/latest_run.json` 或 `state/gate_index.json`，P00 也必须初始化为空索引或有效 JSON。P00 PASS 前，`codex_state.json.current_phase` 必须被推进为 `P01`，`last_completed_phase` 必须为 `P00`，并且 `PHASE_LEDGER.md`、`ARTIFACT_INDEX.md`、`audits/P00.md` 引用同一个 P00 run_id。

## 3. Codex 每轮启动恢复流程

每轮 Codex 开始必须执行以下逻辑：

```text
read master contract
  -> read phase contract
  -> read harness contract
  -> read artifact contract
  -> read RUNBOOK_STATE
  -> read PHASE_LEDGER
  -> read codex_state.json
  -> inspect latest artifacts and audits
  -> compare phase/run_id/audit/gate/artifact index consistency
  -> decide current phase
  -> run state consistency check
  -> continue only current phase
```

不得基于聊天中“我记得上次做到哪里”直接继续。

## 4. 每个 phase 的状态更新点

Codex 必须在以下时刻更新状态文件：

1. phase 开始；
2. 生成 phase plan；
3. 实现完成准备跑 gate；
4. 每次 gate 失败；
5. 每次 gate 通过；
6. 发生 safety blocker；
7. 发生 resource/env blocker；
8. phase audit 完成；
9. 进入下一 phase 前。

每次 `codex exec` 结束前必须满足三选一：当前 phase PASS 并推进下一 phase；当前 phase FAIL 并记录下一次修复动作；当前 phase BLOCKED 并写 blocker。无状态退出是 loop failure。

## 5. 状态一致性 gate

`MEMORY_STATE` gate 必须检查：

1. `codex_state.json.current_phase` 与 `RUNBOOK_STATE.md` 一致。
2. `PHASE_LEDGER.md` 最新记录与当前 phase 一致。
3. `ARTIFACT_INDEX.md` 包含最新 run_id。
4. `HANDOFF.md` 包含 next action。
5. phase PASS 时 audit 文件存在。
6. phase PASS 时 gate result artifact 存在。
7. `cleanup_registry.json` 无未解释残留。
8. `codex_state.json.active_run_id`、最新 ledger run_id、audit 引用 run_id、gate result run_id 一致，除非当前 phase 尚未创建 run，此时必须写明 reason。
9. `progress_fingerprint` 反映的 gate/artifact/audit/cleanup 集合相对上一轮有变化；若无变化，必须递增 `no_progress_count` 或 `loop_control.consecutive_no_progress`。
10. `expected_gate_results` 中当前或刚完成 phase 的 mandatory gate 都能解析到 gate result；若 phase 已 PASS，则这些 gate result 必须全部 `status=PASS`。
11. audit 文件必须使用固定格式，且 `Decision` 与 gate result 状态一致。

状态不一致时不得进入下一 phase。progress fingerprint 必须至少纳入：`current_phase`、`last_completed_phase`、`run_id`、`expected_gate_results` 的状态集合、audit decision、`ARTIFACT_INDEX.md` tail hash、cleanup result hash。仅修改自然语言总结、重写空 artifact 或移动无效路径，不算有效进展。

## 6. 失败恢复协议

### 6.1 Gate 失败

写入：

- gate result；
- failure summary；
- RUNBOOK_STATE 当前 blocker；
- PHASE_LEDGER attempt；
- HANDOFF next safe action。

然后修复当前 phase，不进入下一 phase。每次修复尝试必须递增 `phase_attempt` 或追加 ledger attempt。

### 6.2 Safety blocker

写入 `SAFETY_BLOCKED`，记录触发命令、触发文件、潜在影响。修复前不得继续实现新能力。

### 6.3 Resource blocker

写入 `BLOCKED_RESOURCE`，记录请求规模、资源估算、实际资源、建议动作。不得静默降级并 PASS。

### 6.4 Environment blocker

写入 `BLOCKED_ENV`，记录缺少 Docker、镜像、远端 host、权限或网络条件。不得用 fake 替代 real gate。

### 6.5 No-progress / max-attempt blocker

同一 phase 的自动循环必须受限：

1. `phase_attempt > max_attempts_per_phase` 时，Codex 必须停止继续猜测式修复，写入 `BLOCKED_ENV`、`BLOCKED_RESOURCE` 或 `SAFETY_BLOCKED` 中最准确的状态；若无法归类，写 `phase_status=BLOCKED_PROGRESS`、`blocked=true`、`blocker_type=MAX_ATTEMPTS_EXCEEDED`，并说明需要人工诊断。
2. `no_progress_count >= max_no_progress_rounds` 或 `loop_control.consecutive_no_progress >= loop_control.max_consecutive_no_progress` 时，必须写入 `phase_status=BLOCKED_PROGRESS`，并在 `HANDOFF.md` 中记录最后进展摘要、重复失败 gate、最新 artifact 路径和建议人工检查点。
3. no-progress 的判定依据是 machine-readable 事实是否变化：expected gate 状态变化、真实 gate result 新增或从 FAIL 变 PASS、artifact schema 通过、测试通过项增加、audit decision 更新、cleanup result hash 变化、cleanup 残留减少、明确 blocker 写入都算进展；只修改说明文字、改 README/报告措辞、重写空 artifact 不算进展。

## 7. 上下文压缩规则

当 Codex 认为上下文过长时，不能只在聊天里总结。必须更新：

1. `HANDOFF.md`：短摘要。
2. `RUNBOOK_STATE.md`：当前状态。
3. `PHASE_LEDGER.md`：阶段事件。
4. `RISK_REGISTER.md`：风险。
5. `ARTIFACT_INDEX.md`：证据索引。

下一轮恢复时，以这些文件为准。

## 8. 决策不可丢失规则

以下内容必须写入 `DECISION_LOG.md`：

- 选择 runtime backend；
- 改变 fault injection backend；
- 修改 safety policy；
- 修改 phase gate；
- 修改 artifact schema；
- 调整 scale policy；
- 放弃或延迟某个能力；
- 把某 gate 标为 optional；
- 接受已知风险。

## 9. Artifact 与状态的关系

状态文件只保存索引与摘要，真实证据保存在 artifact。`ARTIFACT_INDEX.md` 必须把 run_id、phase、gate、artifact 路径、schema、hash 关联起来。

```text
PHASE_LEDGER row
      |
      v
run_id
      |
      v
ARTIFACT_INDEX rows
      |
      v
artifacts/runs/<run_id>/*
```

## 10. 自动 loop 的停止条件

自动 loop 只能在以下条件停止：

1. `ALL_PHASES_PASS`。
2. 当前 phase `SAFETY_BLOCKED`。
3. 当前 phase `BLOCKED_RESOURCE`。
4. 当前 phase `BLOCKED_ENV` 或 `BLOCKED_PROGRESS` 且没有安全 fallback。
5. 连续多次同一 gate 失败或连续无进展达到阈值，并已写入 failure artifact、blocker 与 HANDOFF。

停止不等于完成；状态必须准确写入。`BLOCKED_*` 不是 PASS。
