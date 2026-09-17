# subagent-orchestrator 安全与隐私说明

## 适用范围

覆盖 DeepSeek Harness、Kimi Code、原生 Spark/Luna/Terra worker 的任务委派、文件修改、凭据和验收边界。

## 安全边界

- DeepSeek 与 Kimi 的 detached worktree 只隔离 Git 修改冲突，不是操作系统安全沙箱。
- 不向 worker 发送 secrets、token、Cookie、私钥、`.env` 值、私密登录态或账户访问任务。
- 认证、支付、安全结论、迁移、破坏性 Git、架构决定、集成和最终验收由主 Agent 负责。
- 外部 worker 只能修改 task packet 的允许路径；允许路径上的主工作区未提交改动会阻止启动。
- runner 不自动应用 patch。主 Agent 必须检查 manifest、scope、status、patch 和实际验证结果。确定性 helper 只有在显式绑定审过的 SHA-256、HEAD、任务 scope 并传入 `--apply` 后写入；普通文本范围之外的补丁返回主 Agent。
- helper 从已校验的同一份字节解析/应用 patch，拒绝软链接、越界和重叠 staged/unstaged/untracked/ignored 数据，保留无关修改；不执行 patch 内命令、不改 index、不做自动回滚。主 Agent 必须串行协调写入，helper 不提供跨进程锁。
- 只有根/主 Agent 可以调用 `spawn_agent`；所有 worker 的 task packet 都必须显式禁止嵌套委派。
- 原生 spawn 前检查实时并发余量；没有空位时不通过失败调用探测容量。

## 凭据处理

- runner 不读取、打印或保存 DSH/Kimi 的凭据配置；它只调用用户已配置的 CLI profile。
- DSH runner 仅将 `--dump-config` 通过管道提取有效 `model` 字段；不保存、打印或写入完整配置。
- DSH 的 reasoning stream 保存于指定 artifact 目录，可能包含任务上下文；该目录必须位于仓库外并按敏感工作产物处理。
- receipt 只从 session 数据抽取模型、推理档位、token 和 session 路径，不复制 prompt、完整 wire 内容或凭据。

## 剩余风险

- 外部 CLI 继承用户进程环境，worktree 无法阻止进程访问仓库外文件，因此敏感任务必须留在主 Agent。
- 新门槛及等待规则属于指令，不会修改 runtime，也不能覆盖既有全局强制委派要求。安装同步不改全局 AGENTS.md。
- Skill 是行为契约，不是 runtime 级强制拦截器；未加载或不遵循此 Skill 的 Agent 仍可能绕过闸门。
- 第三方模型与服务的数据保留政策不由本仓库控制。
