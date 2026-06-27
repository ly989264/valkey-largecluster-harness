# 给 Codex 的主控规约：自动 NEXT 循环与强制 Gate（v2 fixed）

本文件是执行协议。阶段范围、命令和产物以 `01_阶段Manifest源_ValkeyHarness.md` 的 canonical JSON 为唯一真相。

## 1. 执行器身份

Codex 是受控执行器，不是自由开发者。Codex 的任务是按阶段实现 Valkey 9.x large-cluster validation harness，并用脚本化 gate 阻止跑偏。

必须遵守：

```text
不得跳阶段。
不得合并阶段。
不得扩大 allowed_paths。
不得弱化测试、删除断言、伪造 artifacts。
不得把 SKIPPED_RESOURCE 写成 PASS。
不得修改本 Markdown 规约 bundle。
不得在 gate 未通过时 commit 阶段成果。
```

## 2. P00 bootstrap

P00 是唯一没有既有控制脚本可调用的阶段。P00 必须先从 canonical JSON 精确生成：

```text
codex/phase_manifest.json
codex/phase_cards/P00.md ... codex/phase_cards/P16.md
codex/loop_state.json
```

P00 还必须创建全部控制脚本：

```text
scripts/codex_next.py
scripts/phase_gate.py
scripts/diff_guard.py
scripts/artifact_guard.py
scripts/status_guard.py
scripts/forbidden_guard.py
scripts/project_quality_gate.py
```

P00 的 allowed_paths 已在 canonical JSON 中包含上述全部文件，包括 `scripts/project_quality_gate.py` 和 `tests/test_p00_loop_control.py`。不得把这些文件视为越界。

P00 的 pre-gate commands 不包含 `phase_gate.py check --phase P00`。这是有意设计：`phase_gate.py check` 是 gate 本身，不能作为它自己必须验证的 pre-gate command，否则会形成自举循环。

## 3. 每阶段标准循环

从 P01 开始，每一轮必须执行相同状态机。P00 在脚本创建完成后也必须按同一状态机完成 gate/pass。

```text
┌─────────────────────────┐
│ codex_next.py next      │  输出唯一当前阶段和阶段 contract
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ codex_next.py claim     │  记录 phase_base_ref / attempt / contract hash
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 重新读取 phase card      │  不依赖长上下文记忆
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 只改 allowed_paths       │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 运行 pre_gate_commands   │  精确记录 commands.jsonl / commands.log
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 写 result/notes/changed  │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ phase_gate.py check      │  检查 diff/artifacts/status/forbidden/commands
└──────┬──────────────────┘
       │PASS
       ▼
┌─────────────────────────┐
│ codex_next.py pass       │  内部再次运行 phase_gate.py check
└──────┬──────────────────┘
       ▼
┌─────────────────────────┐
│ git commit && git push   │  推送 single_loop_harness
└──────┬──────────────────┘
       ▼
┌─────────────────────────┐
│ 下一阶段                 │
└─────────────────────────┘
```

## 4. NEXT 的唯一来源

`python3 scripts/codex_next.py next --json` 是唯一 NEXT 来源。其输出必须包含：

```json
{
  "status": "OK",
  "next": "P03",
  "phase_contract": {"id": "P03", "allowed_paths": [], "pre_gate_commands": []},
  "must_reread": ["codex/phase_cards/P03.md", "03_Codex长循环防遗忘规约.md"]
}
```

如果输出 `BLOCKED` 或 `COMPLETE`，不得继续普通阶段实现。

## 5. Gate 与 pre-gate command 的边界

`pre_gate_commands` 是阶段必须先运行并记录的验证命令。`phase_gate.py check` 不是 pre-gate command，不得写进 manifest 的 `pre_gate_commands`。

每个阶段 gate 检查：

```text
1. phase exists in codex/phase_manifest.json。
2. loop_state 当前阶段合法，之前阶段已 PASS。
3. changed files 全部在 allowed_paths 或 global control paths 内。
4. required_artifacts 全部存在且非空。
5. commands.jsonl 精确包含该阶段所有 pre_gate_commands，且 exit_code=0。
6. result.json 可解析，status=PASS，manifest/card hash 匹配。
7. forbidden_guard 无禁止模式。
8. artifact_guard/status_guard/diff_guard 全部通过。
```

## 6. 失败与纠偏

每个阶段最多允许 3 次修复。失败后只能修当前阶段 allowed_paths 内文件。

```text
如果 pre_gate_commands 失败：修当前阶段代码或测试，不得删除测试或降低断言。
如果 diff_guard 失败：回滚越界文件，或停止并报告 BLOCKED。
如果 artifact_guard 失败：补齐真实 artifacts，不得伪造命令成功。
如果 status_guard 失败：修 codex_next/status 逻辑；不得手写 COMPLETE。
如果 forbidden_guard 失败：删除禁止实现路线。
```

3 次仍不能通过，写：

```text
artifacts/phase-PXX/blocker.md
```

并运行：

```bash
python3 scripts/codex_next.py block --phase PXX --reason "..." --json
```

## 7. VCS checkpoint

每个阶段 `codex_next.py pass --phase PXX --json` 成功后，必须：

```bash
git status --short
git add <本阶段 allowed_paths 中实际存在的变更文件> codex/loop_state.json codex/current_phase_contract.json codex/current_phase_contract.md artifacts/phase-PXX
git commit -m "PXX: <phase name>"
git push origin single_loop_harness
```

如果当前分支不是 `single_loop_harness`，先切换或创建该分支。若远端不存在、认证失败、push 被拒绝，必须 BLOCKED；不得进入下一阶段。

## 8. 完成条件

完成条件不是“代码看起来完成”，而是：

```text
P00-P16 都由 codex_next.py pass 标记 PASS；
P16 pre_gate_commands 中 project_quality_gate --candidate-phase P16 通过；
最终再次运行 scripts/project_quality_gate.py --candidate-phase P16 --json 通过；
所有阶段 artifacts 可审计；
最终 report 明确区分 PASS / FAIL / SKIPPED_RESOURCE / INCONCLUSIVE / NOT_VALIDATED。
```
