# P14 Notes

## 已验证
- 已实现 SSHExecutor 和 FakeSSHExecutor，真实执行固定使用 BatchMode 非交互 SSH，单元测试仅使用 fake executor。
- 已实现 RemoteNodehostClient，对远端 nodehostctl 的 status/start/cleanup 以及 artifact collect 进行命令封装。
- 已实现 Deployer，按 ClusterPlan 的 physical_host_id 分发节点到多主机，支持 preflight、sync/package、start virtual AZ runtime、collect artifacts、cleanup。
- 已运行本阶段 manifest 定义的 py_compile 与 unittest pre-gate 命令，均通过。

## 未验证或不确定
- 未连接真实多 Mac 主机执行 SSH，只验证了命令构造、非交互约束和基于 ClusterPlan 的分发逻辑。

## 风险
- 远端路径、包同步细节和 nodehostctl 实际安装位置仍需后续真实环境接入时收敛。

## 下一阶段交接
- P15 可在不耦合 Docker 的前提下补充网络故障 backend，并通过 fake/command-contract 测试验证网络命令构造不被真实执行。
