# Task Packet Contract

Use this template for every delegated task. Keep each packet limited to one independently verifiable responsibility.

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
- Read-only or workspace-write permission.
- Expected response sections.
- That the worker is not alone in the repository and must not revert unrelated changes.
- That `spawn_agent`, nested agents, and every other form of worker delegation are forbidden. Only the root/main agent may dispatch workers.

## External Worker Requirements

- `HEAD-only dependency` must be `yes`. This asserts that no required context exists only in the main workspace's uncommitted changes.
- Allowed paths must be repository-relative and narrower than the entire repository. `*`, `**`, `.`, absolute paths, and parent traversal are invalid.
- Anything outside allowed paths is denied even if it is not listed under forbidden paths. Forbidden paths take precedence.
- Do not include secrets, tokens, cookies, private keys, `.env` values, or private account context.

The DeepSeek and Kimi runners validate the required headings and path scope, refuse dispatch when an allowed path already has uncommitted changes in the main workspace, and record all changed paths for main-agent review.
