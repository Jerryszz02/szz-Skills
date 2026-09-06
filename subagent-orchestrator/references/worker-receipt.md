# Worker Receipt Contract

Every dispatched worker must produce one receipt using this schema. External runners write `worker-receipt.json`; for native workers, the main agent records dispatch fields from `spawn_agent` and actual model/usage only from returned runtime evidence. Record unknown model as `null` if the runtime does not expose it; a requested model or worker self-description is not observed metadata.

```json
{
  "schema_version": 1,
  "worker": "kimi",
  "task": {
    "objective": "Implement the bounded task.",
    "task_packet_sha256": "..."
  },
  "requested_model": null,
  "actual_model": "deepseek-v4-pro",
  "actual_models": ["deepseek-v4-pro"],
  "reasoning_effort": "on",
  "fork_turns": "not-applicable",
  "context_scope": "HEAD-only detached worktree",
  "status": "completed",
  "usage": {
    "available": true,
    "input_tokens": 100,
    "uncached_input_tokens": 80,
    "cached_input_tokens": 20,
    "cache_write_input_tokens": 0,
    "output_tokens": 10,
    "total_tokens": 110,
    "source": "kimi-session-wire"
  },
  "evidence": {
    "session_id": "session_..."
  }
}
```

## Field Rules

- `task.objective` comes from the task packet; do not replace it with a generated summary.
- `requested_model` records a CLI/tool override. It may be `null` when the provider chooses its configured default.
- `actual_model` records the model observed in runtime evidence, never the requested alias. Preserve `actual_models` when more than one model handled the task.
- `reasoning_effort` is the actual or explicitly dispatched reasoning tier. External provider values such as `on` are preserved rather than translated to a native tier.
- `fork_turns` is `none` or a numeric range for native workers. It is `not-applicable` for external workers because they receive a task packet in a `HEAD` worktree rather than a fork of the parent conversation.
- When an external CLI does not expose a configurable reasoning tier, record `reasoning_effort` as `not-exposed` rather than leaving the field ambiguous.
- `status` is one of `completed`, `failed`, `scope-rejected`, `cleanup-failed`, or `metadata-incomplete`.
- Token fields must come from runtime usage evidence. Never estimate missing usage or infer it from text length. Set `usage.available` to `false` and explain the source limitation when the runtime exposes no usage.
- `input_tokens` includes uncached input, cache reads, and cache writes. `total_tokens` is `input_tokens + output_tokens`.

## Acceptance

The main agent reviews the receipt together with the actual diff and test output. Native correctness can be accepted when runtime usage/model metadata is unavailable, but accounting remains incomplete; record this limitation explicitly. A receipt is audit evidence, not proof that the implementation is correct. A successful Kimi run is not acceptable when its actual model, reasoning tier, or usage cannot be recovered; the runner marks it `metadata-incomplete`.

## Task-Level Accounting

Keep all attempted worker receipts, including failed, scope-rejected, and metadata-incomplete runs. Record stable slice IDs and attempt numbers in the task ledger. Include integration/check workers and corrective follow-ups. Preflight-only rejection has no model attempt; unknown launch state is recorded with unavailable usage.

Record one separate manager receipt for the user task with `actual_model`, `status`, and the same `usage` object. It must contain only the main agent's task-local usage, excluding subagents. Use runtime task totals or end-minus-start cumulative counters with known scope. A continuing worker's follow-up likewise needs non-overlapping attempt deltas, not its full session total repeated for every attempt. Preserve the source and counter boundaries in `evidence`; retain original artifacts outside the repository.

Do not use account quota percentages, text length, requested model names, or an unverified session counter as task token evidence. Do not subtract child usage unless the runtime explicitly documents that it is included. When the current runtime cannot expose scoped usage, record `usage.available: false`, null core totals and a source explaining the limitation. The existing `worker_receipt.py native` command requires an observed model; if it is unavailable, write the receipt with null model directly instead of passing the requested alias to that command.

Read `usage-evaluation.md` for the run manifest, offline aggregation command and controlled comparison protocol. Receipt collection for external runners is automatic; main/native scoped collection and the task manifest remain root-managed. The aggregator cannot prove that supplied telemetry is authentic or scoped correctly.
