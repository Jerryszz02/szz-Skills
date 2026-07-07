# non-gpt-subagent-worker 安全与隐私说明

## 文档目的

记录新增 skill 中涉及外部模型、本地命令、文件写入和凭据处理的边界。

## 适用范围

适用于 `non-gpt-subagent-worker` 的 skill 文档、脚本和测试。非目标是管理用户全局 Codex provider、DeepSeek 账号或本地模型安装。

## Plan 或项目证据

- 用户要求支持 Ollama、LM Studio 和 DeepSeek。
- 计划要求 DeepSeek 从 `DEEPSEEK_API_KEY` 读取凭据，不把 key 写入日志。
- AGENTS 要求不得存储 secrets、tokens、private keys 或 `.env` 值。

## 安全边界

- 默认 sandbox 为 `workspace-write`，但只允许 `read-only` 和 `workspace-write` 两档。
- 脚本不得调用 `danger-full-access` 或 `--dangerously-bypass-approvals-and-sandbox`。
- worker prompt 必须要求不读取、不打印、不请求 secrets。
- DeepSeek API key 只能来自环境变量，dry-run 和错误信息不得输出 key。
- DeepSeek 直接 API 路径没有 Codex 工具，不应声称已读取仓库文件。

## 验收标准

- 测试覆盖 `danger-full-access` 被拒绝。
- 测试覆盖缺少 `DEEPSEEK_API_KEY` 时失败信息清晰。
- dry-run 输出不包含任何 secret 值。

## 待确认

- 如果未来支持更多 OpenAI-compatible provider，需要为每个 provider 明确独立的凭据环境变量和日志脱敏规则。
