# subagent-orchestrator 测试计划

## 自动验证

```bash
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/subagent-orchestrator
```

```bash
cd /Users/jerryszz/Desktop/Projects/szzSkills/subagent-orchestrator/scripts
python3 -m unittest test_dsh_runner.py test_kimi_runner.py
```

## 覆盖场景

- DSH headless profile preflight 成功和失败。
- DSH/Kimi detached worktree 产出 patch，但不改变主工作区。
- worker 非零退出码被保留。
- 超出允许路径的修改被 scope check 拒绝。
- 允许路径存在未提交主工作区改动时拒绝 dispatch。
- task packet 拒绝无界允许路径，并要求 `Nested delegation: forbidden`。

## Live 探针

在不含仓库和敏感数据的临时目录中运行只返回固定文本的 `dsh --profile headless` 探针，确认 profile 当前能完成单次命令。探针只证明运行时可用性，不替代 runner 的路径和 patch 测试。

## 人工核对

- `SKILL.md` 和 routing guide 都明确固定 fallback：DeepSeek、Kimi、Luna、Terra；不含 Sol worker。
- 每个原生 spawn 明确要求 `model`、`reasoning_effort` 和 `fork_turns="none"`。
- 每个原生 spawn 前要求检查当前并发位，且只有根/主 Agent 可以调用。
- README 安装命令和目录树使用 `subagent-orchestrator`。
