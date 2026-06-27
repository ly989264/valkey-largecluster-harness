# P06 Notes
## 已验证
- ArtifactLayout 基于 root/run_id 生成隔离目录和标准 artifact 路径。
- EventRecorder 追加 JSONL，replay_events 可从磁盘重放事件。
- RunStatusWriter 与 CommandLogWriter 可写入并读取磁盘 artifacts。
- 损坏 JSONL 行会被标记为 invalid evidence，不会被吞掉或导致 report reader 崩溃。
- 事件 taxonomy 包含 run、command、node、cluster、fault、failover、metric、assertion。

## 未验证或不确定
- 本阶段不运行场景、不启动 nodehost、不生成最终 report；只提供可审计 artifact 基础设施。

## 风险
- ArtifactLayout.create 对已存在 run_id 使用 exist_ok=False，调用方需选择唯一 run_id 或显式处理冲突。

## 下一阶段交接
- P07 应复用 ArtifactLayout/EventRecorder，为本地 nodehost fake runtime 写入 run-scoped 状态。
