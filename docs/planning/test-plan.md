# subagent-orchestrator 测试计划

## 范围与状态

本轮验证结构化结果、移除 Kimi 后的 runner/计量回归、原生续接规则和安装一致性；不把离线通过称为节省 Token。更新日期：2026-09-18。当前状态：113 项离线自动化测试通过，7 个独立流程场景符合预期；技能格式、shell 语法、Markdown 链接、规划审计、diff 和安装副本一致性检查通过。新增结果协议以 fake CLI 覆盖 runner 行为，未以真实模型输出验证其遵从率。本地文件同步不证明 registry 已重新加载，真实节省需独立测量。

## 自动验证

先备份有差异的安装副本，再执行仓库要求的同步；不把 installed-only skill 导入源仓库。

```bash
scripts/sync-installed-skills.sh
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/subagent-orchestrator
python3 -B -m unittest discover -s subagent-orchestrator/scripts -p 'test_*.py' -v
bash -n subagent-orchestrator/scripts/run-dsh-worker.sh
git diff --check
python3 plan-project-docs/scripts/audit_planning_docs.py --root .
```

缓存 PyYAML 不可用时使用已安装且可导入 PyYAML 的 Python，不新增项目依赖。脚本测试使用临时 Git fixture 和 fake CLI，不访问真实 provider。

## 必须保持的行为

- 原有 DSH 的 profile 预检、HEAD-only、脏路径拒绝、patch 导出、scope、退出码和收据规则不退化。
- 结果报告覆盖合法/缺失/畸形/过长 JSON、失败或未执行检查、带未完成条件的假完成声明、Git 实际路径及原始输出保留；CLI 成功不补造验证结果。
- 移除 provider 专属代码时保留通用 task packet scope 测试；历史收据汇总仍按通用 schema 读取。
- 未知 usage 仍为 null；重复 response ID 不重复计数，缓存和推理输出不再次相加。
- 补丁 helper 默认 check-only，显式 apply 才写入；相同 hash 字节用于解析和应用。
- 使用真实 Git diff 复现并覆盖已有可执行文本的内容修改和删除；保留 index 与权限，新增可执行文件及两个方向的权限变更仍拒绝。
- 使用真实 SHA-256 Git 仓库验证完整 64 位 HEAD；截断或不匹配的值拒绝，原有 SHA-1 测试保留。
- helper 拒绝 hash/HEAD 不一致、越界/禁止路径、软链接、模式/二进制/重命名补丁、会改变身份的路径规范化及大小写/Unicode 别名；重叠 staged/unstaged/untracked/ignored 数据及隐藏 index 标记的路径均拒绝。
- 成功集成不改变 index，不影响无关 staged/unstaged 工作；失败不产生部分应用或自动回滚。
- 两类 helper 都不启动模型、不执行内容中的命令；最终目标工作区验证仍由主模型负责。

## 独立路由盲测

给新 evaluator 提供技能和最小场景，不提供[期望答案表](../../subagent-orchestrator/references/test-tasks.md)。只返回工作方式、模型/理由及验收，不实际执行或 dispatch。本轮核对交付前自检、双层通过即结束、具体局部缺陷续接、只读权限限制、运行中等待、环境失败、恢复耗尽和外部路线不可用。

盲测证明这次 evaluator 的规则理解，不证明所有模型始终遵循。若出现问题，只针对已观测失败修正，不无限循环评测。

## 文档与安装

核对 README、SKILL、路由、packet、全局可选模板和规划文档，不保留“两批搜索强制委派”或“机械命令必须另派代理”的冲突要求。检查触发、非触发和依赖不可用场景。全局 AGENTS.md 不自动修改；同步完成后仍需重启 Codex 加载。

## 后续真实测量

A 独立执行、B 冻结旧技能、C 新技能；固定依赖和质量标准，按任务类型重复、轮换顺序，保留失败与 C 直做结果。记录主模型请求数/平均输入、缓存/未缓存/输出、各模型及总量、返工与延迟。详见[技术设计](technical-design.md)和[试验规程](../../subagent-orchestrator/references/test-tasks.md)。本轮未授权自动启动这组付费试验。
