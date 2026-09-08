---
name: subagent-orchestrator
description: Orchestrate bounded subagent work with a planning and acceptance manager, DeepSeek-first execution, and native integration. Use for release-readiness assessments, cross-module code investigations, multi-step implementation, and explicit delegation requests, even when the user does not mention subagents; also use before intended spawn_agent calls. Reduce main-model work through focused task packets, evidence-based acceptance, and bounded recovery.
---

# Subagent Orchestrator

Keep GPT-6, when selected as the main model, focused on requirements, planning, decisions, and final acceptance. Do not switch the user's main model. Delegate substantial execution by default; do not repeat a worker's exploration in the main thread. Only the root/main agent may dispatch workers. Every worker must be prohibited from nested delegation and `spawn_agent`. Never select Sol for a worker.

## Delegation Gate

Run this gate before substantial exploration, and revisit it when an assessment becomes implementation or a new independent workstream appears.

1. Read repository instructions and inspect current Git state with the minimum context needed to dispatch safely. Delegate deeper code discovery and evidence gathering before detailed planning when needed.
2. Define bounded work with explicit inputs, ownership, dependencies, and observable acceptance. Keep tiny tasks or work whose handoff and review would cost more than direct completion in the main thread; state the concrete handoff-cost or scope reason before proceeding. Before deeper exploration, tell the user which slices will be delegated and which decisions stay with the manager; use `references/routing-guide.md` for examples.
3. Keep architecture, ambiguous tradeoffs, security judgments, conflict decisions, and acceptance with the main agent. Workers may gather safe evidence and implement an approved design within their route's boundary.
4. Sequential work can still be delegated. Parallelize only independent slices with non-overlapping ownership and independent acceptance; stabilize shared interfaces before consumers start.
5. Read `references/routing-guide.md` for route selection and recovery limits, `references/task-packet.md` for dispatch, and `references/worker-receipt.md` for evidence and task-level usage. Do not start workers merely because the skill triggered.

## Roles and Routes

- **Main manager:** Own requirements, task map, interfaces, risk decisions, patch authorization, and final acceptance. Inspect actual diffs, relevant code, and verification evidence without replaying every exploration log. Handle tiny work or take over when bounded worker recovery is exhausted.
- **Execution workers:** Code discovery, evidence gathering, implementation, tests, routine fixes, and documentation use **DeepSeek → Kimi → Luna → Terra**, within the recovery budget. Verify availability and safety; do not skip an eligible earlier route for familiarity. DeepSeek and Kimi use the existing detached-worktree runners. Native scouting uses `low`; implementation uses `medium`.
- **Integration/check worker:** Use **Luna (`medium`) → Terra (`medium`) → main manager** for approved patch application, mechanical integration, and checks in the actual target workspace. This is an explicit role exception to the execution order: external HEAD-only runners cannot see uncommitted integrated changes. Root authorization of the concrete patch is required; it does not add a user approval step. Semantic conflicts return to the manager.

For native dispatch, use explicit `model: "gpt-5.6-luna"` or `"gpt-5.6-terra"`, explicit `reasoning_effort`, and `fork_turns: "none"`. Immediately before **every** spawn, call `list_agents`, derive remaining slots from the active runtime limit, and queue when full. Include the complete task packet in the message.

## Workflow

1. Set the task's acceptance criteria, slice IDs, and recovery limits before dispatch. Record role, route, attempt, and skipped-route reasons in a small task ledger. Apply the limits in `references/routing-guide.md` before every retry, fallback, or corrective follow-up.
2. Send only necessary requirements, file locations, shared interface decisions, and relevant failure evidence. Ask for a short result with artifact pointers; keep bulk logs in files. Reuse existing worker evidence rather than assigning duplicate exploration.
3. Require a unified worker receipt. External runners write `worker-receipt.json`; record native runtime evidence in the same schema. Missing usage remains unknown, never estimated or silently zero.
4. Review external `worker-receipt.json`, `manifest.json`, `status.txt`, `scope-check.txt`, and `changes.patch`. Reject out-of-scope changes. The root reviews and authorizes the exact patch before the integration worker can apply it.
5. Serialize integration into an identified target workspace after its writers finish. Capture the starting HEAD and dirty paths, preserve unrelated edits, and run `git apply --check` before applying approved patches. Do not resolve semantic conflicts without a manager decision. Run the required checks against the combined result; invalidate affected check results after further changes.
6. Accept from the actual integrated diff and verification artifacts, not a worker's completion claim. Inspect key logic and gaps according to risk. The manager may perform focused independent checks; avoid broad duplicate test runs without a new reason.
7. Report outcome, remaining limitations, and available main/worker/task usage. Use `scripts/summarize_usage.py` and the run manifest in `references/usage-evaluation.md` for task totals. Read that reference when measuring savings or testing this skill; do not claim savings from worker receipts alone.

## External Worker Boundary

Detached worktrees isolate Git changes, not operating-system access.

- Do not send secrets, credentials, cookies, private keys, `.env` values, private session state, or account access tasks.
- Do not use external workers for authentication, payments, security conclusions, migrations, destructive Git operations, or tasks depending on uncommitted main-workspace changes.
- Require `HEAD-only dependency: yes` and bounded allowed/forbidden paths. Existing runners reject dirty allowed paths; do not bypass this to integrate changes.
- Honor provider/data authorization and approval-review boundaries. When an external route is disallowed, use a permitted native route; do not send the same data through another external provider as a workaround.
- Never automatically apply an external patch. Do not create project `.codex/config.toml` or custom agent TOML files as part of this workflow.

## External Commands

```bash
subagent-orchestrator/scripts/run-dsh-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory

subagent-orchestrator/scripts/run-kimi-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory
```

Use separate empty output directories for each attempt. Kimi uses its configured default model unless the user or current configuration requires `--model <alias>`. Runner failures do not authorize bypassing scope or exceeding the task's recovery budget.
