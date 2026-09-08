# Routing Guide

Optimize main-model work and successful task completion. Delegation can reduce main-model context and still increase total tokens; do not equate model names, lower unit prices, or parallelism with measured savings.

## Decision Matrix

| Task shape | Route | Constraints |
| --- | --- | --- |
| Tiny edit or handoff more expensive than direct work | Main manager | Briefly record the reason; no ceremonial worker. |
| Code discovery, evidence, implementation, tests, routine fixes, documentation | DeepSeek → Kimi → Luna → Terra | Bounded ownership and acceptance; follow dependencies sequentially when needed. |
| Mechanical integration and final combined-workspace checks | Luna → Terra → main manager | Explicit exception to execution order; serialize writes and use the actual target workspace. |
| Architecture, ambiguous debugging decisions, security judgments, semantic conflicts, final acceptance | Main manager | Delegate safe evidence gathering; retain decisions. External exclusions still apply to implementation. |

## Applying the Gate

- A release-readiness assessment can assign rule/test coverage, runtime performance, and build/resource evidence as bounded scouting slices. The manager defines release criteria and accepts the findings; it need not read every module before dispatching scouts.
- For a tiny skill wording correction, the manager can state that reading the relevant instructions, changing two documents, and validating them costs less than a worker handoff. This exception does not extend to unrelated implementation discovered later.
- Sequential dependencies alone do not justify keeping all execution in the main thread. Dispatch the next bounded slice after its inputs are ready. A dirty workspace excludes external HEAD-only routes for affected slices, not all permitted native work.
- Before substantial work, give a concise routing update: slices, worker route or concrete manager-only reason, and manager-owned decisions. When dispatch succeeds, identify the native agent ID or external runner artifact directory. A plan to dispatch is not evidence that a worker ran; report blocked routes and any manager takeover explicitly.

Skill discovery and text instructions are not runtime enforcement. If the skill is missing from the session, stale, or restricted by higher-priority instructions, stronger wording in this file cannot force dispatch. Check the loaded skill path/version and current tool permissions before diagnosing a routing failure; reload the skill registry after installation updates.

## Availability and Context

1. For execution, try DeepSeek first: confirm `dsh` is executable, `dsh --profile headless --help` succeeds, the packet passes runner preflight, and the data/task is permitted for that provider. Use `scripts/run-dsh-worker.sh`.
2. If DeepSeek is unavailable or fails the slice, use Kimi when permitted and callable through `scripts/run-kimi-worker.sh`.
3. If external routes cannot be used, inspect the live native tool for model overrides; select Luna, then Terra. A catalog entry alone is not proof of callability. Record skipped-route reasons, including context or authorization restrictions.
4. Native scouting uses explicit `reasoning_effort: "low"`; implementation and integration use `"medium"`. Never omit the model, inherit full parent history, or use Sol.
5. Integration starts at Luna even if DeepSeek is available. DeepSeek/Kimi runners start from committed HEAD and reject dirty allowed paths. A test run in that detached checkout does not verify the current combined workspace. Native access to the target must also be confirmed; if unavailable, the manager performs the integration/checks there.
6. Use the runtime model evidence when reporting actual models. Do not substitute a requested alias or self-reported model identity for observed metadata.

## Native Spawn Gate

Only the root may dispatch. Immediately before each `spawn_agent`:

1. Call `list_agents`; count live workers plus root against the active runtime limit.
2. When no slot remains, queue or wait. Do not hardcode an older concurrency limit.
3. Pass explicit `model`, `reasoning_effort`, `fork_turns: "none"`, and the complete task packet. Prohibit all nested delegation.

## Integration Contract

- The root reviews scope, patch content, and evidence, then identifies the exact approved artifact (path plus digest) and target workspace. Worker creation does not itself authorize applying arbitrary patches.
- Finish target-workspace writers first. Use one integration/check worker at a time; independent work elsewhere may continue. Record starting HEAD and dirty paths, preserve unrelated edits, and check patch applicability before applying.
- Limit integration to approved patch application and mechanical operations. A semantic conflict, shared-interface change, new failure needing code changes, or out-of-scope operation returns evidence to the manager for a decision or a bounded repair packet.
- Name required commands and evidence output paths. Capture command, cwd, exit code, and concise result; store full logs outside the tracked project. Check the integrated state, including uncommitted changes. A stale pre-integration pass is insufficient.
- Verification alone must not silently repair source files. A corrective follow-up counts toward recovery limits. Root still owns final review, risk decisions, and acceptance; publication requires the task's existing authorization.

## Recovery Budget

Defaults for one user task, unless the user explicitly sets a different budget:

- At most **3 execution attempts per slice**, across all providers and native workers.
- At most **2 recovery attempts for the whole task**, shared across execution, integration, and verification slices. A recovery is any worker attempt after that slice's initial attempt, including provider fallback after execution failure and corrective follow-ups to an existing worker. Use stable slice IDs; renaming or splitting failed work does not reset its recovery count.
- At most **1 targeted retry on the same route**. Use it only for a precise, fixable failure; otherwise advance through the role's fallback order. Both limits above still apply.
- Missing executables, denied dispatch, and preflight failures before model execution do not consume execution attempts. Once model execution starts, its failure and token cost count, even when no receipt is recoverable. Unknown launch state is conservatively counted.
- When either limit is exhausted, stop worker recovery and return the unresolved criterion to the main manager. The manager may complete a bounded fix directly or report a real blocker; it must not launch a fresh worker loop under a new name.

The root tracks these limits in its ledger; existing one-shot runners do not enforce a cross-worker budget. No strict token or spend cap is implied when the runtime lacks a stop mechanism. Record every model attempt, failed attempt, and missing receipt for accounting.

## Context and Return Budget

- Task packets carry relevant facts and paths, not whole conversation history or broad copied files. Workers read owned code directly. Prefer one cohesive slice to many trivial ones.
- Target at most 250 words in each worker's final prose: status, changed paths, concise result, exact checks/exit codes, blockers, and artifact locations. Put full logs and long evidence in files. Expand only for an actionable issue that cannot be represented safely in that budget.
- Request updates on completion, failure, or a decision needed. Do not poll full logs or require routine narration. The manager reads critical evidence and actual diffs without replaying the worker's entire search.
