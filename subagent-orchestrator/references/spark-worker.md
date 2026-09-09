# Spark Worker Eligibility

Use Spark as a focused scout or executor of an existing plan. This is a task-routing preference, not a measured ranking or cost claim. DeepSeek remains the first source-writing choice; preserve **DeepSeek → Kimi → Spark → Luna → Terra** and skip ineligible or unavailable routes.

## Runtime Gate

Use the exact model `gpt-5.3-codex-spark`, explicit `reasoning_effort: "medium"`, `fork_turns: "none"` only when the active subagent tool supports that combination. Medium is this skill's starting policy, not a benchmark result. Pro access or availability in the main-task model picker does not prove subagent availability. Do not create a separate user task, custom agent/config, or CLI workaround to force dispatch. Record a preflight skip, then follow the existing fallback and shared recovery budget.

## Suitable Slices

| Task | Required boundary |
| --- | --- |
| Locate entry points, trace a call chain, collect code evidence | Start read-only; return paths, symbols, line numbers, brief relationships and unresolved questions. No speculative root cause presented as fact. |
| Known-cause small fix | Manager confirms cause and fix scope; no redesign or adjacent cleanup. |
| Focused UI iteration | Supply text requirements for spacing, breakpoints, states or copy; manager separately checks rendered results. |
| Small function, validator or script | Manager supplies inputs, outputs and edge cases; no invented business rules. |
| Repetitive maintenance | Follow an accepted pattern; use deterministic bulk tools first and inspect the diff. |
| Specified tests, log extraction, local regression coverage | Supply exact commands and expected behavior; no deleting tests, weakening assertions or changing requirements to get green. |
| Mechanical integration | Apply only the identified approved patch in the current target workspace; return semantic conflicts to the manager. |

Unknown files are compatible with a bounded scout question. Unknown system behavior, open-ended root-cause diagnosis, architectural tradeoffs, security conclusions and final acceptance belong to the manager; a scout may gather specific supporting evidence. Broader read-only review stays on the Luna route. A known tiny edit or deterministic check can still stay direct.

## Handoff and Acceptance

Begin uncertain tasks with the compact read-only packet in `read-only-worker.md`. Writing requires a separate, explicit packet from `task-packet.md` after the manager decides the plan and ownership; do not silently promote a scout. For a changed role, reassess provider priority and permissions rather than keeping Spark merely because it has context.

Tell every executor to run the named verification commands, with cwd and expected results. Require actual command/cwd/exit code and concise failure evidence; “implemented” is not “verified.” Save long logs outside tracked source and return an evidence index. If a new assumption, out-of-scope failure or semantic conflict appears, stop expansion and return it to the manager. Recovery/fallback remains bounded by `routing-guide.md`.

Spark is documented as text-only: the manager must translate screenshot requirements into concrete text and perform visual acceptance with a capable model/tool. Do not send images to Spark or accept a claimed screenshot review. If visual evidence cannot be checked, report that acceptance as pending.

## Official Basis

Checked 2026-09-09: [OpenAI model guidance](https://learn.chatgpt.com/docs/models) describes Spark as a text-only model for rapid coding iteration. [OpenAI subagent examples](https://learn.chatgpt.com/docs/agent-configuration/subagents) use Spark at medium for a read-only code explorer and for a small fix after reproduction. Those examples support this role split; they do not establish this runtime's availability or comparative savings. Recheck live tool support at dispatch.
