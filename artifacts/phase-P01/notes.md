# P01 Notes
## 已验证
- harness package 可以导入，`python3 -m py_compile` 覆盖 P01 的四个 Python 文件。
- `harnessctl version --json` 和 `doctor --dry-run --json` 输出稳定 JSON。
- validate/plan/run-scenario/report 提供 help，并在直接执行时返回明确 NOT_IMPLEMENTED JSON。
- Makefile 提供 test、gate、lint-lite 目标且不引入第三方依赖。

## 未验证或不确定
- 本阶段不验证 inventory/scenario 配置、拓扑规划、节点运行、Docker、SSH、Valkey 或网络行为；这些属于后续阶段。

## 风险
- P01 的 CLI 子命令是壳实现，后续阶段需要在各自 allowed_paths 内替换 NOT_IMPLEMENTED 行为。

## 下一阶段交接
- P02 应实现 inventory/scenario 契约、schema 与 validate 命令，不应在 P02 做拓扑规划。
