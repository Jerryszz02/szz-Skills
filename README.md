# szz-Skills

这个仓库用于保存和同步个人 Codex skills。

## Skills

### article-summary

按原文顺序总结文章、网页、PDF、Word 文档或纯文本，并为每个核心观点标注对应原文位置。默认输出包含核心观点、原文段落摘译、全文概括总结和校对说明。

路径：

```text
article-summary/
```

### travel-research-maps

为指定目的地研究景点和餐厅，基于近一年独立旅行内容做候选收集、评分和事实核验。默认输出中文审核清单；只有在明确批准后，才会把已核验地点保存到 Google Maps 列表。

路径：

```text
travel-research-maps/
```

### plan-project-docs

在正式 plan 完成后，或用户明确要求为缺少相关文档的现有项目生成文档时，根据 plan 内容或项目证据按需生成 `docs/planning/` 下的项目指导文档与索引。

路径：

```text
plan-project-docs/
```

## Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── article-summary/
│   ├── SKILL.md
│   └── agents/
├── plan-project-docs/
│   ├── SKILL.md
│   ├── agents/
│   └── references/
└── travel-research-maps/
    ├── SKILL.md
    ├── agents/
    ├── references/
    └── scripts/
```

## Install Locally

macOS / Linux:

```bash
mkdir -p ~/.codex/skills
cp -R ./article-summary ~/.codex/skills/article-summary
cp -R ./plan-project-docs ~/.codex/skills/plan-project-docs
cp -R ./travel-research-maps ~/.codex/skills/travel-research-maps
```

Windows PowerShell:

```powershell
Copy-Item -Recurse .\article-summary "$env:USERPROFILE\.codex\skills\article-summary"
Copy-Item -Recurse .\plan-project-docs "$env:USERPROFILE\.codex\skills\plan-project-docs"
Copy-Item -Recurse .\travel-research-maps "$env:USERPROFILE\.codex\skills\travel-research-maps"
```

如果目标目录已存在，先确认本地是否有未提交改动，再决定是否覆盖。安装或更新后重启 Codex，让 skill 注册表重新加载。

## Notes

- 本仓库只包含 skill 指令、公开脚本和本地 agent 展示配置。
- 不包含 API key、token、Cookie、账号密码或其他凭据。
- `travel-research-maps` 的地图写入是外部副作用，必须在用户明确批准后执行。
