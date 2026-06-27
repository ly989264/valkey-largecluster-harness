# P04 Notes
## 已验证
- ClusterPlan、NodeSpec、SlotRange、ReplicaPlacement 模型已实现。
- smoke-6 生成 3 primary 与 3 replica，client/bus ports 唯一且不重叠。
- Slot ranges 完整覆盖 0..16383，无 gap 或 overlap。
- Replica placement 在可行时避开 primary virtual AZ，无法做到时会写 warning。
- harnessctl plan 现在输出包含 cluster_plan 的完整 JSON。

## 未验证或不确定
- 本阶段不执行 cluster_create、nodehost、Valkey runtime 或真实网络验证；后续阶段必须直接消费 ClusterPlan，不得重新规划。

## 风险
- 当前 replica anti-affinity 只基于 virtual AZ；更强的物理 host 级约束可在后续能力阶段扩展但不能改写本阶段计划结果。

## 下一阶段交接
- P05 应实现平台抽象并保持 planner/cluster_create/report 与平台命令解耦。
