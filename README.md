# szz-Skills

这个仓库用于保存和同步个人 Codex skills。每个顶层目录对应一个可复制到 `~/.agents/skills/<skill-name>/` 的 skill。

## Skill 速览

| Skill | 状态 | 主要用途 | 典型触发 |
| --- | --- | --- | --- |
| `article-summary` | 可用 | 按原文顺序总结文章、网页、PDF、Word 文档或纯文本，并标注来源位置 | “总结一下这篇文章”“这个链接讲了什么”“帮我概括这个 PDF” |
| `travel-research-maps` | 可用 | 用 Keyless Firecrawl、浏览器与电脑控制研究景点或餐厅，生成审核清单，并在批准后保存到 Google Maps | “研究京都景点”“推荐成都餐厅”“把审核清单加入地图列表” |
| `plan-project-docs` | 可用 | 将已完成 plan 或现有项目证据整理为最小必要的 `docs/planning/` 项目指导文档 | “把这个计划存到项目文件夹”“根据现有项目生成项目文档” |
| `product-demand-discovery` | 可用 | 用 Firecrawl 公开互联网证据发现产品机会、评分、去重并保存研究报告 | “发现某领域的产品机会”“找有需求但竞品不拥挤的方向” |
| `subagent-orchestrator` | 可用 | 主模型规划验收，DeepSeek 优先执行，Luna 集成检查，并汇总任务用量 | “拆分这个复杂任务”“调用 subagent 前先评估”“用 DeepSeek worker 实现” |

## How This Repository Works

这个仓库本身不是运行时服务，也不保存 Codex 的全局 skill 注册表。它是个人 skill 的源代码仓库：每个顶层目录是一份可独立安装的 skill，目录名就是安装到本地 Codex 时使用的 skill 名称。

一次完整维护通常分为四步：

1. 在对应 skill 目录里修改 `SKILL.md`、`references/`、`scripts/` 或 `agents/openai.yaml`。
2. 用 `quick_validate.py` 校验被修改的 skill 目录。
3. 运行 `scripts/sync-installed-skills.sh`，把仓库中的 skill 同步到 `~/.agents/skills/`。
4. 重启 Codex，让 skill registry 重新加载本地目录。

本仓库中的文件按职责分工：

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 给 Codex agent 的仓库维护规则，包括校验命令、编辑边界和本地安装约定。 |
| `README.md` | 给第一次接触仓库的人看的入口文档，说明有哪些 skill、如何使用、如何安装和验证。 |
| `<skill-name>/SKILL.md` | skill 的触发条件、工作流和安全边界；YAML frontmatter 只包含 `name` 和 `description`。 |
| `<skill-name>/references/` | 放较长、可复用、按需读取的规则和背景资料，避免 `SKILL.md` 过长。 |
| `<skill-name>/scripts/` | 放确定性辅助脚本和对应测试；只有需要代码辅助时才存在。 |
| `<skill-name>/agents/openai.yaml` | Codex UI 展示元数据；`interface.default_prompt` 应明确提到 `$skill-name`。 |

同步脚本只处理仓库中已有的顶层 skill，不会把安装目录中的其它 skill 反向加入仓库；可通过第一个参数指定其它安装根目录。

## article-summary

路径：`article-summary/`

### 功能

`article-summary` 用于对用户提供的文章、网页、PDF、Word 文档或纯文本做可核对的中文总结。它不会只给泛泛摘要，而是按原文出现顺序提炼 5-12 个核心观点，并为每个观点标注 `对应原文位置`，例如章节标题、链接锚点、页码或段落标识。

默认输出包含：

- `核心观点`：保留原文叙事顺序，不改写成主题分类。
- `对应原文位置`：让用户能回到原文核对。
- `原文段落摘译`：用中文忠实转述关键段落，不大段复制原文。
- `全文概括总结`：用一小段说明文章中心论点、机制和结论。
- `校对说明`：指出已修正或保留的限制条件、歧义和风险。

### 怎么用

直接在 Codex 里提供链接、文件或正文，并明确要总结即可：

```text
使用 $article-summary 总结这个链接，并标注对应原文位置：https://example.com/article
```

```text
使用 $article-summary 帮我总结这个 PDF，按原文顺序列核心观点。
```

```text
使用 $article-summary 概括下面这段文字，保留校对说明：...
```

### 边界

- 必须先读取真实原文；遇到登录、验证码、付费墙或缺附件时，会要求用户补充来源，不会用搜索摘要补齐。
- 会区分公告、预览、已发布、未来计划、报告数据和独立验证结果。
- 只有用户明确要求导出、生成、保存 PDF 或文档时，才会创建 PDF。

## travel-research-maps

路径：`travel-research-maps/`

### 功能

`travel-research-maps` 用于研究指定目的地的景点和餐厅，产出可审核的中文地点清单。它不是按天行程生成器，不默认安排“第几天去哪里”；重点是收集近期、多平台、非广告的旅行证据，筛选值得去的地点，并把风险和待确认事项暴露出来。

它的完整流程包括：

- 从请求中提取目的地和旅行日期；未提供日期时标记为“计划前往日期未知”。
- 优先使用无需 API Key 的 Firecrawl Keyless；再用浏览器控制与电脑控制读取公开旅行内容，不使用 Firecrawl MCP。
- 中国大陆目的地优先小红书和 Bilibili；境外目的地优先小红书、YouTube、Instagram 和公开旅行内容。
- 只研究用户请求的类别：景点至少浏览 10 篇相关内容并形成 10 个不同候选；餐厅至少浏览 10 篇相关内容并形成 5 个不同候选。请求两类时均须达标，只问一类时不要求另一类覆盖。
- 排除广告、赞助、探店邀约、优惠码、返佣链接、店方账号和官方旅游机构账号。
- 用 `scripts/score_candidates.py` 做确定性去重、计分和分层。
- 对“优先去”和“备选”地点核验门票、预约、营业时间、关闭风险和地址匹配。
- 先输出审核清单；只有用户明确批准后，才会写入 Google Maps 列表。

### 怎么用

基础研究：

```text
使用 $travel-research-maps 研究一下 2026 年 10 月去京都值得去的景点和餐厅。
```

只要审核清单，不写地图：

```text
使用 $travel-research-maps 看一下成都最近一年被反复推荐的景点和餐厅，先不要写入 Google Maps。
```

审核后写入地图：

```text
把“优先去”都加入 Google Maps，排除 A 和 B，使用列表“京都 2026”。
```

### 输出

只输出请求中的类别；请求两类时分“景点”和“餐厅”两组，每项包含：

- 地点名称、开放/营业、预约状态；
- 一句话介绍；
- 门票、最后入场、闭馆日、菜系、招牌、预算、地址或街区等必要信息；
- 官网或订位渠道、多平台证据、净分、独立正向来源数、正向平台；
- 信息可信度和待确认事项。

### 边界

- Firecrawl Keyless 配额不足或不可用时，继续使用浏览器和电脑控制；三条路径都无法取得公开正文时报告覆盖缺口，不把普通 web-search 摘要当作等价证据。
- Google Maps 评论不直接计入推荐分，只用于地址、营业状态、地点匹配和风险核验。
- 地图写入是外部副作用，必须先拿到用户对审核清单和目标列表的明确批准。
- 不读取 Cookie、密码或浏览器会话数据；如果用户未登录 Google Maps，只保留审核清单并说明阻塞。

### 本地脚本

评分器位于 `travel-research-maps/scripts/score_candidates.py`。典型调用：

```bash
python scripts/score_candidates.py \
  --input evidence.json \
  --output scored.json \
  --as-of YYYY-MM-DD \
  --min-positive-platforms-for-priority 2
```

回归测试从脚本目录运行：

```bash
cd travel-research-maps/scripts
python3 -m unittest test_score_candidates.py
```

## plan-project-docs

路径：`plan-project-docs/`

### 功能

`plan-project-docs` 用于把已经完成的正式 plan、即将执行的正式 plan，或一个现有项目的真实仓库证据，整理成后续开发可引用的 `docs/planning/` 文档。它的目标不是生成一整套模板，而是选择最小必要文档集合，避免文档膨胀。

它支持三种模式：

- Plan 归档模式：Codex 已经为大型工程、主要功能、架构调整或产品方向产出正式 plan，用户要求保存计划、生成 PRD 类文档或实现前准备项目指导文档。
- 执行前准备模式：用户要求执行一个正式 plan 时，在开始修改产品代码、测试、配置或项目文档之前，先生成或更新 `docs/planning/`。
- 现有项目梳理模式：用户明确要求为一个已经存在且缺少相关规划文档的项目生成 `docs/planning/`。

### 怎么用

保存刚完成的 plan：

```text
使用 $plan-project-docs 先把这个计划存到项目文件夹作为项目指导文档，然后继续执行。
```

为现有项目补文档：

```text
使用 $plan-project-docs 根据当前项目的真实代码和 README，生成最小必要的 docs/planning 项目文档。
```

### 输出

每次都会创建或更新：

- `docs/planning/README.md`：索引、生成时间、已检查证据、已生成/跳过文档、待确认项。

按需创建或更新：

- `prd.md`：产品行为、用户场景、需求和验收标准。
- `technical-design.md`：实现方案、受影响子系统、状态流、错误处理和任务拆分。
- `security-privacy.md`：敏感数据、权限、secrets、信任边界和剩余风险。
- `test-plan.md`：单元、集成、E2E、人工、安全或性能验证。
- `api-design.md`、`database-design.md`、`release-plan.md`、`operations-runbook.md` 等仅在项目证据或 plan 确实需要时生成。

### 选择规则

- 默认从 `README.md` 加 1-3 篇核心文档开始判断。
- 先合并后拆分：背景和用户流程优先并入 `prd.md`；架构边界、实现契约和关键决策优先并入 `technical-design.md`。
- 没有 API 改动时不生成 `api-design.md`；没有持久化改动时不生成 `database-design.md`；没有部署或发布事项时不生成 `release-plan.md`。
- 现有项目模式必须先读取真实证据，例如 `README*`、`AGENTS.md`、已有 `docs/`、包管理清单、构建清单、路由/API/schema 文件和应用入口。
- 缺证据的信息写 `待确认`，不编造 API、schema、部署目标、时间线或负责人。

### 边界

- 默认只写目标项目的 `docs/planning/`。
- 不修改产品代码、测试、配置、依赖清单、部署文件、`.env` 或 secrets。
- 如果已有同类 planning 文档，会优先更新索引或合并信息，不重复生成一套。

## subagent-orchestrator

路径：`subagent-orchestrator/`

### 功能

`subagent-orchestrator` 让主模型（选用 GPT-6 时即 GPT-6）默认负责需求、规划、关键决策和最终验收，保留微小任务直做及失败接管。查代码、收集证据、实现、测试、常规修复和文档按以下顺序委派：

- DeepSeek：通过已配置的 `dsh --profile headless`，在 detached Git worktree 中执行。
- Kimi Code：DeepSeek 不可用或失败时的第二选择，同样在 detached worktree 中执行。
- Luna：外部 worker 都不能使用时的首个原生选择；显式指定模型和推理强度。
- Terra：最后一个 worker 回退；显式指定模型和推理强度。

集成操作和最终组合工作区检查单独使用 **Luna → Terra → 主 Agent**。这基于原生 worker 能访问当前工作区的条件；外部 runner 仅从已提交的 HEAD 启动，不能验证尚未提交的集成结果。主 Agent 先审查并授权具体 patch，worker 再串行应用并检查，语义冲突和验收结论仍由主 Agent 决定。

默认每个切片最多 3 次执行、每项用户任务共享最多 2 次恢复尝试，同一路线最多定向重试 1 次；达到任一上限后由主 Agent 接管。闸门检查失败且模型未启动不计执行，执行后失败和缺失用量必须记账。这些是主 Agent 的编排规则，单次 runner 不会自动强制跨 worker 预算。

不会使用 Sol worker。只有根/主 Agent 可以调用 `spawn_agent`；每份 task packet 都明确禁止 worker 再委派。原生 spawn 前必须检查当前剩余并发位，且调用中必须填写 `model`、`reasoning_effort` 和 `fork_turns: "none"`。

### 怎么用

DeepSeek worker：

```bash
subagent-orchestrator/scripts/run-dsh-worker.sh \
  --cwd /Users/jerryszz/Desktop/Projects/example \
  --task-file /tmp/worker-task.md \
  --output-dir /tmp/deepseek-worker-artifacts
```

Kimi fallback：

```bash
subagent-orchestrator/scripts/run-kimi-worker.sh \
  --cwd /Users/jerryszz/Desktop/Projects/example \
  --task-file /tmp/worker-task.md \
  --output-dir /tmp/kimi-worker-artifacts
```

### 边界

- 委派必须有界、可验证；存在依赖时可以串行委派。架构、安全判断、语义冲突和最终验收留在主 Agent；外部 worker 继续排除认证、支付、迁移和破坏性操作。
- DeepSeek 与 Kimi worktree 只是 Git 冲突隔离，不是操作系统安全沙箱，不得传递 secrets、Cookie、私钥、`.env` 值或私密会话。
- runner 不创建分支或 commit，也不自动应用 patch。主 Agent 必须检查 manifest、scope、实际 diff 和验证结果。
- 如果允许路径存在主工作区未提交改动，外部 runner 会拒绝启动；无关脏文件不会阻止执行。
- 每个 worker 都必须提供统一 `worker-receipt.json`/回执，记录任务、实际模型、推理档位、fork 范围、状态和 token。Kimi manifest 从本地 session runtime 读取真实模型与累计 usage；缺少这些证据时不会把请求模型冒充为实际模型。

### 验证与用量

离线回归检查（不调用模型）及真实任务对照方法见 [用量与验证指南](subagent-orchestrator/references/usage-evaluation.md)。主/native 用量和任务 manifest 需按运行时证据记录；工具不会自动从账户额度推算 token。

```bash
python3 -m unittest discover -s subagent-orchestrator/scripts -p 'test_*.py' -v
python3 subagent-orchestrator/scripts/summarize_usage.py --run /tmp/run.json --output /tmp/usage-summary.json
```

汇总区分主模型、worker（含集成和失败重试）与总 token。缺失数据返回 `null`，不会当作零；已知小计不能冒充总量。离线测试验证 runner 边界与记账逻辑，模拟任务检查路由选择；是否节省用量需要在相同任务与验收条件下做对照。

## product-demand-discovery

路径：`product-demand-discovery/`

### 功能

`product-demand-discovery` 用于通过公开互联网信息发现产品机会，重点找出真实用户痛点、可量化市场空间和竞品密度不高的方向。优先使用宿主可用的 Firecrawl；缺失或读取失败时，使用已有的网页搜索、页面读取或浏览器能力继续核验。只有读到正文的页面才计入证据，工具降级不降低评分门槛。

默认输入缺失时，它会使用以下研究范围：

- 目标领域：互联网软件与 AI 工具。
- 地区：全球。
- 语言：中文和英文。
- 目标用户：独立开发者到小团队可执行机会。
- 市场目标：轻量 SaaS、插件、自动化工具或垂直工作流产品。

核心流程包括：

- 发现当前可用工具，按痛点、竞品与市场三个方向搜索和读取公开正文；不把搜索结果摘要当作已读证据。
- 优先采集高质量需求证据，例如 Reddit、Hacker News、V2EX、知乎、小红书、垂直论坛、G2、Capterra、App Store、Google Play、Chrome Web Store、GitHub issues、Discussions 和 Stack Overflow。
- 用 Google Trends、Keyword Planner、Product Hunt、招聘网站、行业报告、年报和竞品案例辅助判断趋势和市场规模。
- 排除明显广告、赞助、品牌账号、SEO 聚合页、affiliate 内容和重复转载。
- 按 Demand Score、Market Score、Gap Score 计算 Overall Score。
- 将候选分为“推荐”“观察”“淘汰”。
- 默认把研究保存到当前工作目录的 `outputs/product-demand-discovery/`，并维护 `index.json`；用户指定目录时采用该目录，只要对话结果时不写文件。

### 怎么用

```text
使用 $product-demand-discovery 搜索公开互联网信息，发现 AI agent 工具领域里有市场空间且竞品不拥挤的产品机会。
```

```text
使用 $product-demand-discovery 研究独立开发者工具方向，找出至少 3 个可验证的产品需求机会。
```

### 输出

默认写入当前工作目录；用户指定目录或明确不保存时遵循其要求：

```text
outputs/product-demand-discovery/
├── YYYY-MM-DD-<topic-slug>.md
└── index.json
```

Markdown 报告应包含：

- 研究范围：领域、地区、语言、目标用户、日期；
- 数据覆盖：搜索次数、读取页面数、来源类型、覆盖缺口；
- 推荐机会、观察机会、淘汰机会；
- 每个机会的目标用户、核心痛点、当前替代方案、竞品密度、市场估算、评分、关键证据、风险、下一步验证实验和历史去重状态。

### 评分门槛

候选机会计划至少满足：

- 至少 8 条独立痛点证据；
- 证据来自至少 3 类来源；
- 能定义目标用户、触发场景、当前替代方案和付费方；
- 直接同类产品不超过 5 个；6-10 个时必须证明竞品差评集中在同一未满足缺口；超过 10 个默认淘汰；
- Overall Score 不低于 70。

### 待补齐

- 是否需要独立脚本来生成报告和维护 `index.json`：待确认，目前由 skill 工作流要求 agent 直接写入。
- 是否为不同研究主题提供固定报告模板或示例输出：待确认，当前只定义了输出 schema。

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
├── subagent-orchestrator/
│   ├── SKILL.md
│   ├── agents/
│   ├── references/
│   └── scripts/
├── product-demand-discovery/
│   ├── SKILL.md
│   ├── agents/
│   └── references/
└── travel-research-maps/
    ├── SKILL.md
    ├── agents/
    ├── docs/
    ├── references/
    └── scripts/
```

## Install Locally

以下命令安装本仓库当前全部 5 个 skill。安装或更新后需要重启 Codex。

macOS / Linux:

```bash
./scripts/sync-installed-skills.sh
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\article-summary "$env:USERPROFILE\.agents\skills\article-summary"
Copy-Item -Recurse -Force .\plan-project-docs "$env:USERPROFILE\.agents\skills\plan-project-docs"
Copy-Item -Recurse -Force .\subagent-orchestrator "$env:USERPROFILE\.agents\skills\subagent-orchestrator"
Copy-Item -Recurse -Force .\product-demand-discovery "$env:USERPROFILE\.agents\skills\product-demand-discovery"
Copy-Item -Recurse -Force .\travel-research-maps "$env:USERPROFILE\.agents\skills\travel-research-maps"
```

这些命令会让目标目录与仓库版本一致，并删除目标目录里仓库不存在的旧文件。仓库 skill 发生更新时，维护规则要求在校验和交付前重新运行同步脚本。安装或更新后重启 Codex，让 skill 注册表重新加载。同步单个 skill 时使用同一模式：

```bash
rsync -a --delete --exclude .DS_Store ./<skill-name>/ ~/.agents/skills/<skill-name>/
```

## Validate Skills

更新 skill 内容后，使用项目约定的校验命令检查对应目录：

```bash
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/<skill-name>
```

如果这个缓存的 `PyYAML` 路径不可用，使用任意已安装 `PyYAML` 的 Python 环境运行同一个 `quick_validate.py`。README 文档改动本身不需要运行 skill 校验；修改 `SKILL.md`、`agents/openai.yaml`、脚本或引用资料时应运行。

## Notes

- 本仓库只包含 skill 指令、公开脚本和本地 agent 展示配置。
- 不包含 API key、token、Cookie、账号密码或其他凭据。
- 每个可用 skill 的 `SKILL.md` frontmatter 只应包含 `name` 和 `description`。
- `agents/openai.yaml` 用于 Codex UI 展示；`interface.default_prompt` 应明确提到对应 `$skill-name`。
- `travel-research-maps` 的地图写入是外部副作用，必须在用户明确批准后执行。
