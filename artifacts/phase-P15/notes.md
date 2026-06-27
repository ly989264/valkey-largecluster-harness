# P15 Notes

## 已验证
- 已实现 NetworkFaultBackend、NetworkFaultResult、NetworkFaultTarget 和 UnsupportedNetworkFaultBackend。
- LinuxNetemBackend 已覆盖 isolate、heal、delay、loss、clear 的命令计划，并包含 client port 与 cluster bus port。
- DarwinPlatformAdapter 明确返回能力受限的 SKIPPED_RESOURCE 结果，不声称 Mac 精确网络注入可用。
- nodehost/faults_network.py 和 NetworkFaultExecutor 均按 ClusterPlan virtual AZ 选择目标。
- 已运行本阶段 manifest 定义的 py_compile 与 unittest pre-gate 命令，均通过。

## 未验证或不确定
- 未执行真实 tc/netem 或 firewall 命令；P15 只验证 Linux 迁移路径的命令构造。
- 未验证真实多主机网络隔离对 Valkey 9.x 集群的影响。

## 风险
- Linux 命令计划尚未处理不同发行版 firewall 工具差异。
- Darwin backend 当前仅能诚实返回能力不足，需要后续真实能力探测才可升级。

## 下一阶段交接
- P16 可汇总各阶段 artifact 与 report，并将 SKIPPED_RESOURCE、NOT_VALIDATED 等状态作为一等报告结果，不伪装为生产验证 PASS。
