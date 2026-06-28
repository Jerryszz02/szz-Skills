# szz-Skills Agent Guide

## Project Purpose

This repository stores personal Codex skills. Each top-level skill directory is intended to be copied into `~/.codex/skills/<skill-name>/`.

## Skill Layout

- Every skill must include `SKILL.md` with YAML frontmatter containing only `name` and `description`.
- Keep `SKILL.md` focused on triggerable workflow instructions.
- Put detailed reusable guidance in `references/`.
- Put deterministic helpers in `scripts/` and cover them with focused tests when they exist.
- Put UI metadata in `agents/openai.yaml`; `interface.default_prompt` must mention the skill as `$skill-name`.

## Editing Rules

- Prefer small, reviewable diffs.
- Do not store secrets, tokens, cookies, private keys, or `.env` values in this repo.
- Update `README.md` whenever adding, removing, or renaming a skill.
- Validate changed skills with:

```bash
PYTHONPATH=/Users/jerryszz/.cache/uv/archive-v0/chiAkiAXGjq6ADkz \
python3 /Users/jerryszz/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
/Users/jerryszz/Desktop/Projects/szzSkills/<skill-name>
```

If that cached `PyYAML` path is unavailable, use any Python environment with `PyYAML` installed rather than adding project dependencies.

## Local Installation

Install a skill by copying its whole directory into `~/.codex/skills/`. Restart Codex after installing or updating a skill so the skill registry reloads.
