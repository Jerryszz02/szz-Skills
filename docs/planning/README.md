# non-gpt-subagent-worker 实施规划索引

## 文档目的

记录本次根据正式 plan 新增 `non-gpt-subagent-worker` skill 的最小实现指导，供实现和复查时引用。

## 生成信息

| 项目 | 内容 |
| --- | --- |
| 更新时间 | 2026-07-07 |
| 项目根目录 | `/Users/jerryszz/Desktop/Projects/szzSkills` |
| 任务 | 新增用于非 OpenAI 模型外部 worker 调度的个人 Codex skill |

## 已检查证据

| 证据 | 用途 |
| --- | --- |
| `README.md` | 确认仓库说明、skill 速览和安装维护入口。 |
| `AGENTS.md` | 确认 skill 布局、校验命令、README 更新规则和 secrets 边界。 |
| `plan-project-docs/SKILL.md` | 确认执行正式 plan 前生成最小 planning 文档的触发规则。 |
| `/Users/jerryszz/.codex/skills/.system/skill-creator/SKILL.md` | 确认新 skill 的结构、frontmatter 和校验要求。 |

## 文档清单

| 文档 | 用途 |
| --- | --- |
| `technical-design.md` | 固化 skill、脚本和 worker 调度实现方式。 |
| `security-privacy.md` | 记录本地/第三方模型、secrets 和权限边界。 |
| `test-plan.md` | 记录必须运行的校验和手工验证场景。 |

## 已跳过文档

| 文档 | 跳过原因 |
| --- | --- |
| `project-brief.md` | 项目背景已由 README 和本索引覆盖。 |
| `prd.md` | 本次是开发者工具 skill，不涉及面向终端用户的产品需求。 |
| `architecture.md` | 仅新增单个 skill 和脚本，架构约束可并入技术设计。 |
| `api-design.md` | 不新增项目服务 API；脚本 CLI 契约写入技术设计。 |
| `database-design.md` | 无持久化 schema。 |
| `release-plan.md` | 无部署流程；安装同步按仓库 README 既有规则执行。 |
| `operations-runbook.md` | 无长期运行服务。 |
| `decision-log.md` | 关键取舍已写入技术设计和安全文档。 |

## 待确认

- 是否在实现完成后立即同步安装到 `~/.codex/skills/non-gpt-subagent-worker/`：本次计划写成“若需要安装”，默认先完成仓库实现与验证。
