---
name: plan-project-docs
description: "用户要求创建、审计或同步 docs/planning，归档或执行已认可的正式 plan 时使用；执行 plan 时先准备 planning 文档。依据当前项目证据核对状态；README 与开发者指南仅在请求范围包含时处理。"
---

# Plan Project Docs

把已认可的正式 plan 或本次核实的项目证据转换为可维护的 `docs/planning/` 文档。planning 保留目标、设计和需求基线；当前实现以本次代码证据为准。不要把 plan、旧文档或历史验收当作当前实现、测试或部署事实。

## 按任务读取

- **执行已认可的正式 plan**：即使用户未提及 `docs/planning/`，也先按 [planning-workflow.md](references/planning-workflow.md) 创建或更新 planning 文档，再继续执行原任务。
- **创建、更新或审计 planning 文档**：读 [planning-workflow.md](references/planning-workflow.md)。需选择或重新评估文档集合时，读 [document-catalog.md](references/document-catalog.md)。已有 `docs/planning/` 时按状态同步处理。
- **更新或审计已有文档，或涉及测试、发布、运行状态**：读 [state-consistency.md](references/state-consistency.md)，核对证据、状态词、历史记录和跨文档冲突。状态变化后重新评估曾跳过的文档。
- **范围明确包含根 README 或 `docs/` 下开发者指南**：读 [repository-docs.md](references/repository-docs.md)；开发者指南的适用判断另见 document-catalog 的「仓库级配套文档」。仅因 planning 需要互链，不要创建或修改范围外文档。
- **只需检查 planning 索引与本地链接**：运行 `python3 "<skill-dir>/scripts/audit_planning_docs.py" --root "<project-root>"`；`<skill-dir>` 是本 `SKILL.md` 所在的安装目录绝对路径，`<project-root>` 是待检查项目的绝对路径。脚本不能证明语义状态正确。

如果既无具体 plan，也无明确的项目文档创建、同步或审计请求，先请用户明确目标，不自行扩大任务。

## 始终遵守

- 当前状态在本次任务中验证，记录日期与证据；无法验证写 `待确认`，带日期的旧事实必须标为历史。实现、验证、部署分别表述；新证据推翻旧状态时修正旧内容，不仅在末尾追加说明。
- 新增、删除、重命名或实质更新 planning 文档时，同步 `docs/planning/README.md`；已有同用途文档优先更新或链接，避免复制。保留仍准确的人工内容。
- 根 README 面向首次访问者，planning 描述设计目标，开发者指南描述代码现状；只处理本次授权范围内的文档。
- 先检查工作区改动，保护现有内容。默认只修改目标项目的 `docs/planning/`；不改产品代码、测试、配置、依赖、部署文件、secrets 或 `.env`。不得写入 secret、token、私钥、Cookie 或环境变量值。
- 用户使用中文时默认写中文；技术名、路径、API 和命令保持原样。缺少证据时列具体待确认问题，不编造功能、schema、路由、凭据、竞品、时间线或负责人。

完成后运行最小相关检查，报告实际修改、跳过项及其理由、验证结果与仍待确认的状态。审计请求按“吻合 / 失配 / 待确认”列出证据。
