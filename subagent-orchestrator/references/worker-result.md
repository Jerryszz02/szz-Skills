# Compact Worker Result

Use for source-writing delivery after implementation, related checks and in-scope self-correction. A result describes work and verification; `worker-receipt.json` separately records model/usage. Root still reviews the actual diff and focused evidence. A well-formed worker claim is not independent acceptance.

## Writer Report

Finish with one JSON object (a single JSON code fence is also accepted), without surrounding prose. Keep explanations short and full logs in artifacts:

```json
{
  "schema_version": 1,
  "status": "completed",
  "summary": "Preserved the CSV header for empty exports and added regression coverage.",
  "checks": [
    {
      "command": "python3 -B -m unittest test_csv_export",
      "cwd": "/absolute/worker-workspace",
      "exit_code": 0,
      "result": "All export regression tests passed."
    }
  ],
  "unresolved": [],
  "evidence": ["/absolute/artifacts/export-tests.log"]
}
```

Use `partial` or `blocked` when acceptance remains unmet. Checks record what actually ran; use a null exit code when execution is unavailable, not a guessed success. A completed report requires executed passing checks and no unresolved criteria. Reference real evidence only; do not invent a log file to fill the example. Missing fields, invalid JSON, oversized reports or contradictory completion claims are unverified. Raw output remains available for targeted diagnosis.

The `checks` array records final required verification of the delivered state. Preserve pre-fix reproductions and superseded failures in evidence references; a repaired historical failure is not a current unmet criterion. Do not omit any still-required verification to claim completion.

## Collection and Acceptance

The DeepSeek runner requests this format and writes `worker-result.json` beside `final.txt`, the full logs, patch and receipt. Changed paths come from the runner's Git observation, not the worker's summary. An otherwise successful CLI execution with incomplete result evidence returns a nonzero result-incomplete outcome; existing process/scope/cleanup failures retain precedence.

For a native writer, save its final report outside the repository and use the same helper. Supply changed paths only from a scoped before/after comparison or patch; do not attribute another worker's changes in a shared workspace to this writer. If no reliable path observation exists, preserve unknown provenance. Read-only scouts keep their compact evidence response and do not need a writing report.

```bash
python3 scripts/worker_result.py \
  --report /absolute/artifacts/final.txt \
  --changed-paths /absolute/artifacts/changed-paths.txt \
  --output /absolute/artifacts/worker-result.json
```

Paths above are relative to the skill directory. Omit `--changed-paths` when no scoped Git observation is available. The normalized record distinguishes Git-observed paths from optional worker-reported paths and preserves a raw-copy reference. It caps raw reports and normalized output at 32 KiB, with smaller field limits; oversized content remains in raw artifacts and cannot produce a completed result. `status_source` distinguishes the worker claim from report validation, not independent correctness.

Helper exits are 0 for a consistent completed claim, 1 for partial/blocked, 3 for unverified and 2 for invalid CLI arguments. The DSH runner uses exit 76 / `result_incomplete` when other execution checks succeeded but the result is incomplete; it retains process/scope/cleanup/metadata failure precedence. Consult runner/manifest status as well as the worker claim: a completed report alone cannot override an execution failure.

Read the compact result first, then inspect the relevant diff and check evidence. A parsing/collection issue does not justify rerunning the implementation automatically: recover existing evidence when possible. A passing self-check plus passing root acceptance ends delivery. Only a concrete remaining defect or verification gap can trigger the bounded native continuation in `execution-flow.md`.
