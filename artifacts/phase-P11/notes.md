# P11 Notes
## 已验证
- FaultPlan、FaultExecutor 和 ProcessFaultBackend 已实现。
- Virtual AZ target selector 基于 ClusterPlan node virtual_az_id，不使用 hostname 猜测。
- kill/pause/resume/restart fake process fault 行为已由 unit tests 验证。
- resume/restart 重复执行不破坏状态。
- fault before/after events 包含时间戳与目标列表。

## 未验证或不确定
- 本阶段不实现网络延迟、丢包或隔离；不操作真实 OS 进程。

## 风险
- ProcessFaultBackend 是 fake process table backend，不代表真实进程信号行为。

## 下一阶段交接
- P12 应从事件重建 failover timeline 并对缺失证据返回 INCONCLUSIVE。
