# Provider Diagnostics and Feedback

Use for an eligible writing route or an explicit provider health check. Read-only task routing does not require external probing. Diagnostic files are local artifacts, not telemetry sent to a service.

## Discover and Verify

Run each probe independently so a missing unrelated command cannot short-circuit it:

```bash
python3 scripts/route_diagnostics.py probe --provider dsh
python3 scripts/route_diagnostics.py probe --provider kimi
```

Paths in these examples are relative to the skill directory. The resolver honors `DSH_BIN` / `KIMI_BIN`, then PATH, then the standard user installs `~/.local/bin/dsh` / `~/.kimi-code/bin/kimi`. An invalid explicit override fails without falling back. It reports the candidates and selected executable without dumping environment variables or configuration. A successful probe proves executable discovery only, not credentials, API connectivity or patch correctness.

The normal runners use this resolver automatically. For a user-requested connectivity check, run each runner against a committed synthetic fixture in a temporary Git repository. Ask it to change one allowed text file, verify the exact content, then inspect the exported patch and receipt. Keep real project content and private sessions out of the probe. Do not run extra paid smoke tests on every delegation: a normal successful bounded worker run is already end-to-end evidence.

Keep entrypoint and actual model separate: Kimi CLI can use a configured model from another provider. Preserve `actual_model`, the evidence source, and configured reasoning settings; do not silently switch models during diagnostics.

## Record Every Route Outcome

Pass stable `--slice-id ID --attempt N` to either runner. Without a slice ID, the runner uses the task-packet digest prefix; supply an explicit ID across corrected packets so recovery history stays stable.

Once a valid repository and safe, empty output directory exist, the runner creates `route.json`. Invalid arguments, unsafe/nonempty output paths or invalid repositories fail on stderr before creating diagnostics. The report records:

- Executable and resolution source; task hash, slice and attempt.
- Stage, `reason_code`, exit code and `execution_state`.
- Actual model, token usage/source and receipt path when recovered.

Typical reasons: `cli_missing`, `headless_preflight_failed`, `model_config_unavailable`, `task_packet_invalid`, `dirty_overlap`, `worker_failed`, `scope_rejected`, `metadata_incomplete`, `completed`.

`not_started` is preflight only and consumes no model attempt. `unknown` is persisted immediately before CLI launch; model execution/usage is unproven, so count it conservatively as an attempted execution. `observed` means runtime usage was recovered, including failed model runs. A hard process kill may leave `worker_running` unfinished; reconcile it with runtime/process evidence instead of dropping the attempt.

When policy/runtime prevents calling a runner, record the decision without invoking a provider:

```bash
python3 scripts/route_diagnostics.py skip \
  --provider dsh --slice-id auth-fix \
  --reason external_boundary \
  --detail 'This slice changes authentication and is restricted to native workers.' \
  --output /absolute/artifacts/auth-dsh-skip.json
```

Use a separate file per decision. State the specific boundary or unavailable capability, not just “fallback”. Never include secrets or raw environment/config values. This is also how to record native unsupported routes and direct-takeover reasons.

## Collect Native and Manager Usage

When authorized local Codex rollout evidence is available, use the collector with an explicit thread and the turns belonging to this attempt:

```bash
python3 scripts/collect_native_receipt.py \
  --rollout /absolute/rollout.jsonl --thread-id THREAD_ID \
  --turn-id TURN_ID --task-file /absolute/task.md \
  --worker native --status completed --fork-turns none \
  --output /absolute/artifacts/native-receipt.json
```

Repeat `--turn-id` for a manager's task-local turns and use `--worker manager`. A corrective worker follow-up needs its own turn selection, not the entire child session again. Resolve local IDs from dispatch/runtime evidence; do not guess file paths or inspect unrelated conversations. The collector reads locally and exports only metadata/counters, never messages. Do not give private rollout files to external workers.

The collector sums incremental `token_usage_record.payload.usage`, filters thread and turns, and deduplicates response IDs. It never adds cumulative thread/turn counters, cached input or reasoning output a second time. Missing or invalid scoped telemetry produces unknown usage with a reason; requested model names cannot establish the actual model. If local logs are unavailable, retain a manual unknown receipt per `worker-receipt.md`.

## Return Useful Feedback

Add route diagnostic paths to the run manifest's optional `routes` list. Only launched model attempts belong in `runs`; preflight/policy skips belong in `routes`. Failed/interrupted launches still need a `runs` entry, with a null receipt if necessary. Reference each runner receipt once; its copy in `route.json` is not another token contribution.

Run `summarize_usage.py` before final reporting. It returns skip reasons, per-run usage/source, unaccounted launched routes, and manager/worker totals. Known overlapping native response IDs are rejected. Missing accounting remains visible; do not report partial subtotals as complete totals.

Return a compact task-end account: which entrypoints and actual models ran, what was skipped and why, manager/worker tokens and cache/source, failures/retries, and the summary artifact path. Keep the selected main model responsible for acceptance; these diagnostics do not change routing boundaries or prove savings without a comparable baseline.
