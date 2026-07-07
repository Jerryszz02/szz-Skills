# non-gpt-subagent-worker 技术设计

## 文档目的

把正式 plan 转成可实现的文件结构、脚本接口和行为边界，避免实现时重新决策。

## 适用范围

适用于 `/Users/jerryszz/Desktop/Projects/szzSkills` 中新增的 `non-gpt-subagent-worker/` skill。非目标是修改 Codex 原生 `spawn_agent`、全局 provider 配置或用户凭据。

## Plan 或项目证据

- 仓库要求每个 skill 使用顶层目录，必须有 `SKILL.md`，可选 `agents/openai.yaml`、`scripts/`、`references/`。
- 用户计划指定支持 `ollama`、`lmstudio`、`deepseek`，并要求默认 worker 可写但不得使用无限制权限。
- 本机 Codex CLI 支持 `codex exec --oss --local-provider lmstudio|ollama`；DeepSeek 当前不应假设已有全局 provider 配置。

## 实现指引

- `SKILL.md` 负责触发条件、provider 选择、委派边界和主 agent 审查要求。
- `references/worker-contract.md` 定义 worker prompt 契约，避免把长规则放进 `SKILL.md`。
- `scripts/run-worker.sh` 是统一入口，根据 provider 调用具体脚本。
- Ollama 和 LM Studio 脚本通过 `codex exec --oss --local-provider <provider>` 执行，使用 `--sandbox read-only|workspace-write`，禁止 `danger-full-access`。
- DeepSeek 脚本通过 OpenAI-compatible chat endpoint 调用，只作为文本 worker，不假设能读取仓库。
- `scripts/run-parallel-workers.sh` 读取 JSON 数组，为每个任务生成 task/result/stdout/stderr 文件，并输出 `summary.json`。
- `scripts/worker_routing.py` 放确定性路由逻辑，供测试覆盖 provider alias、sandbox 和命令形状。

## 验收标准

- `quick_validate.py` 通过新 skill。
- `python3 -m unittest test_worker_routing.py` 通过。
- `run-worker.sh` 的 Ollama、LM Studio、DeepSeek dry-run 都能输出不含 secret 的路由信息。
- DeepSeek 在缺少 `DEEPSEEK_API_KEY` 时清晰失败。
- README skill 速览包含新 skill。

## 待确认

- 用户后续是否要把仓库 copy 同步安装到 `~/.codex/skills/`。
