# P03 Notes
## 已验证
- VirtualAZPlacement model 与 deterministic topology planner 已实现。
- plan output 包含 placements、virtual_az_host_matrix、node_drafts 和 isolation warnings。
- single_az、physical_aligned、uniform_interleaved、custom 均由单元测试覆盖。
- harnessctl plan 可生成 byte-stable JSON topology draft。

## 未验证或不确定
- 本阶段不分配 client/bus ports、slots、primary/replica 关系，也不启动任何 runtime。

## 风险
- P03 node_drafts 只是 topology draft；P04 必须把它扩展为完整 ClusterPlan。

## 下一阶段交接
- P04 应在现有 topology draft 基础上生成 NodeSpec、端口、slot range 和 replica placement，不应让后续 runtime 重新规划。
