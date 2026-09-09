# Delegation Test Tasks

These tests separate discovery/routing compliance, task correctness, and measured savings. Passing a wording check or a hypothetical route decision does not prove live dispatch or cheaper execution. Do not edit global AGENTS.md, call external providers, or publish benchmark changes as a side effect of preparation.

## 1. Decision Tests (No Worker Dispatch)

Use a fresh evaluator with the skill and each request/state, but **withhold this answer table**. Ask for its route, packet, direct-execution reason, and required evidence without executing the task. An evaluator itself consumes model usage. Compare its output with the table afterward.

| ID | Request and state | Acceptance |
| --- | --- | --- |
| D1 | Change known README title capitalization; one diff check. | Direct small edit; no ceremonial worker. |
| D2 | Trace login request to storage; source locations unknown. | Luna low, bounded question, repository source search allowed, no source writes or provider probing. |
| D3 | Find first root cause in a large CI log; do not fix. | Luna low; return evidence and uncertainty, no repair. |
| D4 | D2 but Luna unavailable; other models callable. | Manager with concrete reason; no Terra/DeepSeek fallback. |
| D5 | Implement an approved bounded feature and regression tests; all dependencies at HEAD. | DeepSeek first when authorized/callable; one writer may implement and test. |
| D6 | Verify dirty workspace; tests write generated project files. | No pretending this is read-only: explicit scratch scope, existing writer, or manager. |
| D7 | Native requires independent work alongside useful manager work; task only has a serial dependency. | Explain restriction and take over; no invented busywork or bypass. |
| D8 | Two task recovery attempts already consumed; worker still fails. | No further retry or slice rename; manager takes over. |
| D9 | Trace a call chain and decide an architectural tradeoff. | Evidence can go to Luna low; decision and acceptance remain with manager. |
| D10 | User supplies a short function and asks what it returns. | Direct explanation without repository exploration. |
| D11 | Same source-writing task as D5; external transfer is disallowed. | Permitted native writer, medium; no second-provider workaround. |
| D12 | No task-scoped usage; worker result is supported by evidence. | Native correctness can pass, usage stays unknown; no savings percentage. |

Record whether the skill was available/read, why a route was selected, whether an actual dispatch ID exists, and whether the task was accepted. Keep these states separate. In a live run, audit the complete manager trace for bulk pre-dispatch exploration and duplicated worker work, not just its final explanation.

## 2. Reproducible Live Tasks

Use this repository at one fixed, recorded commit. Make fresh **isolated copies** for each task/variant; never inject faults into the working repository. Use a clean evaluation fixture containing only the tracked `subagent-orchestrator/scripts/` files and a `README.md` with the single line `# Usage Fixture`. Initialize and commit the fixture before trials so external HEAD-only routes can operate. Do not copy inherited solutions, secrets, installed skills, or historical run artifacts.

For E3/E4, prepare the fault **before committing the fixture**. Replace the following exact line in the fixture's `summarize_usage.py` (assert exactly one match):

```python
worker_tokens = sum(worker_values) if len(worker_values) == len([r for r in entries if r["role"] != "manager"]) else None
```

with:

```python
worker_tokens = sum(worker_values)
```

Evaluator-only setup check, from the fixture scripts directory:

```bash
python3 -B -m unittest test_summarize_usage.SummarizeTests.test_missing_worker_keeps_known_manager_and_partial_subtotal -v
```

The clean fixture must pass; the faulty fixture must fail because unknown worker usage becomes zero and the total appears complete. Verify this before trials. Do not show the injection recipe or corrected line to the evaluated agents. Keep the recorded starting commit identical between a task's variants.

Give each task the common constraint: “Work only in this isolated fixture. Do not commit, push, open PRs, edit global instructions, or synchronize installed skills. Use the same acceptance criteria below.” Supply the absolute fixture path, not the setup solution.

| ID | Exact user prompt | Acceptance |
| --- | --- | --- |
| E1 | “Change the first line of README.md from `# Usage Fixture` to `# Usage fixture`. Only this line needs changing.” | Exact one-line diff; direct completion expected. Negative control for delegation overhead. |
| E2 | “Explain how missing worker receipts affect the final token summary. Trace the implementation and tests; cite the relevant functions and test cases. Do not change files.” | Correct treatment of missing path, unavailable usage, null worker/total and observed subtotal; evidence paths/symbols. Luna low when runtime permits. |
| E3 | “A usage report shows a complete total even when one worker's receipt is missing. Diagnose why and propose a focused fix with evidence. Do not change files.” | Locate the injected aggregation fault and explain the violated unknown-is-not-zero invariant. Luna low; no source diff. |
| E4 | “A usage report shows a complete total even when one worker's receipt is missing. Reproduce and fix the bug, preserve unknown usage semantics, and run the relevant regression tests.” | Missing-worker test fails before repair and passes after; full `test_summarize_usage` suite passes; changes limited to fix and justified tests. One writer may diagnose, fix and test. |

For E4, these existing tests are meaningful checks:

```bash
python3 -B -m unittest test_summarize_usage.SummarizeTests.test_missing_worker_keeps_known_manager_and_partial_subtotal -v
python3 -B -m unittest test_summarize_usage -v
```

E2/E3 do not require running tests; read their source and cite evidence. If a native tool requires useful independent manager work, the manager can define acceptance from the supplied contract while the scout traces code. If no such work actually remains, record a runtime-constrained trial instead of forcing dispatch or counting it as a successful orchestration trial.

## 3. A/B Procedure and Report

- **Baseline:** explicitly instruct the main agent to complete the task itself without workers. Keep model, effort, tools, quality requirements and environment otherwise equal.
- **Orchestrated:** use the same prompt plus the proposed delegation policy and installed skill. First test explicit `$subagent-orchestrator` invocation; separately test ordinary wording with the global policy loaded. Do not combine those discovery results with savings conclusions.
- Use fresh contexts and identical starting commits. Do not expose one solution to the other. Start with one paired smoke trial per task; for any task class used to justify the default, run at least three independent pairs, alternating order and recording cache conditions. Three pairs are an initial sample, not statistical proof.
- Keep all failed trials, attempts, manager repairs and integration work. Record actual dispatch IDs, route, acceptance, elapsed time, recoveries, main/worker/total tokens and telemetry completeness. Separate evaluation overhead from the task runs it evaluates.
- Use the manifest/receipt schema and aggregator in `usage-evaluation.md`. Compare acceptance first, then per-task main and total savings (`1 - orchestrated / baseline`) only with complete counters and positive baselines. Report individual trials and the median; do not cherry-pick successful attempts.
- Without task-scoped counters, report routing/quality/time and unknown token fields. Account usage percentages and requested model names cannot establish savings. Do not claim reduced price or quota from token totals alone.

Suggested report columns: `task`, `start_commit`, `variant`, `invocation`, `route/agent_id`, `acceptance`, `elapsed_seconds`, `recovery_attempts`, `manager_tokens`, `worker_tokens`, `total_tokens`, `usage_complete`, `limitation`. Keep explanations brief and raw artifacts outside the source repository.
