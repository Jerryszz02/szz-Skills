# travel-research-maps 技术设计

## 文档目的

把 Firecrawl 来源扩展计划转换为具体实现与维护指引，尤其覆盖评分器输入输出、平台门槛、去重逻辑、错误处理和兼容性约束。

## 适用范围

适用于 `scripts/score_candidates.py`、`references/scoring-rubric.md`、`SKILL.md` 中与评分和执行顺序相关的内容。本文档仅根据当前仓库可见内容整理；未在仓库中找到证据的内容均不做假设。

## Plan 或项目证据

| 证据 | 技术含义 |
| --- | --- |
| `score_candidates.py` | 使用 Python 标准库实现，无外部依赖，无网络请求。 |
| `score_candidates.py` | 支持 `--input`、`--output`、`--as-of` 和 `--min-positive-platforms-for-priority`。 |
| `score_candidates.py` | 候选 `type` 只接受 `attraction` 和 `restaurant`。 |
| `score_candidates.py` | 证据 `stance` 只接受 `strong`、`positive`、`negative`、`neutral`。 |
| `scoring-rubric.md` | 同一平台同一作者或相同内容指纹视为同一独立来源。 |
| `test_score_candidates.py` | 覆盖评分门槛、严重风险、跨平台优先和单平台降级。 |

## 选定方案

采用“Firecrawl 收集公开证据，评分脚本确定性评分，Google Maps 做核验和批准后保存”的分层方案：

- `SKILL.md` 负责人机流程、Firecrawl 工具顺序、覆盖门槛、事实核验和 Google Maps 写入批准。
- `references/scoring-rubric.md` 负责解释多平台证据、营销排除、平台门槛和审计口径。
- `scripts/score_candidates.py` 只负责对已整理好的候选证据做离线评分。

## 评分器输入约定

评分器读取一个 JSON 对象，顶层必须包含 `candidates` 数组。每个候选当前使用的字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 候选地点名称。 |
| `type` | string | `attraction` 或 `restaurant`。 |
| `evidence` | array | 候选证据列表；缺失时按空列表处理。 |
| `hard_risks` | array | 严重风险列表；存在任一项时直接排除。 |

证据项当前使用的字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source` | string | 来源平台，用于作者独立性 key 和正向平台统计。 |
| `url` | string | 证据 URL；作者和指纹都缺失时作为 fallback key 的一部分。 |
| `author` | string | 作者或频道；同一来源同一作者只计一次。 |
| `published_at` | string | 日期字符串，使用前 10 位按 `YYYY-MM-DD` 解析。 |
| `stance` | string | `strong`、`positive`、`negative` 或 `neutral`。 |
| `is_marketing` | bool | 为 true 时完全排除。 |
| `content_fingerprint` | string | 相同内容指纹视为重复证据，即使跨平台也只计一次。 |

## 评分器输出约定

输出 JSON 包含：

| 字段 | 说明 |
| --- | --- |
| `as_of` | 本次研究日期。 |
| `candidates` | 每个候选的评分结果。 |
| `tier` | `priority`、`backup` 或 `excluded`。 |
| `net_score` | 有效独立证据分数之和。 |
| `positive_sources` | 分数大于 0 的有效独立来源数量。 |
| `positive_platforms` | 分数大于 0 的有效证据来源平台列表。 |
| `negative_sources` | 分数小于 0 的有效独立来源数量。 |
| `effective_evidence` | 计入评分的证据。 |
| `excluded_evidence` | 被排除证据的原因计数。 |

## 数据或状态流

1. `parse_date` 将 `published_at` 或 `--as-of` 解析为日期；无效日期返回 `None`。
2. `score_candidate` 用 `as_of - 365 days` 作为过期阈值。
3. 每条证据依次经过营销过滤、日期可识别过滤、过期/未来日期过滤、stance 校验和独立性去重。
4. 脚本根据有效证据计算净分、正向来源数、负向来源数和正向平台列表。
5. `hard_risks` 存在时直接 `excluded`。
6. 景点和餐厅分别使用不同优先门槛；若优先项正向平台数少于 CLI 参数要求，则降级为 `backup`。

## 错误处理和 fallback 行为

| 错误或异常 | 行为 |
| --- | --- |
| `--as-of` 格式不合法 | argparse 报错并退出。 |
| `--min-positive-platforms-for-priority < 1` | argparse 报错并退出。 |
| 输入缺少 `candidates` 数组 | argparse 报错并退出。 |
| 候选 `type` 非法 | 抛出 `ValueError`。 |
| 证据 `stance` 非法 | 抛出 `ValueError`。 |
| 证据日期缺失或无法解析 | 计入 `excluded_evidence.unknown_date`。 |
| 证据早于 365 天窗口或晚于 `as_of` | 计入 `excluded_evidence.stale`。 |
| 作者和内容指纹都缺失 | 使用 URL 和证据 index 作为 fallback 独立性 key。 |

## 兼容性约束

- 评分器当前使用 Python 3.9 可运行语法，包括 `str | None` 类型标注。
- `--min-positive-platforms-for-priority` 默认值为 1，保证旧调用兼容。
- Skill 工作流必须显式传入 `--min-positive-platforms-for-priority 2`。
- 不应引入网络请求或浏览器依赖。

## 任务拆分

| 改动类型 | 应修改文件 |
| --- | --- |
| 调整触发条件或人机流程 | `SKILL.md`、必要时更新 `user-flow.md`。 |
| 调整推荐档位或分层门槛 | `references/scoring-rubric.md`、`scripts/score_candidates.py`、`scripts/test_score_candidates.py`。 |
| 调整评分器字段 | `scripts/score_candidates.py`、测试、必要时补充示例或 schema 文档。 |
| 调整安全边界 | `SKILL.md`、`security-privacy.md`。 |
| 调整 UI 展示名或默认提示 | `agents/openai.yaml`。 |

## 验收指引

- 在 `travel-research-maps/scripts/` 下运行 `python3 -m unittest test_score_candidates.py`。
- 若修改 `SKILL.md`，按仓库 `AGENTS.md` 中的 quick validate 命令验证 skill 元数据。
- 人工审阅 `SKILL.md` 是否仍明确禁止未批准的 Google Maps 写入。

## 待确认

- 是否需要显式校验证据项必需字段，而不是用缺省和排除计数处理。
