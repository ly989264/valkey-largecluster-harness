# 给 Codex 先读取的入口文件（v2 fixed）

Codex，先按顺序读取本目录下四个 Markdown：

```text
1. 00_给Codex的主控_自动NEXT循环规约.md
2. 01_阶段Manifest源_ValkeyHarness.md
3. 02_Gate_Diff_Artifacts_Status脚本规范.md
4. 03_Codex长循环防遗忘规约.md
```

读取后不要解释，不要总结，不要询问。直接从 P00 开始执行。

本 bundle 的硬规则：

```text
1. 01_阶段Manifest源_ValkeyHarness.md 中 BEGIN_CANONICAL_PHASE_MANIFEST_JSON 与 END_CANONICAL_PHASE_MANIFEST_JSON 之间的 JSON 是唯一阶段真相。
2. 其他 Markdown 只定义执行协议、脚本契约和防遗忘纪律；不得覆盖 canonical manifest。
3. 如果 prose 与 canonical JSON 看起来冲突，以 canonical JSON 为准，不得因此 BLOCKED。
4. 如果 canonical JSON 自身无法解析、phase id 不连续、或 P00 必须创建的文件不在 P00 allowed_paths 中，才允许 BLOCKED。
5. 每个阶段必须由 scripts/codex_next.py next/claim/progress/pass 和 scripts/phase_gate.py check 放行；Codex 主观判断无效。
6. 每个阶段完成并 PASS 后，必须 commit 并 push 到 single_loop_harness 分支；失败则 BLOCKED，不得继续下一阶段。
```

当前目标：实现 Valkey 9.x large-cluster validation harness。先支持单 Mac fake/local smoke，再支持多 Mac、Docker hostnet、Linux 网络故障迁移边界、scale ladder 和最终可审计 report。

当前 canonical manifest sha256：

```text
d34c3ae82d24fdfa64baf19779a405194f3c2bd9e559951d6b7350fcad478f30
```
