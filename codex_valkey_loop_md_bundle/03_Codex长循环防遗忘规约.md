# Codex 长循环防遗忘规约（v2 fixed）

本文件专门约束长时间 goal 模式中的上下文遗忘风险。Codex 不得只靠最初读到的长 prompt 记忆执行。

## 1. 每阶段开始的强制重读

每次 `codex_next.py next --json` 输出 phase 后，必须重新读取：

```text
codex/phase_cards/PXX.md
codex/current_phase_contract.md
03_Codex长循环防遗忘规约.md
```

只允许按当前 phase card 执行。不得凭记忆引用上一阶段 allowed_paths 或 commands。

## 2. 阶段内短计划限制

每个阶段开始只输出不超过 8 条阶段内计划。计划必须覆盖：

```text
1. 本阶段目标。
2. 本阶段 allowed_paths。
3. 本阶段 pre_gate_commands。
4. 本阶段 artifacts。
5. 不做的后续功能。
```

如果计划中出现不在 allowed_paths 的文件，必须在写代码前修正计划。

## 3. 证据先于结论

在 artifacts 中，结论必须由证据支撑：

```text
result.json status=PASS 只能在 pre_gate_commands 全部 exit_code=0 后写。
verified_outputs 必须对应实际文件、测试或命令输出。
未执行的真实资源集成必须写 NOT_VALIDATED 或 SKIPPED_RESOURCE，不得写 PASS。
```

## 4. commands.jsonl 记录格式

每个命令一行 JSON：

```json
{"phase":"P03","command":"python3 -m unittest discover -s tests -p 'test_p03_virtual_az.py'","exit_code":0,"started_at":"...","finished_at":"...","stdout_path":"artifacts/phase-P03/cmd-001.stdout.txt","stderr_path":"artifacts/phase-P03/cmd-001.stderr.txt"}
```

命令字符串必须与 manifest 的 pre_gate_commands 完全一致。不得只记录摘要。

## 5. notes.md 固定结构

每个阶段 notes.md 必须包含：

```text
# PXX Notes
## 已验证
## 未验证或不确定
## 风险
## 下一阶段交接
```

“未验证或不确定”不能为空；如果确实无未验证项，写“本阶段范围内未发现；后续阶段仍需验证：...”并列出后续范围。

## 6. result.json 固定结构

每个阶段 result.json 必须包含：

```json
{
  "phase": "P03",
  "status": "PASS",
  "attempt": 1,
  "manifest_sha256": "...",
  "phase_card_sha256": "...",
  "summary": "...",
  "expected_outputs": ["..."],
  "verified_outputs": [{"output":"...","evidence":"..."}],
  "commands": [{"command":"...","exit_code":0}],
  "changed_files": ["..."],
  "risks": ["..."]
}
```

## 7. 不允许的“省事”行为

```text
不得为了通过 gate 删除测试。
不得把复杂功能挪到文档里声称已完成。
不得添加宽泛 allowed_paths。
不得在 P00 后修改 phase_manifest.json，除非用户明确要求重开规约。
不得把 fake runtime 的结果表述为真实 Valkey 生产验证。
不得因为真实 Docker/SSH/Valkey 不存在而伪造成功；应走 fake/unit 或 SKIPPED_RESOURCE/NOT_VALIDATED 路径。
```

## 8. BLOCKED 的唯一合规场景

只有以下情况可以 BLOCKED：

```text
canonical manifest JSON 无法解析或自相矛盾。
当前阶段必须修改的文件不在 allowed_paths，且无法通过当前 allowed_paths 内设计调整解决。
pre_gate_commands 依赖的系统能力在本阶段 contract 中不是 optional/fake/unit，导致无法验证。
需要削弱 gate、删除断言、伪造 artifacts 才能继续。
git commit/push 到 single_loop_harness 失败。
```

BLOCKED 必须写 `artifacts/phase-PXX/blocker.md`，包含：原因、已验证事实、失败命令、未修改或已回滚的越界文件、建议的人类决策。
