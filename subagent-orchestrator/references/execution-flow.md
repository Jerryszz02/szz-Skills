# Compact Execution Flow

Use after choosing a delegated slice or root-approved mechanical integration. The manager owns decisions and acceptance; deterministic tools handle routine coordination.

## One Owner Through Self-Check

- Keep one active worker for this user task across native and external routes and run it serially. Dispatch the next route only after the previous execution has stopped and its result/evidence is recorded. Spare runtime slots never justify another worker.
- Roles and stages are flexible. A read-only worker can gather code evidence, the manager can decide the plan, and a writer can implement; a task with a clear plan can go directly to the writer. Do not require either this sequence or one worker for the whole task. Batch related work into each useful question/outcome, and reuse a worker while scope, capability and permissions fit. A writer normally owns implementation, related tests/docs and in-scope self-correction. Preserve accepted evidence across any role change.
- Before dispatch the manager reads only instructions/state, essential interfaces and acceptance blockers - not a full scout pass or a pre-solved implementation. Give one writer implementation and related verification. Include exact commands, scope and completion criteria in the original packet. It inspects its diff and fixes in-scope issues before first delivery; missing dependencies, interface changes and new requirements return to the manager.
- Workers use `fork none`, paths and accepted decisions plus precise acceptance criteria - not whole chat, files or logs. Keep tools on bounded excerpts and save bulky evidence in artifacts.
- Check cheap environment assumptions before dispatch. Supply existing dependency paths only after verifying them; share prepared acceptance commands where available. Do not independently rebuild elaborate test harnesses in every role.
- Writers return [worker-result.json](worker-result.md): reported outcome, changed paths, command/cwd/exit codes, unresolved criteria and evidence references. Keep bulk logs and implementation files outside the reply; read-only evidence can retain its compact prose format.
- Manager acceptance starts from the worker result, the actual diff/scope and critical evidence; inspect focused hunks or files if needed rather than re-exploring the repository or reading live reasoning/full logs. Confirm the evidence still applies to the current revision; refresh only the affected evidence if state changed. Then check the integrated state. Self-check does not replace final acceptance or required visual inspection. Reuse valid checks for unchanged state; repeat checks only for changed state, failures or unresolved risks.
- Self-check remains part of first delivery. Passing final acceptance ends the slice; do not add a routine second worker review or repeat unchanged broad checks.

## Stop Before and After Green

- Apply these rules before first delivery and after: self-check the agreed requirements, fix concrete in-scope defects, then deliver immediately once the required checks pass and no criterion is unresolved.
- Do not add an unsolicited audit, hardening, feature expansion or repeated broad checks after green.
- On the same environment/capability failure recurring without new evidence or a concrete changed condition, stop and report the blocker instead of looping through browser/install/tool experiments. A precise hypothesis justifies one bounded retry; do not invent a hard token or turn cap.
- These are instruction-level safeguards, not runtime enforcement: they guide the worker and manager but add no callbacks or hard stop.

## Correct an Actual Acceptance Failure

After delivery, classify the evidence before choosing another execution:

- A concrete local defect or missing verification in the original scope: prefer the original native writer when it remains available, its permissions/role still fit, and the active runtime permits continuation. Use that runtime's follow-up operation with the recorded agent ID/name, not a new spawn or a full replay of the packet. Send only the unmet criterion, focused reproduction/evidence, the relevant workspace delta and the remaining recovery allowance. Do not silently turn a read-only worker into a writer.
- A process still running after a wait timeout: wait on the same execution; this is not a new attempt and does not justify a backup worker.
- Missing dependencies, invalid paths, permissions or network failures: diagnose the environment first. Switching models is not a repair for unchanged environmental conditions.
- Changed requirements, shared interfaces or a semantic conflict: root decides the scope/plan first. An unavailable writer, a repeated defect after its one targeted retry, or a clear capability limit can use the next permitted route or root takeover within the existing budget.

Each post-delivery follow-up keeps the slice ID, increments the attempt, consumes one task recovery and records only its incremental usage. Preserve the limits in `routing-guide.md`: three executions per slice, two recoveries per task, one targeted retry per route. No failure means no follow-up. DeepSeek's runner is one-shot: a later attempt uses a fresh HEAD-only worktree and must satisfy the original dirty-path and scope checks; do not imply session continuation.

## Wait Without Repeated Model Decisions

The DSH runner is synchronous: it waits for the CLI, captures artifacts, checks scope and writes a result and receipt. Launch once. A tool returning a running session is not a failed worker or a reason to inspect logs.

1. Prefer completion/event notification supported by the active runtime. For native workers use its wait API; for a running shell use the same session's wait/read API.
2. Address only necessary independent manager decisions that remain; otherwise wait without inventing work or redoing the worker's investigation. When needed, use a bounded wait within current tool/instruction limits (at most 60 seconds per blocking wait on this host). Timeout keeps the same attempt; do not interleave clock calls, short sleeps, log tails and reasoning about unchanged progress.
3. Read the compact final result once. Never read a live reasoning stream for progress. Inspect a specific log excerpt only after failure, meaningful change, a user status request or a deadline requiring a decision.

Waiting uses the same execution; do not start a speculative backup worker while one is running. This reduces avoidable model re-entry; it cannot add callbacks, eliminate mandatory wakeups or provide a hard token cap. Pending is not failed or free; interrupted/unknown launches remain counted. Before stopping/restarting anything, check ownership and current state.

## Root-Approved Mechanical Integration

Do not dispatch an agent merely to apply a patch, collect receipts or run fixed checks. After reviewing the exact patch and evidence, serialize target writers, record HEAD/dirty state, then invoke this helper from the skill directory:

```bash
python3 scripts/apply_approved_patch.py \
  --cwd /absolute/target-repository \
  --patch /absolute/artifacts/changes.patch \
  --sha256 APPROVED_SHA256 \
  --expected-head EXPECTED_FULL_HEAD \
  --task-file /absolute/artifacts/task.md \
  --apply
```

Omit `--apply` for check-only. The digest must identify what root actually reviewed; computing a digest is not approval. Reuse the original packet to preserve scope.

Only ordinary text additions, edits and deletions are supported, including content-only edits and deletions of existing executable text files. New executable files remain unsupported. The expected HEAD must exactly match the repository's full SHA-1 or SHA-256 object ID. The helper verifies hash, HEAD, patch-derived paths, packet scope, symlink boundaries, overlapping staged/unstaged/untracked/ignored data and Git applicability. Paths whose normalization changes their identity, case/Unicode aliases and touched paths with assume-unchanged/skip-worktree flags are conservatively rejected. It preserves unrelated dirty work and returns compact JSON. It never launches a model, runs verification commands or commits. Run the named checks on the integrated state afterward and batch concise results.

Rejection needs manager diagnosis, not a fallback bypass. Binary files, rename/copy or mode changes require a separately reviewed procedure; semantic conflicts return to the manager. Serialize all target writers: this is not a cross-process lock or OS sandbox. No three-way merge, partial rejects, staging or automatic rollback.

Only additional independently useful integration work should pass the gate and native mechanical route. External HEAD-only workers cannot validate uncommitted target integration.

## Collect Once, Preserve Unknowns

Reuse runner receipts rather than asking a model to reconstruct them. Native attempts use the existing scoped collector where authorized; otherwise record null usage with the runtime limitation. Keep receipts outside source and account for all launched, failed and corrective attempts.

At task end run `summarize_usage.py` once. Newly completed attempts or corrected evidence justify refreshing it; unchanged progress does not. Measurement uses `usage-evaluation.md`; ordinary execution does not need the evaluation handbook.
