# subagent-orchestrator 技术设计

## 目标

把“是否委派”和“委派给谁”拆成两个顺序决策：每个准备调用 `spawn_agent` 的任务先通过 Delegation Gate；通过后按 DeepSeek、Kimi、Luna、Terra 的固定顺序选择 worker，永不使用 Sol worker。

## 调度契约

1. 根/主 Agent 识别依赖、ownership、验收命令和风险。
2. 小型、强耦合、顺序依赖、高风险或直接完成更便宜的任务不委派。
3. 外部 worker 依次尝试 DeepSeek 和 Kimi；两者均不能使用时才尝试原生 Luna、Terra。
4. 只有根/主 Agent 可以调用 `spawn_agent`。调用前通过 `list_agents` 读取实时占用，并根据当前 runtime 的并发上限计算剩余位。
5. 原生 worker 显式设置模型和推理强度；scout 使用 low，builder 使用 medium；`fork_turns` 使用 `none`，完整上下文由 task packet 提供。
6. 每份 task packet 都要求 `Nested delegation: forbidden`，禁止 worker 调用 `spawn_agent` 或继续委派。
7. 主 Agent 审查输出、diff 和验证结果，负责集成与最终验收。

## 固定 fallback

| 顺序 | Worker | 可用性与调用要求 |
| --- | --- | --- |
| 1 | DeepSeek Harness | `dsh` 可执行，`dsh --profile headless --help` 成功，任务通过外部 worker 安全边界与 runner preflight。 |
| 2 | Kimi Code | `kimi` 可执行，任务通过相同安全和 packet 边界。 |
| 3 | Luna | `model="gpt-5.6-luna"`；scout `reasoning_effort="low"`，builder `"medium"`。 |
| 4 | Terra | `model="gpt-5.6-terra"`；scout `reasoning_effort="low"`，builder `"medium"`。 |

原生 spawn 同时设置 `fork_turns="none"`。如果没有剩余并发位，不调用 `spawn_agent`，而是等待、排队或由主 Agent 完成。

## 外部 runner

`run-dsh-worker.sh` 和 `run-kimi-worker.sh` 接受绝对 `--cwd`、`--task-file` 和仓库外空 `--output-dir`。两者均：

- 校验 task packet 必需章节、HEAD-only 声明、嵌套委派禁令和允许/禁止路径；
- 拒绝与主工作区允许路径上的未提交改动重叠；
- 从当前 `HEAD` 创建 detached worktree；
- 保存状态、changed paths、binary patch、退出码、scope 结果和 manifest；
- 不创建 branch/commit，不自动应用 patch，完成后清理 worktree。

DeepSeek runner 额外保存 `final.txt` 和 `reasoning.log`；Kimi runner 保存 `events.jsonl` 和 `stderr.log`。

## 验收标准

- `quick_validate.py` 通过。
- DSH 与 Kimi runner 单元测试通过。
- task packet 对缺失或非 `forbidden` 的嵌套委派声明失败。
- 文档不存在 Sol worker 路由，并明确原生模型、推理强度、并发位检查和 root-only spawn。
