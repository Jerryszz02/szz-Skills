---
name: product-demand-discovery
description: 通过 Firecrawl 自动搜索公开互联网信息，发现有真实用户痛点、可量化市场空间且竞品密度不高的产品机会。用于产品需求发现、创业方向筛选、SaaS/AI 工具/Chrome extension/App/B2B 软件机会研究、竞品缺口分析、市场大小初筛，或用户要求“找产品机会”“发现未满足需求”“研究某领域还能做什么产品”。
---

# 产品需求发现

使用公开互联网证据发现产品机会。默认输出中文，结论必须可追溯到来源，不得把单个平台热度当作需求证明。

## 必需输入

先从用户请求中提取：目标领域、地区、语言、目标用户、市场目标。缺失时使用默认值：

- 目标领域：互联网软件与 AI 工具
- 地区：全球
- 语言：中文和英文
- 目标用户：独立开发者到小团队可执行机会
- 市场目标：优先寻找可做成轻量 SaaS、插件、自动化工具或垂直工作流产品的机会

若用户指定行业、地区或用户群，以用户指定范围为准。

## 工作流

1. 读取：
   - `references/source-taxonomy.md`：选择信息源和判断来源权重。
   - `references/scoring-rules.md`：量化市场、筛选候选和评分。
   - `references/output-schema.md`：保存报告和历史去重。
2. 先检查历史输出。读取当前工作目录下 `outputs/product-demand-discovery/index.json`；若不存在，继续研究并在结束时创建。对相同或相近主题，读取最近相关报告，避免重复推荐。
3. 生成搜索矩阵。至少覆盖：
   - 痛点词：`too expensive`、`I wish`、`looking for a tool`、`manual`、`spreadsheet`、`doesn't support`、`alternative to`、`switching from`、`how do I`
   - 竞品词：`best`、`alternatives`、`competitors`、`reviews`、`pricing`、`vs`
   - 市场词：`market size`、`search volume`、`trend`、`jobs`、`budget`、`workflow`
   - 中文补充：`太贵`、`有没有工具`、`替代品`、`差评`、`手动整理`、`表格管理`、`求推荐`
4. 只使用 Firecrawl MCP 获取互联网信息：
   - 使用 `mcp__firecrawl.firecrawl_search` 做跨站发现。
   - 对高价值页面使用 `mcp__firecrawl.firecrawl_scrape` 或 `mcp__firecrawl.firecrawl_extract` 抽取正文或结构化证据。
   - 当站内 URL 难定位时，少量使用 `mcp__firecrawl.firecrawl_map`。
   - 只有搜索、抓取和 map 都无法完成复杂跨站研究时，才使用 `mcp__firecrawl.firecrawl_agent`。
   - 每次处理 `mcp__firecrawl.firecrawl_search` 结果后，立即调用 `mcp__firecrawl.firecrawl_search_feedback`，标注有价值来源或缺失内容。
   - 若 Firecrawl MCP 不可用，报告阻塞原因；不得把内置 web search 当作等价替代。
5. 抽取候选需求。每条证据记录：URL、来源平台、发布时间或检索日期、作者或组织、原文摘要、痛点、当前替代方案、可见付费意图、相关竞品。
6. 合并重复需求。按 `target_user + job_to_be_done + core_pain_cluster` 聚类；同一作者、转载、营销稿或相同素材只算一个独立来源。
7. 做竞品密度检查。对每个候选至少搜索直接竞品、替代方案、评论/差评、Product Hunt 或应用商店供给情况。Product Hunt 只作为新品供给和竞品密度信号，不单独证明需求。
8. 做市场量化。默认 bottom-up，公式为：

   ```text
   年化市场机会 = 可触达客户数 × 年付费金额 × 年购买频次 × 可转化比例
   ```

   可使用 TAM/SAM/SOM 表达，但不得只引用宏观市场报告作为结论。
9. 评分并筛选。入选机会必须同时满足：
   - 至少 8 条独立痛点证据，来自至少 3 类来源。
   - 能定义目标用户、触发场景、当前替代方案和付费方。
   - 直接同类产品不超过 5 个，或 6-10 个但有清晰竞品缺口；超过 10 个默认淘汰。
   - `Overall Score >= 70`，且 Demand、Market、Gap 三项均不低于各自阈值。
10. 保存输出。每次运行结束必须写入当前工作目录：
    - Markdown 报告：`outputs/product-demand-discovery/YYYY-MM-DD-<topic-slug>.md`
    - 机器可读索引：`outputs/product-demand-discovery/index.json`
    - 对历史已发现机会，标注“历史已发现”或“新增证据”，不要作为全新机会重复推荐。

## 输出格式

先给结论，再列证据。每个产品机会使用固定结构：

```markdown
## 产品机会：名称

- 目标用户：
- 核心痛点：
- 当前替代方案：
- 为什么现有产品没解决：
- 直接竞品数量：
- 市场估算：
- 评分：Demand / Market / Gap / Overall
- 关键证据：
- 主要风险：
- 下一步验证实验：
- 历史去重状态：
```

将候选分为：

- `推荐`：达到入选阈值，证据较强。
- `观察`：痛点存在，但市场、竞品或付费意图证据不足。
- `淘汰`：市场太小、竞品拥挤、痛点弱或证据不可审计。

## 边界

- 不绕过登录墙、验证码、付费墙、地区限制或反爬机制。
- 不读取或要求 Cookie、账号密码、私有 API key、付费数据库或浏览器隐私数据。
- 不把榜单排名、点赞、媒体曝光、融资新闻、Product Hunt 票数当作独立需求证明。
- 找不到足够证据时，输出覆盖缺口和下一步验证建议，不强行给机会结论。

## 资源

- `references/source-taxonomy.md`：信息源权重、适用场景和偏差。
- `references/scoring-rules.md`：入选门槛、市场量化和评分规则。
- `references/output-schema.md`：报告保存、索引字段和去重键。
