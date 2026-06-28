# travel-research-maps 测试计划

## 文档目的

定义 Firecrawl 多平台来源扩展后的自动化和人工验证方式，覆盖评分脚本、skill 文档、Firecrawl 流程边界和 Google Maps 写入审批。

## 适用范围

适用于 `travel-research-maps/` 下的 Python 评分脚本、测试、skill 指令、评分规则和 agent 配置。本文档仅根据当前仓库可见内容整理；未在仓库中找到证据的内容均不做假设。

## Plan 或项目证据

| 证据 | 测试含义 |
| --- | --- |
| `score_candidates.py` | 可用 unittest 覆盖离线评分逻辑。 |
| `test_score_candidates.py` | 当前回归测试覆盖分层、过滤、去重、严重风险和平台门槛。 |
| `SKILL.md` | Firecrawl 和 Google Maps 流程需要人工审阅。 |
| `AGENTS.md` | 修改 skill 后需要运行 quick validate。 |

## 自动化检查

评分器单测：

```bash
cd /Users/jerryszz/Desktop/Projects/szzSkills/travel-research-maps/scripts
python3 -m unittest test_score_candidates.py
```

Skill 元数据验证：

```bash
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/travel-research-maps
```

## 回归场景

| 场景 | 验收 |
| --- | --- |
| 景点达到正向来源、净分和 2 个正向平台门槛 | 结果为 `priority`。 |
| 餐厅单平台高分但要求 2 个平台 | 结果降为 `backup`。 |
| Google Maps 核验产生严重风险 | `hard_risks` 直接排除。 |
| 相同内容指纹跨平台转载 | 只计一个独立来源。 |
| 营销、过期、未知日期证据 | 不计入有效证据。 |

## 人工审阅

- `SKILL.md` 明确优先使用 Firecrawl，不再要求 Chrome 小红书。
- 每次处理 Firecrawl search 结果后需要调用 `firecrawl_search_feedback`。
- Google Maps 写入仍必须等用户批准。
- 覆盖不足时仍只报告缺口，不输出伪完整清单。
- 文档中不包含 API key、Cookie、token 或账号凭据。

## 未覆盖风险

- Firecrawl 对各平台的真实抓取质量无法由本地 unittest 覆盖。
- Google Maps UI 变化、列表写入失败和地点匹配歧义未由自动化测试覆盖。
- 平台登录墙、验证码、付费墙或反爬限制需要真实任务中记录。

## 待确认

- 是否需要未来补一个本地 fixture，用静态 `evidence.json` 演示多平台输入输出。
