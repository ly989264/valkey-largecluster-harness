# Gate / Diff / Artifacts / Status 脚本规范（v2 fixed）

本文件定义 P00 必须实现的脚本契约。脚本读取 `codex/phase_manifest.json`，不得从 Markdown prose 中解析阶段范围。

## 1. 通用脚本要求

所有 P00 脚本必须满足：

```text
1. 只使用 Python 标准库。
2. 支持 --json；成功 exit code = 0，失败 exit code != 0。
3. 错误信息必须包含 phase、failed_check、reason。
4. 除 codex_next.py 可修改 loop_state/current_phase_contract，其他 guard 默认只读。
5. phase_gate.py check 可以写 artifacts/phase-PXX/gate_check.json，不能修改源代码。
6. 不得通过硬编码 phase id 来绕过 manifest。
```

## 2. codex/phase_manifest.json

P00 必须从 `01_阶段Manifest源_ValkeyHarness.md` 的 canonical JSON block 精确生成该文件。

必须校验：

```text
version == 2
phase_ids == P00..P16 连续
每个 phase 有 id/order/name/goal/allowed_paths/required_outputs/pre_gate_commands/required_artifacts/acceptance/forbidden
每个 phase 的 required_artifacts 都位于 artifacts/phase-PXX/
每个 phase 的 allowed_paths 包含 artifacts/phase-PXX/** 和 global control paths 展开结果
所有 pre_gate_commands 均不得包含 "phase_gate.py check"
P00 allowed_paths 必须包含 scripts/project_quality_gate.py 与 tests/test_p00_loop_control.py
```

## 3. codex/loop_state.json

建议结构：

```json
{
  "version": 2,
  "current_phase": "P00",
  "blocked": false,
  "blocked_reason": null,
  "complete": false,
  "phases": {
    "P00": {
      "status": "IN_PROGRESS",
      "attempts": 1,
      "base_ref": "<git sha or NO_GIT>",
      "claimed_at": "<iso8601>",
      "updated_at": "<iso8601>",
      "result_path": "artifacts/phase-P00/result.json",
      "phase_card_path": "codex/phase_cards/P00.md"
    }
  }
}
```

合法状态：

```text
PENDING
CLAIMED
IN_PROGRESS
PASS
FAIL
BLOCKED
```

状态规则：

```text
PENDING -> CLAIMED -> IN_PROGRESS -> PASS
IN_PROGRESS -> FAIL -> IN_PROGRESS，最多 3 次
IN_PROGRESS -> BLOCKED
PASS 不得回退
BLOCKED 后不得进入后续阶段
complete=true 只能由 codex_next.py 在 P16 PASS 后写入
```

## 4. codex_next.py

必须支持：

```bash
python3 scripts/codex_next.py status --json
python3 scripts/codex_next.py next --json
python3 scripts/codex_next.py claim --phase P03 --json
python3 scripts/codex_next.py progress --phase P03 --json
python3 scripts/codex_next.py pass --phase P03 --json
python3 scripts/codex_next.py fail --phase P03 --json
python3 scripts/codex_next.py block --phase P03 --reason "..." --json
python3 scripts/codex_next.py explain --phase P03 --json
```

`next` 逻辑：

```text
读取 manifest 和 loop_state。
如果无 loop_state，返回 P00，但不得自动写状态。
如果 blocked=true，返回 BLOCKED。
如果存在 CLAIMED/IN_PROGRESS 阶段，返回该阶段。
按 order 返回第一个非 PASS 阶段。
如果 P00-P16 都 PASS，返回 COMPLETE。
```

`claim` 逻辑：

```text
只能 claim next 返回的阶段。
记录 attempts +1。
记录 base_ref：git rev-parse HEAD；无 git 则 NO_GIT。
写 codex/current_phase_contract.json 和 .md。
状态置为 CLAIMED，然后 progress 可置为 IN_PROGRESS。
```

`pass` 逻辑：

```text
先运行：python3 scripts/phase_gate.py check --phase <phase> --json
只有该命令 exit_code=0，才能把 loop_state.phases[phase].status 写为 PASS。
如果 phase=P16 且所有阶段 PASS，写 complete=true。
pass 命令不得接受 --force。
```

## 5. diff_guard.py

必须支持：

```bash
python3 scripts/diff_guard.py changed-files --phase P03 --json
python3 scripts/diff_guard.py allowed-files --phase P03 --json
python3 scripts/diff_guard.py check --phase P03 --json
```

变更来源优先级：

```text
1. 如果 .git 存在且 loop_state 中有 base_ref：
   - git diff --name-status <base_ref>..HEAD
   - git diff --name-status
   - git ls-files --others --exclude-standard
   合并三者，覆盖 committed-in-phase、working tree、untracked。
2. 如果无 git：读取 artifacts/phase-PXX/changed_files.txt。
3. 以上均无结果时，changed-files 可返回空，但 artifact_guard 仍要求 changed_files.txt 存在。
```

匹配规则：

```text
使用 fnmatch/pathlib 风格 glob。
当前 phase 的 allowed_paths 加上 global control paths 展开结果是唯一允许范围。
artifacts/phase-PXX/** 只允许当前 phase。
禁止修改其他阶段 artifacts。
禁止修改 Markdown spec bundle。
删除文件也必须在 allowed_paths 内。
```

失败 JSON：

```json
{
  "status": "FAIL",
  "phase": "P03",
  "failed_check": "diff_guard",
  "violations": [{"file": "...", "reason": "not in allowed_paths"}]
}
```

## 6. artifact_guard.py

必须支持：

```bash
python3 scripts/artifact_guard.py check --phase P03 --json
python3 scripts/artifact_guard.py explain --phase P03 --json
```

必须检查：

```text
required_artifacts 全部存在且非空。
result.json 可解析，phase 匹配，status=PASS。
result.json 有 manifest_sha256 和 phase_card_sha256。
commands.jsonl 每行是 JSON，包含 phase/command/exit_code/started_at/finished_at。
commands.log 非空。
notes.md 非空，且包含“已验证”“未验证或不确定”“风险”。
changed_files.txt 存在；其中每个文件也必须通过 diff_guard allowed_paths。
```

## 7. status_guard.py

必须支持：

```bash
python3 scripts/status_guard.py check --phase P03 --json
python3 scripts/status_guard.py explain --phase P03 --json
```

必须检查：

```text
loop_state.json 存在且 version=2。
当前 phase 是 next/claim/progress/pass 允许的阶段。
之前所有 phase 都是 PASS。
未来 phase 不得是 PASS。
blocked=true 时任何非 block/status/explain 命令失败。
complete=true 只能在 P16 PASS 且所有 phase PASS 时出现。
```

`phase_gate.py check` 在 pass 前运行时，当前 phase 状态可以是 CLAIMED 或 IN_PROGRESS；在重复审计时也可以是 PASS。

## 8. forbidden_guard.py

必须支持：

```bash
python3 scripts/forbidden_guard.py check --phase P03 --json
python3 scripts/forbidden_guard.py scan --json
```

至少扫描：

```text
Docker-in-Docker: docker:dind, privileged.*dockerd, DOCKER_HOST=tcp://
One-node-one-container: 对每个 node 执行 docker run 的明显循环模式
Fake pass: assert True, pytest.skip( 无 SKIPPED_RESOURCE 说明, return {"status":"PASS"} 且无验证输入
Hard-coded cluster scale: total_nodes == 6 作为核心逻辑分支，除测试 fixture 外
Hard-coded host/IP/port: 127.0.0.1 或 localhost 写入 planner/config renderer 核心逻辑，除 single-mac sample/test 外
Spec mutation: 修改 codex_valkey_loop_md_bundle*/ 下文件
```

扫描必须允许合理测试 fixture，但发现疑似模式时要给出文件、行号、pattern 和原因。

## 9. phase_gate.py

必须支持：

```bash
python3 scripts/phase_gate.py list --json
python3 scripts/phase_gate.py explain --phase P03 --json
python3 scripts/phase_gate.py check --phase P03 --json
```

`check` 顺序：

```text
1. manifest schema check。
2. status_guard check。
3. artifact_guard check。
4. diff_guard check。
5. commands.jsonl exact pre_gate_commands check。
6. forbidden_guard check。
7. result.json expected_outputs/verified_outputs coverage check。
8. 写 artifacts/phase-PXX/gate_check.json。
```

命令匹配必须精确比较 canonical manifest 中的 `pre_gate_commands` 字符串。Shell redirection 命令也按字符串记录；Codex 不得把失败命令改名为成功命令。

## 10. project_quality_gate.py

P00 创建严格 stub：

```text
--help / --json / --candidate-phase 参数可用。
在 P16 之前不作为 phase pre_gate command。
如果缺少 harness/project_quality.py 或 report pipeline，返回 FAIL，不得假 PASS。
```

P16 必须完成它，使其检查：

```text
manifest consistency。
P00-P15 loop_state PASS，P16 candidate artifacts 存在。
forbidden_guard 全仓扫描通过。
核心 unit tests 可运行。
report honesty：失败、跳过、不确定项不能被隐藏。
scale-2000-empty 的非生产声明存在。
```
