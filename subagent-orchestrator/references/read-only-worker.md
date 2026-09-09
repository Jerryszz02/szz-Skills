# Read-only Luna Worker

Use only native `gpt-5.6-luna`, explicit `reasoning_effort: "low"`, `fork_turns: "none"`. No external provider probing, worktree, patch, or Terra fallback. If the route is unavailable, constrained by the active tool, or fails after permitted recovery, state the reason and let the manager take over.

## Compact Packet

Send these facts directly; no external packet headings or HEAD-only preflight are needed:

```text
Role: read-only scout/reviewer/verifier; Luna, low, fork none.
Slice: <stable ID>; attempt: <n>; remaining task recoveries: <n>.
Question: <one bounded question and observable completion criterion>.
Workspace/state: <absolute path, current workspace or committed revision>.
Read scope: <relevant source/docs/tests/logs; repository-wide search if location unknown>.
Exclude: secrets, credentials, .env values, private sessions, .git internals,
         dependency/vendor/generated trees unless explicitly relevant and permitted.
Source writes: forbidden. No repairs, Git mutations, nested delegation or provider calls.
Evidence/checks: <required paths/symbols/line evidence or exact safe commands>.
Return: conclusion, evidence, checks with cwd/exit code, uncertainty and blockers;
        target <=250 words, longer only for essential actionable evidence.
Artifacts: <optional directory outside source repo for long logs/results>.
```

Repository-wide search permits locating relevant files, not dumping every file. Narrow reads as evidence develops. Read-only is a task instruction, not an operating-system sandbox. Do not run builds/tests that change project files under this role: use a permitted isolated scratch copy with explicit command/output scope, the existing executor, or manager. Pure bounded verification can remain direct. Any permitted artifact writes are restricted to the named output directory.

The manager checks rules/state and supplies the question, not a precomputed file map. Scout uncertainty is an acceptable result when supported by evidence; the manager can ask one targeted follow-up within budget. A new source repair requires an explicit writing packet and the writing route. Preserve cited findings so the executor does not restart exploration.

## Dispatch and Recovery

Only root dispatches. Call `list_agents` immediately before spawn; check the active tool's availability, independence requirements and capacity. Queue if capacity alone is exhausted. Identify useful independent manager work when the native tool requires it. Do not claim a dispatch that never returned an agent ID.

Apply at most three attempts per slice, two recovery attempts shared across the entire task, and one targeted retry on this route. Once model execution starts, a failed attempt counts even if its receipt is missing. A corrective follow-up counts as recovery; never rename a failed slice to reset the budget. Unavailable routes/preflight-only failures do not count as model execution; unknown launch state counts conservatively. There is no fallback model for this role.

## Compact Native Receipt

Root records one JSON receipt outside the repository per attempt. Add dispatch details and evidence from the actual call/result; do not ask the worker to guess telemetry. Example with unavailable runtime counters:

```json
{
  "schema_version": 1,
  "worker": "native",
  "task": {"objective": "<packet question>"},
  "requested_model": "gpt-5.6-luna",
  "actual_model": null,
  "reasoning_effort": "low",
  "fork_turns": "none",
  "context_scope": "<workspace and read scope>",
  "status": "completed",
  "usage": {
    "available": false,
    "input_tokens": null,
    "output_tokens": null,
    "total_tokens": null,
    "source": "runtime did not expose attempt-scoped counters"
  },
  "evidence": {"agent_id": "<returned ID>", "slice_id": "<ID>", "attempt": 1}
}
```

Set status to the observed outcome, not always completed. When available, replace null metadata with runtime evidence and preserve its source. Correctness may be accepted from evidence while accounting stays incomplete. Read `worker-receipt.md` only for full field rules or `usage-evaluation.md` for task aggregation and comparison.
