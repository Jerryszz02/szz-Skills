# Usage Measurement and Evaluation

Measure three separate outcomes: main-model tokens, total tokens across all agents, and successful task completion/time. Lower main-model usage does not prove lower total usage or lower price/account quota consumption. Keep cached input, output, provider, model, and reasoning metadata in the original receipts for any later price analysis; this tool does not calculate prices.

Rank results by the evaluation priority: quality gate first, then main-agent usage (response count, mean input, cache), then total cost priced separately by actual model and cached/uncached/output rates, then latency. All-model tokens remain diagnostic: a cheap worker consuming more tokens is not automatically a failure. For price comparisons, verify dated official per-model rates and price cached/uncached input and output separately; missing rates or counters leave cost unknown. API prices do not establish subscription-quota consumption.

## Offline Checks (No Model Calls)

From the repository root:

```bash
python3 -m unittest discover -s subagent-orchestrator/scripts -p 'test_*.py' -v
bash -n subagent-orchestrator/scripts/run-dsh-worker.sh
python3 /absolute/path/to/skill-creator/scripts/quick_validate.py /absolute/path/to/subagent-orchestrator
git diff --check
```

Use a Python environment with PyYAML for `quick_validate.py`. Existing runner tests use fake CLI fixtures in temporary Git repositories; they test scope rejection, patch export, and receipt handling without sending code to a provider. The new summary tests check accounting with synthetic receipts. They cannot establish model quality, real routing compliance, or token savings.

## Forward-Testing the Instructions

For a meaningful change to routing, use an isolated fixture and an independent permitted worker. Give it the skill and a realistic request/state; ask it to produce task packets, route choices and a ledger without dispatching models or modifying a real project. Do not give it the expected route. Check the resulting decisions against these acceptance cases:

| Fixture | Expected behavior |
| --- | --- |
| One trivial wording correction | Direct completion when delegation costs more; brief reason. |
| Bounded text/code evidence; Spark and Luna callable | Spark medium, compact packet, no external probing. |
| Read-only work; Spark and Luna unavailable but Terra/DeepSeek callable | Manager takeover with reason; no Terra/provider fallback. |
| Bounded source-writing implementation; all routes permitted and callable | DeepSeek first, with only required context. |
| Source-writing work; DeepSeek unavailable before execution, eligible native writer callable | Use the eligible native writing route; preflight skip consumes no model execution. |
| Source-writing work; external data transfer disallowed | Permitted native writing route; no workaround via another provider. |
| Approved patches plus unrelated uncommitted edits | Root-reviewed deterministic integration in target workspace; preserve unrelated edits and check combined state. No worker solely for fixed commands. |
| Spark appears in the main-task picker but not the active spawn tool | Skip it before execution; preserve DeepSeek priority for writing and use role fallback. |
| Two failures already consumed the whole task's recovery allowance | No further worker recovery, even if another provider remains available. |
| Worker says tests passed but lacks command/cwd/results | Request evidence; do not accept the summary as verification. |
| Native tool requires independent work; only a serial dependency remains | State restriction; do not manufacture parallel work or bypass the same restriction. |
| Verification command writes generated project files | Not read-only; use an allowed scratch copy, existing writer or manager. |
| Writer self-check and final acceptance both pass | Finish; no mandatory correction or second worker review. |
| Delivered native writer has one reproducible in-scope omission and recovery remains | Continue that writer with focused failure evidence; same slice, next attempt, incremental usage. |
| Missing or contradictory structured result despite CLI exit zero | Preserve raw artifacts and mark result unverified/incomplete; do not infer passing checks. |
| Two independent bounded questions and free runtime slots | One active worker; fold into one packet or run serially; free slots never justify fan-out. |
| Feature needing investigation, implementation and related tests | Flexible serial stages: use a read-only result for planning when needed, otherwise go directly to a writer; batch related work, with no fixed role sequence or mandatory single worker for the entire task. |
| Long manager context, many changed files, full logs | Packet carries paths, accepted decisions and acceptance criteria only; bounded excerpts with bulk evidence in artifacts. |
| Writer's checks pass while hardening ideas remain | Deliver immediately; stopping rule applies before first delivery; no unsolicited expansion or repeated broad checks after green. |
| Same environment/capability failure recurs without new evidence | Stop and report the concrete blocker; no install/browser/tool loop and no invented token/turn cap. |
| Native model catalogued but rejected by the active spawn tool | Skip before execution, record the reason and advance serially; no custom config/CLI workaround. |
| Ordinary request without explicit skill invocation | Do not activate this skill; ordinary delegation remains governed by the user and applicable instructions. |
| Quality passed but a cheap worker used more tokens | Diagnostic all-model total, not automatically a failure; price total cost by actual model and cached/uncached/output rates; no fabricated savings/quota. |
| Code evidence is needed before the manager can plan | A serial read-only stage followed by planning and, if needed, writing is allowed; preserve evidence across roles. |
| A clear plan and a current writer able to finish implementation/tests | Reuse that writer; no mandatory scout/tester stages or new worker just to change phase. |
| Explicit skill invocation for a known tiny edit | Direct completion; invocation is not a mandate to orchestrate or load worker manuals. |
| Handoff needs most of the parent history and a full manager replay | Keep direct or redefine a bounded question with compact evidence; no presumed savings. |
| Relevant state changed after the worker collected evidence | Refresh only affected evidence before accepting; do not rely on stale findings. |

This exercises instructions, not the real execution harness. It uses evaluator tokens, so record it as an evaluation attempt. A forward-test failure supports a focused correction; do not repeat evaluation indefinitely.

## Runtime Evidence

Use [provider-diagnostics.md](provider-diagnostics.md) for runner discovery, structured skip reasons and native rollout collection. Manifests may add `"routes": ["dsh/route.json", "native-skip.json"]`; these are diagnostics, not extra model attempts. The summary exposes `routing`, `skipped_routes` and `unaccounted_routes`. A launched route absent from `runs` makes worker/total usage unknown. Per-run `usage` retains cache and source; native receipts with overlapping response IDs are rejected.

External attempts already produce `worker-receipt.json`. For main/native runs, use runtime evidence with explicit task/attempt scope. Do not assume the native collaboration tool exposes usage. Record unavailable fields honestly. One manager receipt covers all main-agent work for this task, including its planning, review, and any direct repair; exclude child usage.

The manager receipt uses the same `actual_model`, `status`, and `usage` fields as a worker. For example, when scoped counters are unavailable:

```json
{
  "schema_version": 1,
  "worker": "manager",
  "actual_model": null,
  "status": "completed",
  "usage": {
    "available": false,
    "input_tokens": null,
    "output_tokens": null,
    "total_tokens": null,
    "source": "runtime did not expose task-scoped manager counters"
  }
}
```

When available, supply observed nonnegative integer input/output/total tokens, `available: true`, and the evidence source. Total must equal input plus output. Input already includes cache reads/writes; do not add cached tokens again. Store counter boundaries and provenance in `evidence`. For a continuing native worker, use separate attempt deltas, not repeated cumulative session totals. The script validates arithmetic, not telemetry provenance or whether a run was omitted.

## Run Manifest and Summary

Write one manifest per baseline/orchestrated trial, outside the source repository. `acceptance` is the root's verified outcome (`passed`, `failed`, or `incomplete`), not an inference from worker status. `elapsed_seconds` is measured wall time. Use stable `slice_id` values and increasing attempts for retries/fallbacks; include failed and integration attempts. Exactly one manager entry is required. Its `attempt` is 1 and its receipt contains the whole task's manager usage.

```json
{
  "schema_version": 1,
  "task_id": "parser-regression-trial-1",
  "variant": "orchestrated",
  "acceptance": "passed",
  "elapsed_seconds": 120,
  "runs": [
    {"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"},
    {"id": "build-1", "role": "worker", "slice_id": "build", "attempt": 1, "receipt": "build-1/worker-receipt.json"},
    {"id": "build-2", "role": "worker", "slice_id": "build", "attempt": 2, "receipt": "build-2/worker-receipt.json"},
    {"id": "integrate", "role": "integrator", "slice_id": "integration", "attempt": 1, "receipt": null}
  ]
}
```

This is an illustrative manifest, not measured results. `receipt: null`, a missing file, or `usage.available: false` means unknown usage. Relative paths resolve from the manifest directory. Do not supply both a receipt and its manifest copy, duplicate receipt files under different names, or overlapping session counter windows. The tool rejects duplicate resolved paths and duplicate role/slice/attempt identities, but cannot identify all duplicated evidence or infer missing runs.

```bash
python3 subagent-orchestrator/scripts/summarize_usage.py \
  --run /absolute/artifacts/run.json \
  --output /absolute/artifacts/usage-summary.json
```

Without `--output`, JSON goes to stdout. Outputs:

- `manager_tokens`: the main task's observed tokens, or `null`.
- `worker_tokens`: all worker/integrator attempt tokens, or `null` if any are unknown; zero for a baseline without workers.
- `total_tokens`: manager plus workers only when complete, otherwise `null`.
- `observed_tokens`: known subtotal, **not a total when `usage_complete` is false**.
- `missing_usage`, per-run model/status/completeness, `worker_attempts`, and `retry_attempts` for audit. Retry count includes provider fallback after execution failure and corrective follow-ups whose attempt is greater than 1.

Malformed inputs and inconsistent totals return a nonzero exit with an error; incomplete telemetry still returns a valid summary. The tool neither enforces recovery budgets nor verifies the supplied acceptance outcome.

## Before Dispatch: Predict Without Fabricating Savings

Prefer delegation when a worker can consume substantial independent work and return compact evidence the manager will not reconstruct. Direct work is valid for known coupled tasks and cheap evidence; fixed commands use deterministic tools. No search-count threshold or invented numeric savings decides this. Keep one active worker per user task across native and external routes and run them serially; do not fan out independent parts or start a fallback before the previous execution has stopped. Use the task battery in `test-tasks.md` to calibrate the gate.

Treat successful acceptance as a prerequisite. Track manager tokens, total tokens, latency and recovery separately; price/quota savings require their own valid accounting. Missing telemetry limits accounting, not native correctness acceptance.

## Controlled Task Comparison

A small benchmark can run before relying on daily production work:

1. Choose a tiny edit, a bounded bug with existing tests, and a feature with separable implementation and integration. Prepare fixed prompts and observable acceptance checks.
2. Run each from the same starting commit and dependency state in separate clean worktrees: baseline with the selected main model alone; orchestrated with the same main model and the proposed worker routing. Keep main reasoning effort and acceptance criteria equal. Record skill versions, actual models/efforts, routing availability, start/end times, and all attempt evidence.
3. Use fresh contexts; do not show one variant's solution to the other. Alternate run order across trials and record cache behavior. Repeat representative cases when variance matters; one run is a smoke test, not a stable savings estimate.
4. Compare acceptance first, then main tokens, total tokens, elapsed time, and recovery count. Include failed trials and failed attempts; do not improve savings by dropping failures. Calculate `1 - orchestrated / baseline` separately for main and total tokens only when both corresponding measurements are complete and the baseline is positive.
5. If main/native task counters are unavailable, report the measurement gap and provider subtotals only. A harness with scoped telemetry is needed for a defensible full comparison; account usage percentages cannot fill that gap.

Synthetic fixtures and forward-tests can run without live repository mutation or external provider calls. A real A/B benchmark consumes real model usage and must stay within the user's authorized data/provider/task scope. Do not claim a measured saving from the offline suite.


## Coordination Diagnostics

Alongside receipts, record observed main-model unique response count and mean input, per-model cache/uncached/output, progress-only responses, handoffs and post-delivery repairs when the runtime exposes them. Missing fields stay unknown. These diagnostics explain overhead; they do not assign causal savings to a phase or infer price/quota. Sum cached input only once as part of input; reasoning output is already part of output. Avoid creating another model task solely to count deterministic receipt fields.

For a strategy revision, use the A/B/C protocol in `test-tasks.md`: direct baseline, frozen previous policy and revised policy. Measure request reduction and acceptance together, not only raw totals dominated by repeated cached context. Do not automatically execute the live benchmark during a skill update.
