# subagent-orchestrator 规划索引

## 来源与状态

- 请求：基于 V8 A/B 分析完成优化计划并改进现有技能。
- 模式：执行前准备与既有文档同步；更新日期：2026-09-17。
- 项目根目录：`/Users/jerryszz/Desktop/Projects/szzSkills`。
- 本项目是个人技能源仓库；本轮减少模型往返与交接，保留边界及计量。
- 当前状态：本轮实现已通过 91 项自动化测试、10 个路由盲测场景、技能格式与文档检查，并完成本地安装同步；仍在功能分支交付，未声称已合并或实测节省。

## 已检查证据

`AGENTS.md`、根 README、技能与 references、同步脚本、两个同步外部 runner、task packet scope 校验及 receipt/usage 测试。起点为本次刷新的 `origin/main`（`5b49901`）。历史 A/B 仅以汇总数字说明动机，原始会话与 provider 日志留在仓库外。

## 文档清单

| 文档 | 维护职责 |
| --- | --- |
| [technical-design.md](technical-design.md) | 完整优化计划、委派门槛、执行责任、确定性整合及后续 A/B/C 方案 |
| [test-plan.md](test-plan.md) | 自动化、路由盲测、安装验收和节省结论边界 |
| [security-privacy.md](security-privacy.md) | 外部执行、凭据、patch 审查和本地数据保护 |

[根 README](../../README.md)面向使用者；[技能入口](../../subagent-orchestrator/SKILL.md)及 references 是运行时契约，脚本和测试证明实现。本目录保留需求与设计基线，事实冲突以代码为准。

未新增 PRD、独立架构/API/数据库/发布/运维文档：现有 CLI 契约可集中在技术设计，无服务、数据库或部署。未新增开发者指南，避免重复 references。

## 验证与待确认

验证日期为 2026-09-17；命令与本次结果见 [测试计划](test-plan.md)。发布状态以 GitHub PR 为准；加载状态以新任务/重启后的 registry 为准，不以复制成功代替。

- 待验证：新版在真实任务中的 Token/费用效果；本轮不自动启动付费 benchmark。
- 采用限制：全局 AGENTS.md 不随技能同步更改；已有强制委派规则需由用户另行决定是否采用新模板。
