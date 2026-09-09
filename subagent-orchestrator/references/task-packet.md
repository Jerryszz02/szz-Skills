# Task Packet Contract

For native read-only tasks, use the compact packet in `read-only-worker.md` instead. Use the following template for external execution and native source-writing tasks. Keep each packet limited to one independently verifiable responsibility. Include stable slice ID, role, attempt number, remaining task recovery budget, and artifact output directory in the Objective or additional sections. These orchestration fields are tracked by the root; the external packet validator only enforces its existing required sections.

```markdown
# Task Packet

## Objective

Describe the observable result to produce.

## Dependencies

Write `none` for parallel work, or list the decisions and task results that must exist first.

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

## Native Worker Additions

Also state:

- Role, required model, and required reasoning level.
- `fork_turns: "none"`; put all required context in the task packet instead of replaying parent history.
- Read-only or workspace-write permission, absolute target workspace, permitted read scope and owned write paths.
- For integration: starting HEAD/dirty-path inventory, exact root-approved patch paths and digests, writer dependencies, required commands, and log destinations. Verification-only packets prohibit source repairs.
- State `HEAD-only dependency: no` when inspecting current uncommitted changes. Native packets are not passed through the external HEAD-only validator.
- Expected response sections: status, changed paths, result, exact checks/exit codes, blockers, artifact pointers; target at most 250 words of final prose and save bulk logs to artifacts.
- Attempt number and remaining recovery allowance; workers report failures instead of spawning retries or silently expanding repairs.
- The unified receipt fields required by `worker-receipt.md`.
- That the worker is not alone in the repository and must not revert unrelated changes.
- That `spawn_agent`, nested agents, and every other form of worker delegation are forbidden. Only the root/main agent may dispatch workers.

## External Worker Requirements

- `HEAD-only dependency` must be `yes`. This asserts that no required context exists only in the main workspace's uncommitted changes.
- Allowed paths must be repository-relative and narrower than the entire repository. `*`, `**`, `.`, absolute paths, and parent traversal are invalid.
- Anything outside allowed paths is denied even if it is not listed under forbidden paths. Forbidden paths take precedence.
- Do not include secrets, tokens, cookies, private keys, `.env` values, or private account context.

The DeepSeek and Kimi runners validate the required headings and path scope, refuse dispatch when an allowed path already has uncommitted changes in the main workspace, and record all changed paths for main-agent review.

## Compact Handoffs

Provide relevant file paths, verified interface decisions, acceptance criteria, and focused failure evidence. Avoid copying whole files or the parent conversation. A scout returns evidence locations and unresolved questions; the manager reads enough cited evidence to decide the plan. Do not make a second worker rediscover accepted findings.

## External Commands

Use a separate empty output directory for each attempt:

```bash
subagent-orchestrator/scripts/run-dsh-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory

subagent-orchestrator/scripts/run-kimi-worker.sh \
  --cwd /absolute/project/path \
  --task-file /absolute/task-packet.md \
  --output-dir /absolute/artifact-directory
```

External workers keep their configured provider reasoning settings; do not assign native `medium` to DeepSeek/Kimi. Kimi uses its configured default model unless the user or current configuration requires `--model <alias>`. Runner failures do not authorize bypassing scope or recovery limits. Read the external boundaries in `routing-guide.md` before dispatch.
