#!/usr/bin/env bash

model=""
cwd="$(pwd)"
sandbox="workspace-write"
task_file=""
task=""
output=""
dry_run=0

parse_common_args() {
  local provider_name="$1"
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --model) model="${2:-}"; shift 2 ;;
      --cwd) cwd="${2:-}"; shift 2 ;;
      --sandbox) sandbox="${2:-}"; shift 2 ;;
      --task-file) task_file="${2:-}"; shift 2 ;;
      --task) task="${2:-}"; shift 2 ;;
      --output) output="${2:-}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      -h|--help) common_usage "$provider_name"; exit 0 ;;
      *) echo "Unknown argument: $1" >&2; common_usage "$provider_name" >&2; exit 2 ;;
    esac
  done

  if [[ -z "$model" || -z "$output" ]]; then
    common_usage "$provider_name" >&2
    exit 2
  fi
  if [[ -z "$task_file" && -z "$task" ]]; then
    echo "Either --task-file or --task is required." >&2
    exit 2
  fi
  if [[ "$sandbox" != "read-only" && "$sandbox" != "workspace-write" ]]; then
    echo "Unsupported sandbox: $sandbox" >&2
    exit 2
  fi
  if [[ "$cwd" != /* ]]; then
    echo "--cwd must be an absolute path." >&2
    exit 2
  fi
}

common_usage() {
  local provider_name="$1"
  cat <<USAGE
Usage: run-${provider_name}-worker.sh --model MODEL --cwd /abs/path --task-file FILE --output FILE [--sandbox workspace-write] [--dry-run]
USAGE
}

read_task() {
  if [[ -n "$task_file" ]]; then
    cat "$task_file"
  else
    printf '%s\n' "$task"
  fi
}

build_prompt_file() {
  local prompt_file="$1"
  {
    cat <<PROMPT
You are an external worker for a Codex main agent.

Project root: $cwd
Permission: $sandbox

Rules:
- You are not alone in the codebase; do not revert unrelated user or agent changes.
- Do not run destructive git commands.
- Do not print, request, or store secrets, tokens, cookies, private keys, or .env values.
- Keep any edits tightly scoped to the task.
- If blocked, report the blocker and the exact command or file that proved it.

Task:
PROMPT
    read_task
    cat <<'PROMPT'

Return:
- Summary
- Files inspected
- Files changed, if any
- Commands run
- Findings or implementation notes
- Remaining risks
PROMPT
  } > "$prompt_file"
}

quote_command() {
  python3 - "$@" <<'PY'
import shlex
import sys
print(" ".join(shlex.quote(arg) for arg in sys.argv[1:]))
PY
}

run_codex_local_worker() {
  local provider_name="$1"
  local prompt_file
  prompt_file="$(mktemp "${TMPDIR:-/tmp}/non-gpt-worker.XXXXXX")"
  trap 'rm -f "$prompt_file"' EXIT
  build_prompt_file "$prompt_file"
  mkdir -p "$(dirname "$output")"

  local cmd=(
    codex exec
    --oss
    --local-provider "$provider_name"
    -m "$model"
    -C "$cwd"
    --sandbox "$sandbox"
    --output-last-message "$output"
    -
  )

  if [[ "$dry_run" -eq 1 ]]; then
    quote_command "${cmd[@]}"
    printf ' < %s\n' "$prompt_file"
    exit 0
  fi

  if ! command -v codex >/dev/null 2>&1; then
    echo "codex command not found on PATH." >&2
    exit 127
  fi
  "${cmd[@]}" < "$prompt_file"
}
