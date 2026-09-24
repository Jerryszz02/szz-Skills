---
name: subagent-orchestrator
description: Choose direct execution or serial delegation only when the user explicitly invokes $subagent-orchestrator or asks to use this skill. Do not activate automatically for repository investigation, implementation, or verification.
---

# Subagent Orchestrator

Use only when explicitly invoked, not for general requests to use subagents. The main agent plans, decides and accepts. Keep **at most one active worker for this user task**, across native and external routes. No parallel workers, nested delegation, Sol workers or full parent-history forks.

## Start Direct, Delegate When Useful

Invocation does not require a worker, role-selection ceremony or separate orchestration plan. Start direct. Delegate only when a bounded question/outcome needs little shared context and its compact result can replace manager work without requiring a full replay. Once that boundary is clear, delegate before doing the work yourself.

Read instructions/state, essential interfaces and acceptance blockers. Delegate code reading when planning needs evidence; otherwise a clear implementation can go directly to a writer.

- **Direct:** known small edits, short explanations, or coupled work whose handoff/acceptance would repeat the solution.
- **Deterministic:** fixed checks, waiting, receipts and approved patch application; no worker solely for these steps.
- **Delegate:** a complete useful question or outcome, not tiny file-by-file errands. Roles and stages are flexible: reading can inform the manager's plan, or one writer can investigate, implement, test and correct. Reuse the same worker while scope, capability and permissions fit; neither a fixed role sequence nor one worker for the entire task is required.

State a concrete reason. Respect user choices and runtime restrictions; never manufacture parallel work, new tasks or tool/config workarounds to force dispatch. If no permitted route fits, take over.

## Select One Route

- **Writing:** DeepSeek → eligible Spark → Luna → Terra; native writers use `medium`. Read [routing-guide.md](references/routing-guide.md) and [task-packet.md](references/task-packet.md).
- **Read-only outcome:** bounded evidence uses Spark (`medium`) → Luna (`low`) → manager; broader analysis starts at Luna. Read [read-only-worker.md](references/read-only-worker.md); consult [spark-worker.md](references/spark-worker.md) when considering Spark. No external or Terra fallback.

Before native spawn, call `list_agents`, check live model/effort support and capacity, and confirm this task has no running native or external worker. Pass explicit model/effort, `fork_turns: "none"` and a compact packet of paths, accepted decisions and acceptance criteria, not copied conversations/files/logs. Record the actual dispatch ID/artifact directory, slice and attempt. Start fallback only after the previous execution stops.

## Execute, Then Accept

Read [execution-flow.md](references/execution-flow.md) once for stopping, waiting and integration. The same writer self-checks and fixes in-scope defects, then delivers when required checks pass and no criterion remains unresolved. No unrequested audit or hardening after green. Repeated environment/capability failures without new evidence or changed conditions return as blockers. These are instructions, not runtime hard limits.

Read the compact [worker result](references/worker-result.md), actual diff/scope and critical evidence; open focused details as needed instead of repeating investigation. Review the exact external patch before deterministic integration, preserve unrelated data and verify the integrated state. Required visual acceptance stays with the manager; reuse valid checks on unchanged state.

For a concrete in-scope acceptance failure, prefer the same native writer with delta-only evidence and workspace changes. Preserve permissions, slice and recovery accounting: three executions per slice, two task recoveries, one targeted retry per route. DeepSeek remains one-shot; later attempts use fresh HEAD-only worktrees. Passing acceptance ends the task.

## Account on Demand

Keep receipts for every attempt; [provider-diagnostics.md](references/provider-diagnostics.md) and [worker-receipt.md](references/worker-receipt.md) cover collection. Unknown usage stays unknown. Evaluate quality first, then main-agent usage, total cost priced by actual model, then latency. All-model token totals are diagnostic, not a price proxy.

Load [usage-evaluation.md](references/usage-evaluation.md) and [test-tasks.md](references/test-tasks.md) only for measurement. [global-policy.md](references/global-policy.md) is optional; installation never edits global instructions. Read only references needed by the selected route.
