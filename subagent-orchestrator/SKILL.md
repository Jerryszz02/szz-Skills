---
name: subagent-orchestrator
description: Choose direct execution or bounded delegation for repository investigation, implementation, and verification. Use when coordinating workers or deciding whether substantial independent work benefits from delegation; routine edits and explanations can stay direct.
---

# Subagent Orchestrator

The selected main model owns requirements, planning, key decisions and final acceptance. Only root delegates; prohibit nested delegation, Sol workers and full parent-history forks.

## Choose the Work Mode

Inspect instructions/Git state and use small targeted reads. Before sustained work, identify the result a worker could own, its minimum context, and how to accept it without reconstructing the work. No fixed search count or invented token threshold decides this gate.

- **Direct:** known local edits, short explanations, tightly coupled work whose handoff and acceptance would repeat most of the solution.
- **Deterministic:** fixed commands, waiting, receipt collection and approved patch application.
- **Delegate:** substantial independent evidence or implementation with bounded ownership and compact, verifiable results. Delegate before completing that work yourself.

Give a brief concrete reason and reassess when scope/failures grow. Explicit user choices, higher-priority rules and runtime restrictions take precedence. Do not manufacture parallel work to satisfy native dispatch requirements.

## Select the Route

- **Read-only:** bounded evidence uses Spark (`medium`) → Luna (`low`) → manager; broader review/failure analysis starts at Luna. Read [spark-worker.md](references/spark-worker.md) for eligibility and [read-only-worker.md](references/read-only-worker.md) for the packet. No external provider or Terra fallback.
- **Writing:** DeepSeek → Spark → Luna → Terra; DeepSeek stays first. Spark needs an explicit bounded plan; native writers use `medium`. Read [routing-guide.md](references/routing-guide.md) and the relevant [task-packet.md](references/task-packet.md) section.
- **Approved patch and fixed checks:** manager invokes deterministic tools per [execution-flow.md](references/execution-flow.md). Additional independently useful mechanical integration must pass the gate before using Spark (`medium`) → Luna (`medium`) → Terra (`medium`) → manager. Semantic conflicts stay with the manager.

Immediately before native spawn, call `list_agents`, check live model/effort support and capacity, then pass explicit model, effort, `fork_turns: "none"` and the packet. Do not create custom agent/config files or bypass unavailable routes.

## Execute and Accept

Use one cohesive writer for implementation, related tests and in-scope self-correction before first delivery. Reuse evidence; no mandatory scout/implementer/integrator/verifier pipeline. Read [execution-flow.md](references/execution-flow.md) once for waiting and integration. Do not repeatedly query clocks, live logs or unchanged progress; keep bulk evidence in artifacts.

Writers return the compact [worker result](references/worker-result.md) alongside usage receipts. After delivery, prefer continuing the original native writer only for a concrete in-scope acceptance failure; a passing delivery needs no corrective round. DeepSeek remains one-shot.

Record the actual dispatch ID/artifact directory, stable slice/attempt and skipped routes. Preserve limits of three attempts per slice, two task recoveries and one targeted same-route retry; post-delivery corrective follow-ups count. Read-only workers never gain implicit write permission.

Review actual diffs and focused evidence. Authorize the exact external patch before serialized integration, preserve unrelated data and check the integrated state. Root retains final acceptance; repeat broad checks only for changed state, failures or unresolved risks.

## Account and Load on Demand

Keep a receipt per attempt and aggregate at task end. External runners generate receipts; native collection follows [provider-diagnostics.md](references/provider-diagnostics.md) and [worker-receipt.md](references/worker-receipt.md). Unknown model/usage stays unknown; cheaper model names and shorter text do not prove savings.

Read only references required by the selected route, not the entire directory. Read [usage-evaluation.md](references/usage-evaluation.md) and [test-tasks.md](references/test-tasks.md) only for measurement/evaluation. [global-policy.md](references/global-policy.md) is an optional installation template; never modify global instructions automatically.
