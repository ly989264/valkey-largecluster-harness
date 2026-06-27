# P10 Notes
## 已验证
- run-scenario CLI 已接入 ScenarioRunner。
- smoke-6 fake backend 完整执行 validate、plan、nodehost start、fake cluster create/check、cleanup。
- run artifacts 写入 events.jsonl、run_status.json、cluster_plan.json、commands.jsonl。
- cleanup 在 finally 路径执行，unit test 验证 nodehost process_table 被移除。
- 非 fake backend 在缺少 valkey-server 时返回 SKIPPED_RESOURCE，不伪装 PASS。

## 未验证或不确定
- 本阶段不启动真实 Valkey，不验证真实集群性能、RTO 或生产行为。

## 风险
- pre-gate run artifacts 写在 /tmp 下，phase artifacts 中只记录命令证据；最终 report 阶段需索引实际 run artifacts。

## 下一阶段交接
- P11 应在 fake/process path 上增加 node/virtual AZ fault 操作，不做网络故障。
