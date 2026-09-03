#!/usr/bin/env bash
set -euo pipefail

cwd=""
task_file=""
output_dir=""
model=""
kimi_bin="${KIMI_BIN:-kimi}"
run_root=""
worktree=""
worktree_registered=0
artifacts_complete=0

usage() {
  cat <<'USAGE'
Usage: run-kimi-worker.sh --cwd /absolute/project --task-file /absolute/task.md --output-dir /absolute/artifacts [--model MODEL]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd) cwd="${2:-}"; shift 2 ;;
    --task-file) task_file="${2:-}"; shift 2 ;;
    --output-dir) output_dir="${2:-}"; shift 2 ;;
    --model) model="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 64 ;;
  esac
done

if [[ -z "$cwd" || -z "$task_file" || -z "$output_dir" ]]; then
  usage >&2
  exit 64
fi
if [[ "$cwd" != /* || "$task_file" != /* || "$output_dir" != /* ]]; then
  echo "--cwd, --task-file, and --output-dir must be absolute paths." >&2
  exit 64
fi
if [[ ! -f "$task_file" ]]; then
  echo "Task file does not exist: $task_file" >&2
  exit 66
fi
if ! command -v "$kimi_bin" >/dev/null 2>&1; then
  echo "Kimi Code CLI is not installed or is not executable: $kimi_bin" >&2
  exit 69
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd -- "$script_dir/.." && pwd -P)"
python3 "$script_dir/task_packet.py" validate --task-file "$task_file"

if ! repo_root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)"; then
  echo "--cwd is not inside a Git repository: $cwd" >&2
  exit 66
fi
repo_root="$(cd -- "$repo_root" && pwd -P)"
git -C "$repo_root" rev-parse --verify HEAD >/dev/null

mkdir -p "$output_dir"
output_dir="$(cd -- "$output_dir" && pwd -P)"
case "$output_dir/" in
  "$repo_root/"*) echo "--output-dir must be outside the target repository." >&2; exit 65 ;;
esac
if find "$output_dir" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  echo "--output-dir must be empty: $output_dir" >&2
  exit 73
fi

preflight_paths="$output_dir/preflight-paths.txt"
{
  git -C "$repo_root" diff --name-only
  git -C "$repo_root" diff --cached --name-only
  git -C "$repo_root" ls-files --others --exclude-standard
} | awk 'NF' | sort -u > "$preflight_paths"
if ! python3 "$script_dir/task_packet.py" check-overlap --task-file "$task_file" --paths-file "$preflight_paths"; then
  echo "Kimi cannot start because an allowed path has uncommitted main-workspace changes." >&2
  exit 65
fi
rm -f "$preflight_paths"

run_root="$(mktemp -d "${TMPDIR:-/tmp}/subagent-orchestrator-kimi.XXXXXX")"
worktree="$run_root/worktree"

retain_on_failure() {
  local exit_code=$?
  if [[ "$artifacts_complete" -ne 1 && "$worktree_registered" -eq 1 ]]; then
    echo "Kimi worktree retained for recovery: $worktree" >&2
  fi
  exit "$exit_code"
}
trap retain_on_failure EXIT

git -C "$repo_root" worktree add --detach "$worktree" HEAD >/dev/null
worktree_registered=1
head_commit="$(git -C "$worktree" rev-parse HEAD)"

prompt="/goal $(<"$task_file")"
command=("$kimi_bin")
if [[ -n "$model" ]]; then
  command+=(--model "$model")
fi
command+=(
  --agent-file "$skill_dir/references/kimi-worker-agent.md"
  --prompt "$prompt"
  --output-format stream-json
)

set +e
(
  cd "$worktree"
  KIMI_CODE_EXPERIMENTAL_FLAG=1 "${command[@]}"
) >"$output_dir/events.jsonl" 2>"$output_dir/stderr.log"
kimi_exit_code=$?
set -e

git -C "$worktree" add -N -- . >/dev/null
git -C "$worktree" status --short > "$output_dir/status.txt"
git -C "$worktree" diff --name-only --no-ext-diff "$head_commit" -- | awk 'NF' | sort -u > "$output_dir/changed-paths.txt"
git -C "$worktree" diff --binary --no-ext-diff "$head_commit" -- > "$output_dir/changes.patch"
printf '%s\n' "$kimi_exit_code" > "$output_dir/exit-code"

scope_ok=true
if python3 "$script_dir/task_packet.py" check-paths \
  --task-file "$task_file" \
  --paths-file "$output_dir/changed-paths.txt" \
  >"$output_dir/scope-check.txt" 2>&1; then
  printf '%s\n' "scope check passed" > "$output_dir/scope-check.txt"
else
  scope_ok=false
fi

worktree_cleaned=true
if ! git -C "$repo_root" worktree remove --force "$worktree"; then
  worktree_cleaned=false
fi
if [[ "$worktree_cleaned" == true ]]; then
  worktree_registered=0
  rmdir "$run_root" 2>/dev/null || true
fi

runner_exit_code="$kimi_exit_code"
if [[ "$scope_ok" != true ]]; then
  runner_exit_code=65
elif [[ "$worktree_cleaned" != true ]]; then
  runner_exit_code=74
fi

worker_status="completed"
if [[ "$kimi_exit_code" -ne 0 ]]; then
  worker_status="failed"
fi
if [[ "$scope_ok" != true ]]; then
  worker_status="scope-rejected"
elif [[ "$worktree_cleaned" != true ]]; then
  worker_status="cleanup-failed"
fi

kimi_session_index="${KIMI_SESSION_INDEX:-$(python3 -c 'from pathlib import Path; print(Path.home() / ".kimi-code/session_index.jsonl")')}"
metadata_complete=true
if ! python3 "$script_dir/worker_receipt.py" kimi \
  --task-file "$task_file" \
  --events-file "$output_dir/events.jsonl" \
  --session-index "$kimi_session_index" \
  --requested-model "$model" \
  --status "$worker_status" \
  --output "$output_dir/worker-receipt.json" \
  --require-complete; then
  metadata_complete=false
  if [[ "$runner_exit_code" -eq 0 ]]; then
    runner_exit_code=75
    worker_status="metadata-incomplete"
    python3 "$script_dir/worker_receipt.py" kimi \
      --task-file "$task_file" \
      --events-file "$output_dir/events.jsonl" \
      --session-index "$kimi_session_index" \
      --requested-model "$model" \
      --status "$worker_status" \
      --output "$output_dir/worker-receipt.json"
  fi
fi

python3 - "$output_dir/manifest.json" "$output_dir/worker-receipt.json" "$repo_root" "$head_commit" \
  "$kimi_exit_code" "$runner_exit_code" "$scope_ok" "$worktree_cleaned" "$worktree" "$metadata_complete" <<'PY'
import json
import sys

(
    manifest_path,
    receipt_path,
    repo_root,
    head_commit,
    kimi_exit_code,
    runner_exit_code,
    scope_ok,
    worktree_cleaned,
    worktree_path,
    metadata_complete,
) = sys.argv[1:]

with open(receipt_path, encoding="utf-8") as handle:
    receipt = json.load(handle)

manifest = {
    "repo_root": repo_root,
    "head_commit": head_commit,
    "requested_model": receipt["requested_model"],
    "actual_model": receipt["actual_model"],
    "actual_models": receipt["actual_models"],
    "reasoning_effort": receipt["reasoning_effort"],
    "usage": receipt["usage"],
    "metadata_complete": metadata_complete == "true",
    "kimi_exit_code": int(kimi_exit_code),
    "runner_exit_code": int(runner_exit_code),
    "scope_ok": scope_ok == "true",
    "worktree_cleaned": worktree_cleaned == "true",
    "worktree_path": None if worktree_cleaned == "true" else worktree_path,
    "artifacts": [
        "events.jsonl",
        "stderr.log",
        "status.txt",
        "changed-paths.txt",
        "changes.patch",
        "exit-code",
        "scope-check.txt",
        "worker-receipt.json",
    ],
}

with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

artifacts_complete=1
trap - EXIT
exit "$runner_exit_code"
