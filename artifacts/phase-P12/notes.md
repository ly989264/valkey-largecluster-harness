# P12 Notes
## 已验证
- FailoverTimeline 包含 fault/PFAIL/FAIL/promotion/slot recovery/cluster ok/client recovery 时间戳。
- 完整 timeline 可计算所有 manifest 要求的 metrics。
- FailoverObserver 可从 events 重建 timeline，不合成缺失时间戳。
- StabilityAssertions 对缺失 PFAIL、promotion、client recovery 返回 INCONCLUSIVE；stale owner 返回 FAIL。

## 未验证或不确定
- 本阶段只验证事件证据模型，不运行真实 failover 或客户端流量。

## 风险
- metrics 依赖事件完整性；缺失证据必须保留 INCONCLUSIVE。

## 下一阶段交接
- P13 应实现 Docker hostnet nodehost contract，保持 Docker capability 不可用时结构化 SKIPPED_RESOURCE。
