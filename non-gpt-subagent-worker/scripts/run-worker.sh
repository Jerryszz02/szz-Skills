#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: run-worker.sh --provider ollama|lmstudio|deepseek --model MODEL --cwd /abs/path --task-file FILE --output FILE [--sandbox workspace-write] [--dry-run]

Options:
  --provider    Worker provider: ollama, lmstudio, or deepseek.
  --model       Model name to use.
  --cwd         Absolute project path. Defaults to current directory.
  --sandbox     read-only or workspace-write. Defaults to workspace-write.
  --task-file   File containing the worker task prompt.
  --task        Inline worker task prompt.
  --output      File where the final worker result should be written.
  --dry-run     Print the selected route without calling the provider.
USAGE
}

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
provider=""
model=""
cwd="$(pwd)"
sandbox="workspace-write"
task_file=""
task=""
output=""
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) provider="${2:-}"; shift 2 ;;
    --model) model="${2:-}"; shift 2 ;;
    --cwd) cwd="${2:-}"; shift 2 ;;
    --sandbox) sandbox="${2:-}"; shift 2 ;;
    --task-file) task_file="${2:-}"; shift 2 ;;
    --task) task="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$provider" || -z "$model" || -z "$output" ]]; then
  usage >&2
  exit 2
fi

provider_key="$(printf '%s' "$provider" | tr '[:upper:]' '[:lower:]' | tr -d '-')"
case "$provider_key" in
  ollama)
    target="$script_dir/run-ollama-worker.sh"
    ;;
  lmstudio|lm\ studio)
    target="$script_dir/run-lmstudio-worker.sh"
    ;;
  deepseek)
    target="$script_dir/run-deepseek-worker.sh"
    ;;
  *)
    echo "Unknown provider: $provider" >&2
    exit 2
    ;;
esac

args=(--model "$model" --cwd "$cwd" --sandbox "$sandbox" --output "$output")
if [[ -n "$task_file" ]]; then
  args+=(--task-file "$task_file")
fi
if [[ -n "$task" ]]; then
  args+=(--task "$task")
fi
if [[ "$dry_run" -eq 1 ]]; then
  args+=(--dry-run)
fi

exec bash "$target" "${args[@]}"
