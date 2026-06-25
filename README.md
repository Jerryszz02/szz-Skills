# szz-Skills

这个仓库用于保存和同步个人 Codex skills。

## Skills

### article-summary

按原文顺序总结文章、网页、PDF、Word 文档或纯文本，并为每个核心观点标注对应原文位置。默认输出包含核心观点、原文段落摘译、全文概括总结和校对说明。

路径：

```text
skills/article-summary/
```

### travel-research-maps

为指定目的地研究景点和餐厅，基于近一年独立旅行内容做候选收集、评分和事实核验。默认输出中文审核清单；只有在明确批准后，才会把已核验地点保存到 Google Maps 列表。

路径：

```text
skills/travel-research-maps/
```

## Repository Structure

```text
.
├── README.md
└── skills/
    ├── article-summary/
    │   ├── SKILL.md
    │   └── agents/
    └── travel-research-maps/
        ├── SKILL.md
        ├── agents/
        ├── references/
        └── scripts/
```

## Install Locally

在 Windows PowerShell 中运行：

```powershell
Copy-Item -Recurse .\skills\article-summary "$env:USERPROFILE\.codex\skills\article-summary"
Copy-Item -Recurse .\skills\travel-research-maps "$env:USERPROFILE\.codex\skills\travel-research-maps"
```

如果目标目录已存在，先确认本地是否有未提交改动，再决定是否覆盖。

## Notes

- 本仓库只包含 skill 指令、公开脚本和本地 agent 展示配置。
- 不包含 API key、token、Cookie、账号密码或其他凭据。
- `travel-research-maps` 的地图写入是外部副作用，必须在用户明确批准后执行。
