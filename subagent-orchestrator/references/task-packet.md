# Task Packet Contract

For native read-only tasks, use the compact packet in `read-only-worker.md` instead. Use the following template for external execution and native source-writing tasks. Each packet should cover a complete useful question or independently verifiable outcome, with related work batched together. Roles are optional and serial: a read-only result may inform the manager's plan before implementation, or a writer may investigate locally, implement, test and self-correct in one packet. Do not impose a fixed sequence or a different worker for every file/phase. Include stable slice ID, role, attempt number, remaining task recovery budget, and artifact output directory in the Objective or additional sections. These orchestration fields are tracked by the root; the external packet validator only enforces its existing required sections.

```markdown
# Task Packet

## Objective

Describe the observable result to produce.

## Dependencies

Write `none` when the outcome depends on no prior result, or list the decisions and task results that must exist first.

## Allowed paths

- path/to/file
- path/to/directory/**

## Forbidden paths

- .git/**
- path/to/shared-contract/**

## Acceptance criteria

- Observable criterion 1
- Observable criterion 2

## Required verification

- Exact test, lint, type-check, build, or inspection command

## Explicit non-goals

- Work that must not be attempted

## Nested delegation

forbidden

## HEAD-only dependency

yes
```

Include implementation, related tests and in-scope self-correction in one writer's responsibility. Supply paths and accepted decisions plus precise acceptance criteria, not whole chat, files or logs. Name available acceptance commands/dependencies so it can self-check before first delivery. State the stopping rule: self-check the agreed requirements, fix concrete in-scope defects, then deliver immediately once checks pass and no criterion is unresolved; no unsolicited audit, hardening or repeated broad checks after green, and a recurring environment/capability failure returns as a blocker instead of a tool/install loop. Return unresolved environment/interface decisions to root. Put prose in Dependencies, not among Allowed/Forbidden path bullets; validate the packet once before launch. See `execution-flow.md` for waiting, handoffs and recovery accounting.

## Native Worker Additions

For Spark, first apply `spark-worker.md`; keep DeepSeek ahead of it on source-writing routes. Also state:

- Role, required model, and required reasoning level supported by the active tool.
- For a Spark writer: manager-approved plan, exact inputs/outputs and edge cases, owned files, non-goals, and exact verification commands with cwd and expected result. Missing business rules or an unconfirmed cause return to the manager; do not design them independently.
- Explicitly run the required checks and report command/cwd/exit code plus a concise result. Do not delete tests, relax assertions, or alter requirements to make checks pass. UI work needs separate visual acceptance by a capable manager/tool; implementation is not visual verification.
- `fork_turns: "none"`; put all required context in the task packet instead of replaying parent history.
- Read-only or workspace-write permission, absolute target workspace, permitted read scope and owned write paths.
- For integration: starting HEAD/dirty-path inventory, exact root-approved patch paths and digests, writer dependencies, required commands, and log destinations. Verification-only packets prohibit source repairs.
- Do not create an integration packet solely for fixed patch/check commands: root invokes deterministic tools. Additional independently useful integration must pass the work-mode gate.
- State `HEAD-only dependency: no` when inspecting current uncommitted changes. Native packets are not passed through the external HEAD-only validator.
- Writers return the JSON report in `worker-result.md`; preserve raw responses and bulk logs in artifacts. Read-only workers keep the compact evidence response in `read-only-worker.md`.
- Attempt number and remaining recovery allowance; workers report failures instead of spawning retries or silently expanding repairs.
- For a same-owner continuation, send only the unmet criterion, focused evidence, the workspace delta and the remaining budget; do not replay the whole packet or reset the attempt/recovery counts.
- The unified receipt fields required by `worker-receipt.md`.
- That the worker is not alone in the repository and must not revert unrelated changes.
- That `spawn_agent`, nested agents, and every other form of worker delegation are forbidden. Only the root/main agent may dispatch workers.

## External Worker Requirements

- `HEAD-only dependency` must be `yes`. This asserts that no required context exists only in the main workspace's uncommitted changes.
- Allowed paths must be repository-relative and narrower than the entire repository. `*`, `**`, `.`, absolute paths, and parent traversal are invalid.
- Anything outside allowed paths is denied even if it is not listed under forbidden paths. Forbidden paths take precedence.
- Do not include secrets, tokens, cookies, private keys, `.env` values, or private account context.

The DeepSeek runner validates the required headings and path scope, refuses dispatch when an allowed path already has uncommitted changes in the main workspace, and records all changed paths for main-agent review.

## Compact Handoffs

Provide relevant file paths, verified interface decisions, acceptance criteria, and focused failure evidence. Avoid copying whole files or the parent conversation. A scout returns evidence locations and unresolved questions; the manager reads enough cited evidence to decide the plan. Do not make a second worker rediscover accepted findings.

## External Commands

Use a separate empty output directory for each attempt:

```bash
subagent-orchestrator/scripts/run-dsh-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory
```

DeepSeek keeps its configured provider reasoning settings; do not assign native `medium` to it. Runner failures do not authorize bypassing scope or recovery limits. Read the external boundaries in `routing-guide.md` before dispatch.
