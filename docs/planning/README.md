# subagent-orchestrator 规划索引

## 来源与状态

- 请求：在显式调用与统一结果摘要之上，把委派改为 串行委派：整个用户任务跨原生与外部路线只保持一个在跑 worker、串行执行、角色按需切换且每次覆盖完整问题或结果，并把停止规则前移到首次交付之前。
- 模式：实现与既有文档同步；更新日期：2026-09-24。
- 项目根目录：`/Users/jerryszz/Desktop/Projects/szzSkills`。
- 本项目是个人技能源仓库；本轮减少模型往返与交接，保留边界及计量。
- 当前状态：串行委派与灵活角色、默认直接执行、短交接及停止规则已实现。集成后 113 项离线回归、技能格式、shell 语法、Markdown 链接、规划审计、diff 与源/安装副本一致性检查通过；本轮没有独立模型盲测或 A/B，不声称已实测节省。

## 已检查证据

`AGENTS.md`、根 README、技能与 references、同步脚本、DeepSeek runner、task packet scope 校验及 result/receipt/usage 测试。本修订从已刷新的 `origin/main`（`d3e6a9f`）建立独立分支，再保留既有的显式调用改动（本分支提交 `bc3ac53`）。历史 A/B 仅以汇总数字说明动机，原始会话与 provider 日志留在仓库外。

## 文档清单

| 文档 | 维护职责 |
| --- | --- |
| [technical-design.md](technical-design.md) | 完整优化计划、串行委派 委派门槛、执行责任、确定性整合及后续 A/B/C 方案 |
| [test-plan.md](test-plan.md) | 自动化、路由盲测、安装验收和节省结论边界 |
| [security-privacy.md](security-privacy.md) | 外部执行、凭据、patch 审查和本地数据保护 |

[根 README](../../README.md)面向使用者；[技能入口](../../subagent-orchestrator/SKILL.md)及 references 是运行时契约，脚本和测试证明实现。本目录保留需求与设计基线，事实冲突以代码为准。

未新增 PRD、独立架构/API/数据库/发布/运维文档：现有 CLI 契约可集中在技术设计，无服务、数据库或部署。未新增开发者指南，避免重复 references。

## 验证与待确认

本轮验证日期与结果见 [测试计划](test-plan.md)。发布状态以 GitHub PR 为准；加载状态以新任务/重启后的 registry 为准，不以复制成功代替。

- 待验证：串行委派 修订在真实任务中的主模型用量、按模型计价的总成本与延迟效果；本轮不自动启动付费 benchmark。
- 采用限制：全局 AGENTS.md 不随技能同步更改；已有强制委派规则需由用户另行决定是否采用新模板。
