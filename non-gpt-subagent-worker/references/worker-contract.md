# Worker Contract

Use this contract when preparing prompts for `non-gpt-subagent-worker` scripts.

## Required Task Fields

Every worker task should state:

- Goal: the exact question to answer or implementation slice to complete.
- Project root: absolute `cwd`.
- Provider and model: `ollama`, `lmstudio`, or `deepseek`, plus the model name.
- Permission: `read-only` or `workspace-write`.
- Ownership: files, modules, or responsibility boundaries the worker may touch.
- Output: the sections the main agent needs back.

## Worker Prompt Template

```text
You are an external worker for a Codex main agent.

Project root: <absolute path>
Permission: <read-only|workspace-write>
Ownership: <files/modules/responsibility>

Rules:
- Do not revert unrelated user or agent changes.
- Do not run destructive git commands.
- Do not print or request secrets, tokens, cookies, private keys, or .env values.
- If edits are allowed, keep them scoped to the ownership boundary.
- If blocked, report the blocker and the exact command or file that proved it.

Task:
<task>

Return:
- Summary
- Files inspected
- Files changed, if any
- Commands run
- Findings or implementation notes
- Remaining risks
```

## Suitable Tasks

- Locate relevant files or symbols.
- Explain a test failure from logs.
- Run a narrow read-only investigation.
- Implement a small change in a disjoint file set.
- Draft a candidate patch or migration approach.
- Compare two simple alternatives and cite evidence.

## Unsuitable Tasks

- Final architecture or product decision.
- Security-sensitive conclusion without main-agent validation.
- Credential, token, cookie, or `.env` handling.
- Destructive git operations.
- Work requiring browser login state or private account access.
- Broad refactors with overlapping ownership.

## Review Requirement

The main agent must review worker output before using it. For code changes, inspect the diff and run the smallest meaningful verification command. For analysis-only work, spot-check evidence before treating conclusions as facts.
