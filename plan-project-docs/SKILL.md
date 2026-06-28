---
name: plan-project-docs
description: Turn a completed implementation plan into project-local planning documents under docs/planning. Use after Codex produces a formal plan for a large engineering project, major feature, architecture change, or product direction, especially when the user asks to save the plan, generate PRD-style docs, create project guidance, or prepare reference documents before implementation.
---

# Plan Project Docs

Generate only the project guidance documents needed for the completed plan and the actual repository architecture. The output is a maintainable `docs/planning/` folder that future implementation work can cite.

## Workflow

1. Identify the source plan.
   - Use the most recent formal plan in the conversation, including `<proposed_plan>` content when present.
   - If multiple plans conflict, use the newest user-approved or user-provided version.
   - If there is no concrete plan, ask for one instead of inventing scope.
2. Inspect the target project before writing.
   - Confirm the project root from the current working directory or explicit user path.
   - Read likely sources of truth first: `README*`, `AGENTS.md`, existing `docs/`, package manifests, build manifests, route/API/schema files, and visible app entrypoints.
   - Use read-only commands for discovery. Do not infer APIs, database tables, deployment targets, or product behavior from filenames alone.
3. Read `references/document-catalog.md` and select the minimum document set.
   - Generate documents only when the plan and repo evidence meet the catalog's "Need when" rules.
   - Do not generate `api-design.md` without API work, `database-design.md` without persistence changes, or `release-plan.md` without deployment/release work.
   - For small bug fixes or narrow refactors, generate only the smallest useful planning note and the index.
4. Write or update `docs/planning/`.
   - Create `docs/planning/README.md` as the index for every run.
   - For each generated file, include: purpose, scope, plan-derived content, non-goals, and implementation or acceptance guidance.
   - If a target file already exists, merge new information into it and preserve human-written content. Do not overwrite unrelated sections.
   - Mark missing plan details as `待确认`; do not fabricate requirements, schemas, routes, credentials, timelines, or ownership.
5. Report what changed.
   - List generated and updated planning files.
   - List intentionally skipped catalog documents with short reasons.
   - Mention any unresolved `待确认` items that could affect implementation.

## File Rules

- Write only under the target project's `docs/planning/` directory unless the user explicitly requests a different location.
- Do not modify product code, tests, config, secrets, `.env` files, dependency manifests, or deployment files.
- Do not paste secrets, tokens, private keys, cookie values, or environment variable values into planning documents.
- Keep documents concrete to the current plan. Avoid generic templates, speculative features, or broad architecture essays.
- Prefer Chinese output when the user is working in Chinese; preserve English technical names, paths, APIs, and commands.

## Index Requirements

`docs/planning/README.md` must include:

- the plan title or short description;
- the date of generation or update;
- the project root inspected;
- a table of generated or updated documents with one-line purpose statements;
- a table of skipped catalog documents with reasons;
- a short list of open questions or `待确认` items, if any.

## Document Requirements

Each generated planning file must include these sections unless a different structure is clearly better for that document type:

```markdown
# Document Title

## Purpose

## Scope

## Plan Details

## Non-Goals

## Implementation Guidance

## Acceptance Criteria

## Open Questions
```

Use concise prose and tables where they make implementation decisions easier to scan. Remove empty sections only when the file's purpose does not need them.

## Resources

- `references/document-catalog.md`: document selection rules, scope definitions, required content, and skip conditions.
