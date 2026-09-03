# Routing Guide

Pass the Delegation Gate before every intended `spawn_agent` call. Use task properties before model names to decide whether delegation is justified, then use the fixed worker fallback order. File count alone does not determine complexity.

## Decision Matrix

| Task shape | Route | Required constraints |
| --- | --- | --- |
| Small, tightly coupled, sequential, or coordination-heavy | Main manager | Explain briefly why delegation would not help. |
| Any bounded, safe delegated slice | DeepSeek via `dsh --profile headless` | First choice; detached worktree, bounded paths, no secrets or high-risk work, reviewable patch. |
| Same task when DeepSeek is unavailable or fails | Kimi Code | Second choice; detached worktree, bounded paths, no secrets or high-risk work, reviewable patch. |
| Same task when both external routes cannot be used | Luna | Third choice; explicit model and reasoning effort; full task packet; no nested delegation. |
| Same task when Luna is not callable or fails | Terra | Final worker fallback; explicit model and reasoning effort; full task packet; no nested delegation. |
| Architecture, ambiguous debugging, security, authentication, payments, migrations, destructive work, integration, or final review | Main manager | Scout evidence may be delegated, but judgment and acceptance remain in the main thread. |

## Availability and Fallback

1. Try DeepSeek first. Confirm `dsh` is executable, `dsh --profile headless --help` succeeds, the task is safe for an external worker, and the task packet passes `run-dsh-worker.sh` preflight.
2. If DeepSeek is absent, fails preflight, or fails the bounded task, try Kimi. Confirm `kimi` is executable and the same safety and packet checks pass.
3. If neither external route can be used, inspect the active native subagent tool for callable model overrides. A model catalog entry or custom-agent file is not proof that the current session can select it.
4. Try Luna, then Terra. For scouting use explicit `reasoning_effort: "low"`; for implementation use explicit `reasoning_effort: "medium"`. Never omit the model or reasoning effort and never use Sol.
5. Native dispatch must use `fork_turns: "none"` so the bounded task packet, rather than replayed parent history, is the worker's context. Put all required context in `message`.
6. Never silently substitute a model or provider. Record why each skipped or failed route was unavailable and report the chosen fallback.

## Native Spawn Gate

Only the root/main agent may call `spawn_agent`. Immediately before each native spawn:

1. Confirm the current agent is the root/main agent.
2. Call `list_agents` and count live workers plus the root agent.
3. Derive remaining slots from the concurrency limit stated by the current runtime; do not hardcode a limit from an older session.
4. If zero slots remain, do not call `spawn_agent`. Wait, queue the task, or keep it in the main thread.
5. Send the complete task packet and explicitly prohibit `spawn_agent`, nested agents, and any other delegation.

Native examples:

```text
Scout:  model="gpt-5.6-luna",  reasoning_effort="low",    fork_turns="none"
Builder: model="gpt-5.6-luna", reasoning_effort="medium", fork_turns="none"
Fallback scout:  model="gpt-5.6-terra", reasoning_effort="low",    fork_turns="none"
Fallback builder: model="gpt-5.6-terra", reasoning_effort="medium", fork_turns="none"
```

## Parallelism Gate

Parallel execution requires all of the following:

- At least two useful tasks with `Dependencies: none`.
- Explicit, non-overlapping ownership.
- No shared lockfile, database schema, generated artifact, API contract, or type definition being edited concurrently.
- Independent acceptance commands.
- Expected speed or context benefit greater than dispatch, review, and integration cost.

If an interface is shared, stabilize it in the main thread before dispatching its consumers.

## Retry and Acceptance

- Give the retry only the failed criterion and relevant evidence, not a fresh broad request.
- Move a failed task through the configured order: DeepSeek, Kimi, Luna, Terra, then main thread.
- Permit at most one targeted retry on a route before moving to the next route.
- Inspect actual diffs and command output. Do not accept a worker result from its prose summary alone.
- Require the unified worker receipt from `worker-receipt.md`. Never substitute the requested model for the observed model or estimate unavailable tokens.
- Reject a successful Kimi result when its actual model, reasoning tier, or usage cannot be recovered from runtime evidence.
