# subagent-orchestrator 实施规划索引

## 文档目的

记录 `subagent-orchestrator` 替换旧外部 worker skill 后的调度契约，供实现、安装和复查使用。

## 生成信息

| 项目 | 内容 |
| --- | --- |
| 更新时间 | 2026-09-03 |
| 项目根目录 | `/Users/jerryszz/Desktop/Projects/szzSkills` |
| 任务 | 所有原生 spawn 前执行委派闸门，并建立 DeepSeek 优先的固定 fallback 顺序 |

## 已检查证据

| 证据 | 用途 |
| --- | --- |
| `AGENTS.md` | 确认 skill 布局、验证、分支交付和 secrets 边界。 |
| `subagent-orchestrator/SKILL.md` | 确认委派闸门、角色顺序、主 Agent 所有权和验收流程。 |
| `subagent-orchestrator/references/` | 确认路由、task packet、嵌套委派禁令和外部 worker 契约。 |
| `subagent-orchestrator/scripts/` | 确认 DSH/Kimi worktree、路径 scope、artifact 和测试行为。 |
| 本机 `dsh --profile headless --help` 与可用性探针 | 确认 headless profile 可从命令行执行单次任务。 |

## 文档清单

| 文档 | 用途 |
| --- | --- |
| `technical-design.md` | 固化委派闸门、fallback、并发检查、task packet 和 runner 契约。 |
| `security-privacy.md` | 记录外部进程、secrets、worktree 和主 Agent 审查边界。 |
| `test-plan.md` | 记录 skill 校验、runner 单元测试和 live profile 探针。 |

## 已跳过文档

| 文档 | 跳过原因 |
| --- | --- |
| `prd.md` | 本次是内部调度契约调整，不新增终端产品行为。 |
| `architecture.md` | 结构和执行流已足够集中在技术设计。 |
| `api-design.md` | 不新增网络服务 API。 |
| `database-design.md` | 不涉及持久化 schema。 |
| `release-plan.md` | 仅通过仓库 PR 和本地 skill 同步交付。 |
| `operations-runbook.md` | 不包含长期运行服务。 |

## 待确认

- Skill 指令可以约束遵循它的 Agent，但不是 `spawn_agent` 工具层的强制拦截器；若未来需要不可绕过的强制策略，应在 Codex runtime 或全局 Agent 指令层实现。
