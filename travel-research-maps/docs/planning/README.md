# travel-research-maps 项目文档索引

## 文档目的

记录 `travel-research-maps` Firecrawl 多平台来源扩展后的产品、技术、安全和验证指导。

## 更新时间

2026-06-29

## 已检查的项目根目录

`/Users/jerryszz/Desktop/Projects/szzSkills/travel-research-maps`

## 已检查的关键项目证据

| 证据 | 用途 |
| --- | --- |
| `SKILL.md` | 触发条件、Firecrawl 主工作流、覆盖门槛、审核清单和 Google Maps 写入边界。 |
| `references/scoring-rubric.md` | 多平台证据、推荐档位、营销排除、分层和事实核验规则。 |
| `scripts/score_candidates.py` | 离线评分、去重、日期过滤、平台门槛和 JSON 输入输出。 |
| `scripts/test_score_candidates.py` | 评分器回归测试场景。 |
| `agents/openai.yaml` | Codex UI 展示名称、短描述和默认提示词。 |

## 已更新文档

| 文档 | 用途 |
| --- | --- |
| `project-brief.md` | 说明 Firecrawl 来源扩展的目标、边界和成功标准。 |
| `prd.md` | 定义新版用户可见行为和验收标准。 |
| `architecture.md` | 说明 Firecrawl、评分器、事实核验和 Google Maps 写入的数据流。 |
| `technical-design.md` | 记录评分器平台门槛和实现维护指引。 |
| `security-privacy.md` | 记录外部抓取、平台限制、凭据和地图写入的安全边界。 |
| `user-flow.md` | 描述研究、评分、审核和批准后保存流程。 |
| `test-plan.md` | 定义自动化和人工验证方式。 |
| `decision-log.md` | 保留 Firecrawl、多平台、Google Maps 核验等关键决策。 |

## 已跳过文档

| 文档 | 跳过原因 |
| --- | --- |
| `api-design.md` | 未新增稳定 HTTP/RPC/API 契约。 |
| `database-design.md` | 未新增持久化 schema、迁移或数据库。 |
| `release-plan.md` | 当前是本地 skill 文档和脚本更新，无生产发布路径。 |
| `operations-runbook.md` | 无长期运行服务、队列或运维流程。 |

## 待确认

- Firecrawl 对小红书、Bilibili、Instagram、X 等平台的公开页面抓取质量会随平台限制变化，需要实际任务中记录覆盖缺口。
- Google Maps 保存仍依赖用户已登录的浏览器会话，列表创建细节需在实际 UI 中确认。
