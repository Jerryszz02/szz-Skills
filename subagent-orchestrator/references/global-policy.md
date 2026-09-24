# Optional Global Delegation Policy

Copy the following into your global `~/.codex/AGENTS.md` (or the effective Codex home instruction file) if you want this policy across projects. This is a manual user action; skill synchronization does not install it. Project instructions and runtime restrictions still apply. Keep route mechanics in the skill.

```markdown
## Delegation

- The main agent owns requirements, planning, key decisions, and final acceptance.
- Use $subagent-orchestrator only when the user explicitly invokes it or asks
  to use that skill. Do not activate it automatically for exploration,
  diagnosis, implementation, or general requests to use subagents.
- Once invoked, choose direct work, deterministic tools or bounded delegation;
  honor runtime restrictions.
- Start direct; invocation does not require a worker. Delegate a bounded part
  only when little shared context and a compact handoff can replace manager
  work without requiring it to be repeated.
- Keep known small or tightly coupled work direct when handoff/acceptance would
  reconstruct it. Reassess if scope grows.
- Keep one active worker for this user task across native and external routes
  and run it serially. Spare runtime slots never justify another worker, and a
  fallback starts only after the previous execution has stopped.
- Choose roles as needed, without a fixed sequence or a one-worker-per-task
  requirement. A read-only result can inform planning; a clear plan can go
  directly to a writer. Batch related work and reuse the same worker while
  scope, capability and permissions fit. Pass paths, accepted decisions and
  acceptance criteria, not whole chat or logs.
- Let one worker implement and self-check; use deterministic tools for waiting,
  receipts and approved patch application.
- Apply stopping rules before first delivery and after: self-check, fix
  concrete in-scope defects, then deliver once checks pass and no criterion is
  unresolved. No unsolicited audit or hardening after green; a recurring
  environment/capability failure returns as a blocker.
- If no permitted route fits or recovery is exhausted, state the concrete reason
  and take over. Do not claim token or quota savings without complete measurements.
```

An existing higher-priority policy that mandates delegation still governs until the user explicitly changes it. Updating or installing this skill does not silently replace that policy.
