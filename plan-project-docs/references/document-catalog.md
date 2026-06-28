# Document Catalog

Use this catalog to decide which files to generate under `docs/planning/`. Generate the smallest set that materially helps future implementation.

## Selection Rules

- Always generate or update `README.md` as the planning index.
- Prefer fewer, concrete documents over a full template set.
- A document is needed when the plan changes behavior, architecture, data, APIs, user flows, security posture, release process, or operations.
- A document is not needed when it would only restate the plan, contain placeholders, or describe a subsystem the plan does not touch.
- If evidence is incomplete but the document is still required, write `待确认` for unknowns and explain the dependency.

## Catalog

### `project-brief.md`

Purpose: define why the project exists and what outcome the plan is trying to achieve.

Need when:
- starting a new project;
- beginning a major feature or product direction;
- success criteria, audience, scope, or constraints need to stay visible across later work.

Do not need when:
- the task is a narrow bug fix, cleanup, or small implementation detail;
- the repository already has an up-to-date brief covering the same plan.

Include:
- background and problem statement;
- target users or operators;
- goals and non-goals;
- success metrics or acceptance outcomes;
- scope boundaries;
- constraints, assumptions, and dependencies.

### `prd.md`

Purpose: define the product behavior that must exist when implementation is complete.

Need when:
- the plan introduces or changes user-visible behavior;
- workflows, permissions, content, UX states, or business rules must be implemented;
- acceptance depends on product requirements rather than only code structure.

Do not need when:
- the change is internal-only and has no product behavior;
- the plan is purely infrastructure or developer tooling.

Include:
- users and use cases;
- functional requirements;
- non-functional requirements;
- states, permissions, and edge cases;
- acceptance criteria;
- explicit non-goals.

### `architecture.md`

Purpose: explain the system shape and boundaries that implementation must preserve.

Need when:
- the plan touches multiple modules, services, packages, or apps;
- there are important dependencies, data flows, deployment boundaries, or ownership boundaries;
- long-term maintainability or extensibility is a core concern.

Do not need when:
- changes are isolated to one component with obvious local behavior;
- an existing architecture doc already covers the same design and only needs a pointer from the index.

Include:
- module or service responsibilities;
- data/control flow;
- external dependencies;
- deployment/runtime shape when relevant;
- security and trust boundaries;
- important alternatives rejected.

### `technical-design.md`

Purpose: translate the plan into concrete implementation guidance.

Need when:
- implementation has non-trivial logic, sequencing, state handling, compatibility concerns, or integration details;
- another engineer should be able to implement without re-deciding the approach.

Do not need when:
- the change is a one-file mechanical edit or obvious bug fix;
- the plan itself is already a sufficiently detailed implementation spec.

Include:
- selected approach;
- affected subsystems;
- data/state flow;
- error handling and fallback behavior;
- compatibility constraints;
- task breakdown;
- acceptance guidance.

### `user-flow.md`

Purpose: describe how users or operators move through the experience.

Need when:
- the plan adds or changes UI, CLI, onboarding, permissions, or operational workflows;
- error, empty, loading, cancellation, or retry states matter.

Do not need when:
- there is no user or operator interaction change;
- behavior is entirely backend/internal.

Include:
- entry points and exits;
- primary flow;
- alternate and failure flows;
- permissions or role differences;
- UI/CLI states and copy-sensitive decisions;
- acceptance scenarios.

### `api-design.md`

Purpose: define service boundaries and request/response contracts.

Need when:
- the plan adds, removes, or changes HTTP/RPC/GraphQL/WebSocket/CLI/plugin APIs;
- clients and servers need a stable contract;
- error handling, auth, pagination, idempotency, or versioning matters.

Do not need when:
- no API contract changes;
- API behavior is already fully specified in an existing contract file and only needs an index pointer.

Include:
- endpoints or operations;
- request and response shapes;
- authentication and authorization;
- validation rules;
- errors and status codes;
- pagination, idempotency, and versioning when relevant;
- compatibility notes.

### `database-design.md`

Purpose: define persistent data changes.

Need when:
- the plan adds, removes, or changes tables, documents, collections, indexes, migrations, or durable storage semantics;
- data retention, backfill, consistency, or rollback matters.

Do not need when:
- there are no persistence changes;
- data changes are limited to in-memory state or local cache without durable schema implications.

Include:
- entities and relationships;
- fields and meanings;
- indexes and constraints;
- migration and rollback plan;
- data lifecycle and retention;
- backfill or compatibility notes.

### `security-privacy.md`

Purpose: record security, privacy, and trust-boundary decisions.

Need when:
- the plan handles user data, credentials, permissions, external services, file access, network calls, browser automation, payments, or sensitive operations;
- access control, auditability, data minimization, or abuse resistance matters.

Do not need when:
- the change has no meaningful security or privacy impact;
- the relevant controls are unchanged and already documented elsewhere.

Include:
- sensitive data and data classification;
- authentication and authorization;
- secrets handling;
- trust boundaries;
- audit/logging expectations;
- privacy constraints;
- threats, mitigations, and residual risks.

### `test-plan.md`

Purpose: define how implementation will be verified.

Need when:
- the plan changes behavior, architecture, data, APIs, or user workflows;
- acceptance criteria need executable or manual verification.

Do not need when:
- the change is documentation-only and the index already records review checks;
- the plan is a trivial text edit with no behavior impact.

Include:
- unit, integration, E2E, manual, performance, and security checks as applicable;
- fixtures or test data;
- regression scenarios;
- acceptance criteria;
- commands to run when known;
- risks not covered by tests.

### `release-plan.md`

Purpose: define how the change reaches users safely.

Need when:
- deployment, migration, feature flags, staged rollout, data backfill, or rollback strategy matters;
- the project has production users or operational risk.

Do not need when:
- the change is local-only, documentation-only, or not released through a deployment path;
- release mechanics are unchanged and trivial.

Include:
- rollout sequence;
- feature flags or staged exposure;
- migration and backfill order;
- rollback steps;
- monitoring and alerting;
- release checklist.

### `operations-runbook.md`

Purpose: help operators run and debug the resulting system.

Need when:
- the plan introduces or changes services, scheduled jobs, long-running processes, queues, external integrations, or production operations;
- future incidents need concrete commands or log locations.

Do not need when:
- no runtime or operational behavior changes;
- existing runbooks remain accurate and only need an index pointer.

Include:
- start/stop/restart procedures;
- configuration locations without secret values;
- logs and health checks;
- common failure modes;
- troubleshooting steps;
- backup, restore, and recovery notes when relevant.

### `decision-log.md`

Purpose: preserve important decisions and tradeoffs.

Need when:
- the plan chooses between materially different product, architecture, vendor, model, data, or release options;
- a future maintainer would otherwise re-open the same decision.

Do not need when:
- there are no meaningful alternatives or tradeoffs;
- decisions are minor implementation details.

Include:
- decision date;
- decision statement;
- context;
- options considered;
- rationale;
- consequences and follow-up triggers.
