# Optional Global Delegation Policy

Copy the following into your global `~/.codex/AGENTS.md` (or the effective Codex home instruction file) if you want this policy across projects. This is a manual user action; skill synchronization does not install it. Project instructions and runtime restrictions still apply. Keep route mechanics in the skill.

```markdown
## Delegation

- The main agent owns requirements, planning, key decisions, and final acceptance.
- Use $subagent-orchestrator to choose direct work, deterministic tools or
  bounded delegation. Delegate independent work when compact handoff and
  acceptance avoid repeating it; honor runtime restrictions.
- Keep known small or tightly coupled work direct when handoff/acceptance would
  reconstruct it. Reassess if scope grows. Let one worker implement and self-test;
  use deterministic tools for waiting, receipts and approved patch application.
- If no permitted route fits or recovery is exhausted, state the concrete reason
  and take over. Do not claim token or quota savings without complete measurements.
```

An existing higher-priority policy that mandates delegation still governs until the user explicitly changes it. Updating or installing this skill does not silently replace that policy.
