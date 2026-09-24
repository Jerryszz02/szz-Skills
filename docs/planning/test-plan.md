# subagent-orchestrator 测试计划

## 范围与状态

本轮验证串行委派指令修订：单 worker 串行与 fan-out 拒绝、灵活多角色与完整问题/结果、最小上下文、首次交付前的停止规则、同 owner 增量续接、重复环境故障停止、原生 runtime 不兼容、隐式非触发和评估优先级；不把离线通过称为节省 Token。更新日期：2026-09-24。

当前状态：2026-09-24 在集成后的独立工作区运行 113 项离线回归，全部通过；技能格式、shell 语法、Markdown 链接、规划审计、diff 与 5 个源/安装副本一致性检查通过。新增的串行与灵活角色、默认直接执行、交接成本及证据时效场景已做静态核对；本轮未启动独立模型盲测或 A/B，不把场景清单等同于模型遵从率。后续仅文档调整复用未变更脚本的回归结果，并刷新格式、链接与安装检查。重启 Codex 后才重新加载技能注册表，真实节省仍需独立测量。

## 自动验证

先备份安装副本。worker 在 scratch 安装根自检；主模型审查并集成后，再运行同步脚本更新真实 `~/.agents/skills` 并核对所有仓库 skill 的一致性。不把 installed-only skill 导入源仓库。

```bash
scripts/sync-installed-skills.sh
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$PWD/subagent-orchestrator"
python3 -B -m unittest discover -s subagent-orchestrator/scripts -p 'test_*.py'
bash -n subagent-orchestrator/scripts/run-dsh-worker.sh
git diff --check
python3 plan-project-docs/scripts/audit_planning_docs.py --root .
```

技能格式校验使用已安装且可导入 PyYAML 的 Python 环境，不新增项目依赖。脚本测试使用临时 Git fixture 和 fake CLI，不访问真实 provider。

## 必须保持的行为

- 原有 DSH 的 profile 预检、HEAD-only、脏路径拒绝、patch 导出、scope、退出码和收据规则不退化；本轮只更新 runner 的注入指令文本。
- runner 注入文本包含单 owner、最小上下文和停止规则；不改变 parser/scope/receipt/cleanup/security 行为。
- 结果报告覆盖合法/缺失/畸形/过长 JSON、失败或未执行检查、带未完成条件的假完成声明、Git 实际路径及原始输出保留；CLI 成功不补造验证结果。
- 未知 usage 仍为 null；重复 response ID 不重复计数，缓存和推理输出不再次相加。
- 补丁 helper 默认 check-only，显式 apply 才写入；相同 hash 字节用于解析和应用；拒绝条件与不变式保持。
- 已有可执行文本的内容修改和删除、完整 64 位 HEAD、越界/禁止路径、软链接、模式/二进制/重命名、重叠数据均按原规则处理。
- 成功集成不改变 index，不影响无关 staged/unstaged 工作；失败不产生部分应用或自动回滚。
- 两类 helper 都不启动模型、不执行内容中的命令；最终目标工作区验证仍由主模型负责。

## 后续独立路由盲测（本轮未运行）

给新 evaluator 提供技能和最小场景，不提供[期望答案表](../../subagent-orchestrator/references/test-tasks.md)。只返回工作方式、模型/理由及验收，不实际执行或 dispatch。除既有交付前自检、双层通过即结束、局部缺陷续接、只读权限、运行中等待、环境失败、恢复耗尽与外部路线不可用外，场景覆盖 serial fan-out 拒绝、灵活角色与完整阶段、最小上下文、同 owner 增量续接、通过后停止、重复环境故障停止、原生 runtime 不兼容、隐式非触发和按模型计价的成本解释。

盲测证明这次 evaluator 的规则理解，不证明所有模型始终遵循。若出现问题，只针对已观测失败修正，不无限循环评测。

## 文档与安装

核对 README、SKILL、路由、packet、全局可选模板和规划文档，不保留“两批搜索强制委派”“机械命令必须另派代理”或“空闲并发位可加派 worker”的冲突要求。检查触发、非触发和依赖不可用场景。全局 AGENTS.md 不自动修改；同步完成后仍需重启 Codex 加载。

## 后续真实测量

A 独立执行、B 冻结旧技能、C 串行委派技能；固定依赖和质量标准，按任务类型重复、轮换顺序，保留失败与 C 直做结果。先看质量门槛，再记录主模型请求数/平均输入、缓存/未缓存/输出、按模型计价的总成本、各模型及总量、返工与延迟。详见[技术设计](technical-design.md)和[试验规程](../../subagent-orchestrator/references/test-tasks.md)。本轮未授权自动启动这组付费试验。
