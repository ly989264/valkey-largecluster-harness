# P07 Notes
## 已验证
- nodehostctl 提供 status/prepare/start/stop/cleanup/metrics 命令。
- LocalProcessManager 和 ProcessTable 使用 run_id scoped 状态文件；cleanup 只删除指定 run_id。
- FakeValkeyRuntime 可表示多个 node 状态和 metrics，unit tests 不需要真实 Valkey binary。
- harness/nodehost_client.py 提供 controller-side client contract。

## 未验证或不确定
- 本阶段不启动真实 Valkey、不管理真实 OS 进程、不验证端口监听；fake/local contract 供后续 runner 使用。

## 风险
- nodehostctl 当前只提供 fake process table 行为；真实进程启动将在后续配置生成和 runner 阶段收敛。

## 下一阶段交接
- P08 应基于 ClusterPlan/NodeSpec 渲染 Valkey 配置文件，但仍不启动集群。
