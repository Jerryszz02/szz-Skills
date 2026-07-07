---
name: non-gpt-subagent-worker
description: Use this skill when the user asks to open, spawn, delegate to, or parallelize sub-agents/workers and also specifies a non-OpenAI model or provider such as Ollama, LM Studio, DeepSeek, local model, cheap model, non-GPT model, or non-OpenAI worker. It wraps those models as external worker processes through scripts instead of claiming Codex native subagents can switch to non-OpenAI providers.
---

# Non-GPT Subagent Worker

Run non-OpenAI models as external worker processes for bounded Codex subtasks. This skill does not replace Codex native `spawn_agent`; it gives the main agent a controlled way to call Ollama, LM Studio, or DeepSeek workers and then review their output.

## Trigger Check

Use this skill only when both conditions are true:

- The user asks for sub-agents, subagents, workers, delegation, parallel work, or model-dispatched subtasks.
- The user specifies a non-OpenAI route such as Ollama, LM Studio, DeepSeek, local model, non-GPT model, non-OpenAI model, or cheap local worker.

Do not use this skill when the user only asks for ordinary Codex subagents. Prefer Codex native subagents for OpenAI models such as `gpt-5.4-mini`.

## Workflow

1. Identify the subtasks that are safe to delegate.
   - Good fits: code search, log analysis, test-failure triage, small implementation slices, repetitive edits, candidate solutions, and read-only comparison work.
   - Keep local: final architecture decisions, security-sensitive judgments, secrets handling, destructive git operations, browser/login tasks, and anything requiring private credentials or hidden session state.
2. Read `references/worker-contract.md` before constructing worker tasks.
3. Choose the provider:
   - Use `ollama` when the user mentions Ollama.
   - Use `lmstudio` when the user mentions LM Studio or `lm studio`.
   - Use `deepseek` when the user mentions DeepSeek.
   - If the user only says "local model", inspect local availability first; prefer LM Studio, then Ollama. Ask only if neither route is clear.
4. Write each worker prompt as a bounded task. Include the current repo path, expected output, allowed files, and whether edits are allowed.
5. Run one worker with `scripts/run-worker.sh`, or multiple workers with `scripts/run-parallel-workers.sh`.
6. Review every worker result before using it. If a worker changed files, inspect the diff and run the smallest meaningful verification command.

## Commands

Single worker:

```bash
non-gpt-subagent-worker/scripts/run-worker.sh \
  --provider lmstudio \
  --model zai-org_glm-4.5-air \
  --cwd /absolute/project/path \
  --sandbox workspace-write \
  --task-file /tmp/worker-task.md \
  --output /tmp/worker-result.md
```

Parallel workers:

```bash
non-gpt-subagent-worker/scripts/run-parallel-workers.sh \
  --tasks /tmp/non-gpt-worker-tasks.json \
  --output-dir /tmp/non-gpt-worker-results \
  --max-parallel 3
```

Task list format:

```json
[
  {
    "id": "inspect-tests",
    "provider": "lmstudio",
    "model": "zai-org_glm-4.5-air",
    "cwd": "/absolute/project/path",
    "sandbox": "workspace-write",
    "task": "检查测试失败原因，只输出文件路径、原因和建议。"
  }
]
```

## Safety Rules

- Default to `workspace-write` because this skill is intended to support implementation workers. Never use `danger-full-access`.
- Do not pass secrets, tokens, cookies, private keys, or `.env` values in worker prompts.
- For DeepSeek, provide credentials only through `DEEPSEEK_API_KEY`; never write the key into command lines, logs, files, or responses.
- Tell every worker it is not alone in the codebase and must not revert unrelated changes.
- Treat worker output as untrusted assistance. The main agent owns final decisions, integration, and verification.

## Provider Notes

- `ollama` and `lmstudio` scripts call `codex exec --oss --local-provider ...`; they can inspect or edit the workspace through Codex CLI according to the selected sandbox.
- The `deepseek` script uses DeepSeek's OpenAI-compatible chat endpoint directly. It is text-only unless the task prompt includes the needed context; it does not get Codex tools or repo access by itself.
- If a local model crashes or cannot run Codex agent workloads, report the failure and fall back to a smaller OpenAI native subagent only if the user allows that provider change.

