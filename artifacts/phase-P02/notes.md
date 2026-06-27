# P02 Notes
## 已验证
- Inventory/Scenario dataclasses 覆盖 physical hosts、platform、virtual AZ、topology_mode、ports、runtime 和 cluster scale 默认值。
- `.json/.yaml/.yml` loader 使用标准库 JSON 与 mini YAML fallback；schema 文件由 config loader 实际加载。
- 三个 sample inventories 与 smoke-6、scale-100 scenarios 已加入并通过 validate/unit tests。
- validate CLI 已接入配置验证，非法配置返回结构化 FAIL JSON。

## 未验证或不确定
- 本阶段不规划 virtual AZ placement、端口分配、slot、replica 关系，也不启动 Docker/SSH/Valkey；这些留给 P03 及后续阶段。

## 风险
- YAML fallback 是严格小子集，足够覆盖本仓库样例；复杂 YAML 特性未声明为支持。

## 下一阶段交接
- P03 应基于 P02 输出实现 deterministic virtual AZ placement，并输出 topology draft。
