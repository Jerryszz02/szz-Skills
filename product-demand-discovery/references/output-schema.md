# 输出持久化规则

每次运行结束必须把结果保存到当前工作目录下：

```text
outputs/product-demand-discovery/
├── YYYY-MM-DD-<topic-slug>.md
└── index.json
```

## Markdown 报告

报告必须包含：

- 研究范围：领域、地区、语言、目标用户、日期。
- 数据覆盖：搜索次数、读取页面数、来源类型、覆盖缺口。
- 推荐机会、观察机会、淘汰机会。
- 每个机会的目标用户、核心痛点、当前替代方案、竞品密度、市场估算、评分、关键证据、风险、下一步验证实验、历史去重状态。

## index.json

索引为 JSON 对象，建议结构：

```json
{
  "version": 1,
  "reports": [
    {
      "date": "YYYY-MM-DD",
      "topic_slug": "ai-agent-tools",
      "path": "outputs/product-demand-discovery/YYYY-MM-DD-ai-agent-tools.md",
      "region": "global",
      "target_user": "indie hackers and small teams",
      "opportunity_keys": [
        "ai-agent-tools|indie-hackers-and-small-teams|global|agent-evaluation-debugging"
      ]
    }
  ],
  "opportunities": [
    {
      "key": "ai-agent-tools|indie-hackers-and-small-teams|global|agent-evaluation-debugging",
      "first_seen": "YYYY-MM-DD",
      "last_seen": "YYYY-MM-DD",
      "latest_report": "outputs/product-demand-discovery/YYYY-MM-DD-ai-agent-tools.md",
      "status": "recommended"
    }
  ]
}
```

## 去重键

使用以下字段生成稳定 key：

```text
topic_slug + target_user + region + core_pain_cluster
```

规范化规则：

- 小写。
- 空格转 hyphen。
- 删除标点。
- 同义词尽量合并到同一 `core_pain_cluster`，例如 `agent eval`、`agent debugging` 可合并为 `agent-evaluation-debugging`。

如果候选已存在：

- 新证据明显增加时，标为“新增证据”。
- 无新增证据时，标为“历史已发现”。
- 不要把同一机会重复放入“新机会”。
