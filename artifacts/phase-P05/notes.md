# P05 Notes
## 已验证
- PlatformAdapter interface、DarwinPlatformAdapter、LinuxPlatformAdapter 已实现。
- FakeExecutor 与 SubprocessExecutor 已实现，unit tests 使用 fake executor，不依赖真实 lsof/ps/docker/tc。
- doctor --dry-run 输出 platform_capabilities 和 Linux tc/netem 迁移提示，不改变系统状态。
- planner 未导入 platform_darwin/platform_linux。

## 未验证或不确定
- 本阶段不执行真实平台探测命令、不验证 Docker host network、不执行 tc/netem；这些能力只建模为 adapter contract。

## 风险
- Darwin network fault injection 明确为 unsupported；真实 Linux backend 要在 P15 验证命令构造边界。

## 下一阶段交接
- P06 应建立事件、状态和 artifacts 基础设施，继续保持 report 可从磁盘重建。
