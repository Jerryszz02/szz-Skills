---
name: subagent-orchestrator
description: Gate and orchestrate Codex delegation across a main manager, a DeepSeek Harness headless worker, an isolated Kimi Code worker, and explicit Luna or Terra native subagents. Must be used before every intended spawn_agent call and whenever work may benefit from decomposition, parallel investigation or implementation, multiple independent workstreams, or explicit subagent delegation. Delegate only bounded, independent, verifiable work; keep architecture, sensitive judgment, integration, and final acceptance with the main agent.
---

# Subagent Orchestrator

Treat the root agent as the only manager. Only the root agent may invoke `spawn_agent`; every worker must be explicitly prohibited from delegating or spawning another worker. Never select Sol for a worker.

## Delegation Gate

Before every intended `spawn_agent` call, and before substantial work that may benefit from delegation:

1. Identify candidate workstreams and their dependencies.
2. Keep the task with the main agent when it is small, tightly coupled, sequential, security-sensitive, destructive, or cheaper to complete directly.
3. Delegate only bounded work with explicit inputs, outputs, ownership, and verification.
4. Parallelize only when at least two useful tasks have no unresolved dependency, have non-overlapping ownership, and can be accepted independently.
5. Record the routing choice and the reason. Do not start workers merely because this skill triggered.
6. Immediately before a native spawn, call `list_agents`, derive the remaining native concurrency slots from the active runtime limit, and do not call `spawn_agent` when no slot remains.

Read `references/routing-guide.md` before choosing a worker. Read `references/task-packet.md` before constructing any delegated task. Read `references/worker-receipt.md` before dispatch so every route returns the same audit fields.

## Roles

- **Main manager:** Own requirements, planning, task dependencies, interfaces, security decisions, conflict resolution, integration, final diff review, and acceptance. Implement directly when delegation has no clear benefit. It is the only role allowed to call `spawn_agent`.
- **DeepSeek worker:** First choice for every delegated slice when `dsh --profile headless` is callable and the task is safe for an external worker. Run it through `scripts/run-dsh-worker.sh` in an isolated detached worktree.
- **Kimi worker:** Second choice when DeepSeek is unavailable, fails its preflight, or fails the bounded task. Use only for a slice that can start from current `HEAD`, owns bounded paths, and has deterministic acceptance. Run it through `scripts/run-kimi-worker.sh`.
- **Luna native worker:** Third choice when the external routes cannot be used. Use `model: "gpt-5.6-luna"` and explicitly set `reasoning_effort`: `low` for scouting or `medium` for implementation.
- **Terra native worker:** Final worker fallback. Use `model: "gpt-5.6-terra"` and explicitly set `reasoning_effort`: `low` for scouting or `medium` for implementation.

The required fallback order is DeepSeek, Kimi, Luna, then Terra. Do not skip an available earlier route merely because a later model is more familiar. Model names are not proof of availability; verify the actual CLI or native tool before dispatch. Never use Sol for a worker.

## Workflow

1. Inspect repository instructions and current Git state before delegation.
2. Build a dependency-aware task map. Stabilize shared interfaces before starting downstream tasks.
3. Write a complete task packet for each worker. Every packet must explicitly say nested delegation and `spawn_agent` are forbidden.
4. Try the worker routes in order: DeepSeek, Kimi, Luna, Terra. A route is unavailable only when its executable/tool/model is absent, its required preflight fails, or the task violates that route's safety boundary.
5. Before every native spawn, confirm this is the root agent, call `list_agents`, calculate remaining native slots, and stop or queue the task when none remain. Call `spawn_agent` with explicit `model`, explicit `reasoning_effort`, and `fork_turns: "none"`; include the full task packet in `message`.
6. Dispatch dependent tasks sequentially. Run workers concurrently only for disjoint, dependency-free slices with independent acceptance.
7. Require a worker receipt containing the task objective, actual model, reasoning tier, fork range, status, and runtime token usage. External runners write `worker-receipt.json`; the main agent records the same schema for native workers.
8. Review actual worker evidence. For DeepSeek or Kimi, inspect `worker-receipt.json`, `manifest.json`, `status.txt`, `scope-check.txt`, and `changes.patch`; then run `git apply --check` before accepting the patch. Kimi is not acceptable when its actual model, reasoning tier, or usage metadata is incomplete.
9. Retry a failed task at most once with the exact failed criterion. Then continue to the next fallback route or retain it in the main thread and report the fallback.
10. Run deterministic verification against the integrated workspace. The main agent owns the final answer.

## External Worker Boundary

DeepSeek and Kimi worktree isolation is a Git conflict boundary, not an operating-system security sandbox.

- Do not send secrets, credentials, cookies, private keys, `.env` values, private session state, or account access tasks.
- Do not use an external worker for authentication, payments, security conclusions, migrations, destructive Git operations, or work that depends on uncommitted main-workspace changes.
- Require the task packet to declare that the slice is `HEAD`-only and to enumerate allowed and forbidden paths.
- Never apply an external worker patch automatically. Reject out-of-scope changes and inspect all accepted changes in the main thread.
- Do not create project `.codex/config.toml` files or custom agent TOML files as part of this workflow.

## DeepSeek Command

```bash
subagent-orchestrator/scripts/run-dsh-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory
```

The runner uses the configured `dsh --profile headless` profile. After at most one targeted retry, a nonzero runner exit, missing command, failed profile preflight, or failed scope check moves the task to Kimi; it does not authorize bypassing the task boundary.

## Kimi Command

```bash
subagent-orchestrator/scripts/run-kimi-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory
```

Pass `--model <alias>` only when the user or current Kimi configuration requires a specific model. Otherwise let Kimi use its configured default.
