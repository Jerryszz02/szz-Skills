---
name: subagent-orchestrator
description: Delegate repository exploration, behavior tracing, debugging, implementation, fixes, refactors, code review, and test or CI failure analysis. Use before substantial coding execution or intended subagent calls, even without an explicit delegation request. Known tiny edits, short supplied-code explanations, and simple verification may stay with the main agent.
---

# Subagent Orchestrator

Keep the selected main model responsible for requirements, planning, key decisions, and final acceptance. Only the root may delegate; prohibit nested delegation. Do not switch the main model or use Sol workers.

## Decide Before Exploring

Read repository instructions and Git state, then use at most two small, targeted discovery batches to locate the task. This is an initial operating limit, not a measured token break-even point; never expand a batch into a bulk repository read to evade it.

When a permitted worker can own a bounded result, **delegate sustained exploration, failure diagnosis, and independently verifiable implementation** before doing that work yourself. Direct completion is allowed for a known small local edit, a short supplied-code explanation, or a deterministic check with bounded output. Keep decisions and focused acceptance checks with the manager. State a concrete exception, runtime restriction, or exhausted recovery budget when taking over; do not justify substantial direct work merely with “handoff is expensive.”

Use one cohesive responsibility per worker and reuse accepted evidence. Scout, executor, and verifier are roles, not a mandatory three-worker pipeline. Delegate dependent work only when the active tool permits it; native dispatch may require independent work alongside useful manager work. Instructions cannot override runtime restrictions.

## Select the Route

- **Read-only work:** bounded text/code evidence uses **Spark (`medium`) → Luna (`low`) → manager**; broader review/failure analysis stays Luna (`low`) → manager. Read [spark-worker.md](references/spark-worker.md) for eligibility and [read-only-worker.md](references/read-only-worker.md) for the packet. No external provider or Terra fallback.
- **Source-writing implementation, fixes, tests and documentation:** **DeepSeek → Kimi → Spark → Luna → Terra**; keep DeepSeek first. Spark is only for an explicit, bounded plan and is skipped otherwise. Native writing uses `medium`. Read [routing-guide.md](references/routing-guide.md) and the external or native-writing section of [task-packet.md](references/task-packet.md).
- **Patch application and mechanical integration:** **Spark (`medium`) → Luna (`medium`) → Terra (`medium`) → manager**, in the actual target workspace. Skip Spark unless integration is fully specified and mechanical. Read the integration contract in [routing-guide.md](references/routing-guide.md). Verification-only work uses the read-only route; an executor may run its own relevant tests without a new worker.

Immediately before every native spawn, call `list_agents`, check the live tool's supported models/efforts, restrictions and remaining capacity, and queue if full. Pass explicit model, effort, `fork_turns: "none"`, and the route's packet. Do not create custom agent/config files.

## Accept and Account

Announce the delegated responsibility and manager-owned decisions; record the returned agent ID or runner artifact directory, stable slice/attempt, and skipped-route reasons. Default limits: three attempts per slice, two recovery attempts across the task, one targeted retry per route. Follow-ups that repair a failed criterion count as recovery; a read-only worker must not silently become a writer.

Accept from cited evidence, actual diffs, and exact verification results, not a completion claim. Authorize external patches before serialized integration; preserve unrelated work. Avoid repeating a worker's full exploration or broad tests without new evidence.

Keep a receipt per attempt: external runners generate it; the manager records native runtime evidence. The compact read-only receipt is in its route reference; use [worker-receipt.md](references/worker-receipt.md) for full accounting. Missing actual-model or token evidence remains unknown and does not by itself invalidate native correctness. Never infer savings from worker count, requested model, text length, or account percentages.

For measurement and evaluation, read [usage-evaluation.md](references/usage-evaluation.md) and [test-tasks.md](references/test-tasks.md). For the optional user-installed global policy, use [global-policy.md](references/global-policy.md); do not modify global instructions automatically.
