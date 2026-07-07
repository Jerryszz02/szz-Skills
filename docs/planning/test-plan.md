# non-gpt-subagent-worker 测试计划

## 文档目的

定义新增 skill 完成后的最小验证命令和手工场景。

## 适用范围

覆盖 `non-gpt-subagent-worker/` 的 skill 元数据、脚本路由、DeepSeek secret handling 和 README 更新。

## Plan 或项目证据

- 仓库 AGENTS 指定使用 `quick_validate.py` 校验 changed skills。
- 用户计划指定 `test_worker_routing.py`、三个 provider dry-run 和 DeepSeek 缺 key 场景。

## 验证命令

```bash
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/non-gpt-subagent-worker
```

```bash
cd /Users/jerryszz/Desktop/Projects/szzSkills/non-gpt-subagent-worker/scripts
python3 -m unittest test_worker_routing.py
```

## 手工场景

- `run-worker.sh --provider ollama ... --dry-run` 输出 `codex exec --oss --local-provider ollama`。
- `run-worker.sh --provider lmstudio ... --dry-run` 输出 `codex exec --oss --local-provider lmstudio`。
- `run-worker.sh --provider deepseek ... --dry-run` 输出 endpoint、model、cwd、sandbox、output，不输出 API key。
- 不设置 `DEEPSEEK_API_KEY` 运行 DeepSeek 非 dry-run，应以清晰错误退出。

## 待确认

- 是否要在本次实现后执行安装同步和 installed copy 差异验证。
