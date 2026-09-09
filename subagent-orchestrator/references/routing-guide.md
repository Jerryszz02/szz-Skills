# Routing Guide

Optimize main-model work and successful task completion. Delegation can reduce main-model context and still increase total tokens; do not equate model names, lower unit prices, or parallelism with measured savings.

## Decision Matrix

| Task shape | Route | Constraints |
| --- | --- | --- |
| Known small edit, short supplied-code explanation, bounded deterministic check | Main manager | No ceremonial worker; stop direct diagnosis when exploration grows. |
| Bounded text/code scouting, call tracing, log extraction, specified verification | Spark (`medium`) → Luna (`low`) → manager | Apply `spark-worker.md`; compact read-only packet, no source writes or external/Terra fallback. |
| Broader read-only review or failure analysis | Luna (`low`) → manager | Evidence only; manager owns uncertain diagnosis and risk decisions. |
| Source-writing implementation, tests, fixes, documentation | DeepSeek → Kimi → Spark → Luna → Terra | DeepSeek stays first; Spark needs a fully specified small slice. Native writers use `medium`. |
| Patch application and mechanical integration | Spark (`medium`) → Luna (`medium`) → Terra (`medium`) → main manager | Skip Spark unless fully specified and mechanical; serialize writes in the target workspace. |
| Architecture, risk judgments, semantic conflicts, final acceptance | Main manager | Delegate evidence gathering; retain decisions. |

## Applying the Gate

- Before substantial execution, inspect rules/Git state and at most two small targeted discovery batches. If further searching, tracing, or failure analysis is needed, delegate a bounded question. Unknown target paths are a reason for read-only scouting, not for the manager to finish discovery first. This starter limit is a policy to evaluate, not a token estimate.
- Known small local edits, short supplied-code explanations, and deterministic checks with bounded output may stay direct. A failing check becomes a new routing decision; do not consume bulk logs in the manager. Architecture uncertainty does not exempt evidence gathering from delegation.
- For implementation, the root defines observable acceptance and write ownership. One worker may implement and run relevant tests. Reuse evidence and workers when their route, effort and permissions fit; do not force scout → executor → verifier handoffs or silently upgrade a scout to write access.
- Sequential work is eligible only when the active dispatch tool permits it. For a native tool requiring independent work alongside useful manager work, identify that work honestly; do not invent busywork or relabel the same blocked call through another route. If no permitted route fits, state the concrete constraint and take over.
- Before substantial work, briefly identify the delegated slice and manager decisions. After dispatch record the actual agent ID or runner artifact directory. Distinguish missing skill, direct exception, blocked dispatch, worker failure, and accepted worker result. A plan is not proof of execution.

Skill discovery and text instructions are not runtime enforcement. Check the loaded path/version and tool restrictions before diagnosing failure; reload the registry after installation updates. Global policy is optional user configuration: see `global-policy.md`.

## Availability and Context

1. Apply `spark-worker.md` before selecting Spark: bounded read-only evidence uses Spark (`medium`) → Luna (`low`) → manager; broader analysis starts at Luna. Use `read-only-worker.md` without external provider probing. Check support in the active dispatch tool, not the main-task model picker. Skip unsupported models/efforts with a reason; do not invent aliases or bypass restrictions through a new task, CLI, or custom config.
2. For source-writing execution, confirm `dsh` is executable, `dsh --profile headless --help` succeeds, external boundaries below are satisfied, and the packet passes preflight. Then use `scripts/run-dsh-worker.sh`. DeepSeek/Kimi retain their configured provider reasoning settings; native `low`/`medium` tiers do not apply to external CLIs.
3. If DeepSeek is unavailable or fails, use Kimi when permitted through `scripts/run-kimi-worker.sh`, then native Spark, Luna and Terra (`medium`) within budget. Skip Spark if its eligibility or runtime gate fails; missing native support never moves it ahead of DeepSeek/Kimi. Check actual tool callability, not just catalog entries. Record skipped-route reasons.
4. Fully specified mechanical patch integration starts at eligible Spark (`medium`), otherwise Luna (`medium`), then Terra and manager. External runners start from committed HEAD and cannot verify uncommitted integrated changes. Confirm native access to the target; otherwise the manager integrates there. Verification-only work uses the read-only route, while a writer can run its own relevant checks.
5. Record observed model evidence separately from requested aliases. Never inherit full parent history or use Sol.

## External Worker Boundary

- Detached worktrees isolate Git changes, not operating-system access. Do not send secrets, credentials, cookies, private keys, `.env` values, private sessions, or account access tasks.
- External workers exclude authentication, payments, security conclusions, migrations, destructive Git operations, and dependencies on uncommitted main-workspace changes.
- Require HEAD-only dependencies and bounded allowed/forbidden paths. Do not bypass dirty-path preflight or broaden external read scope to the whole repository. Native read-only scope does not change external runner contracts.
- Honor existing provider/data authorization. A denied external transfer cannot be routed through another external provider as a workaround; use a permitted native route.
- Never automatically apply external patches or create project `.codex/config.toml` or custom agent TOML files.

## Native Spawn Gate

Only the root may dispatch. Immediately before each `spawn_agent`:

1. Call `list_agents`; count live workers plus root against the active runtime limit.
2. When no slot remains, queue or wait. Do not hardcode an older concurrency limit.
3. Pass explicit `model`, `reasoning_effort`, `fork_turns: "none"`, and the route's task packet. Prohibit all nested delegation.

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
- At most **1 targeted retry on the same route**. Use it only for a precise, fixable failure; otherwise advance through the role's fallback order if one exists; read-only Spark may fall back to Luna, then returns to the manager. Both limits above still apply.
- Missing executables, denied dispatch, and preflight failures before model execution do not consume execution attempts. Once model execution starts, its failure and token cost count, even when no receipt is recoverable. Unknown launch state is conservatively counted.
- When either limit is exhausted, stop worker recovery and return the unresolved criterion to the main manager. The manager may complete a bounded fix directly or report a real blocker; it must not launch a fresh worker loop under a new name.

The root tracks these limits in its ledger; existing one-shot runners do not enforce a cross-worker budget. No strict token or spend cap is implied when the runtime lacks a stop mechanism. Record every model attempt, failed attempt, and missing receipt for accounting.

## Context and Return Budget

- Task packets carry relevant facts and paths, not whole conversation history or broad copied files. Workers read owned code directly. Prefer one cohesive slice to many trivial ones.
- Target at most 250 words in each worker's final prose: status, changed paths, concise result, exact checks/exit codes, blockers, and artifact locations. Put full logs and long evidence in files. Expand only for an actionable issue that cannot be represented safely in that budget.
- Request updates on completion, failure, or a decision needed. Do not poll full logs or require routine narration. The manager reads critical evidence and actual diffs without replaying the worker's entire search.
