# Optional Global Delegation Policy

Copy the following into your global `~/.codex/AGENTS.md` (or the effective Codex home instruction file) if you want this policy across projects. This is a manual user action; skill synchronization does not install it. Project instructions and runtime restrictions still apply. Keep route mechanics in the skill.

```markdown
## Delegation

- The main agent owns requirements, planning, key decisions, and final acceptance.
- When permitted by the runtime, delegate sustained repository exploration,
  failure diagnosis, and independently verifiable implementation using
  $subagent-orchestrator. Do not finish exploration before handing it off.
- Use Luna with low reasoning for read-only delegated work.
- Handle known small edits, short supplied-code explanations, and bounded
  deterministic checks directly. Reuse workers and evidence; avoid duplicate work.
- If no permitted route fits or recovery is exhausted, state the concrete reason
  and take over. Do not claim token or quota savings without complete measurements.
```
