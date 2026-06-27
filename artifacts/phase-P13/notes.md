# P13 Notes
## 已验证
- docker/nodehost.Dockerfile 与 docker/nodehost-entrypoint.sh 已创建。
- DockerNodehostClient 按 virtual_az_id 分组构造 host network 命令，一个 virtual AZ 一个容器。
- command builder unit tests 证明不会一节点一容器。
- Docker capability 不可用时返回 SKIPPED_RESOURCE，unit contract 仍通过。

## 未验证或不确定
- 本阶段不构建镜像、不运行 Docker，也不验证 host network 在当前机器真实可用。

## 风险
- Docker integration 仍是 command contract；真实运行和 artifact 收集需要后续阶段/人工环境验证。

## 下一阶段交接
- P14 应实现多 Mac SSH 编排，且不得耦合到 Docker 实现。
