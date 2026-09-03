#!/usr/bin/env bash
set -euo pipefail

cwd=""
task_file=""
output_dir=""
dsh_bin="${DSH_BIN:-dsh}"
run_root=""
worktree=""
worktree_registered=0
artifacts_complete=0

usage() {
  cat <<'USAGE'
Usage: run-dsh-worker.sh --cwd /absolute/project --task-file /absolute/task.md --output-dir /absolute/artifacts
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd) cwd="${2:-}"; shift 2 ;;
    --task-file) task_file="${2:-}"; shift 2 ;;
    --output-dir) output_dir="${2:-}"; shift 2 ;;
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
if ! command -v "$dsh_bin" >/dev/null 2>&1; then
  echo "DeepSeek Harness CLI is not installed or is not executable: $dsh_bin" >&2
  exit 69
fi
if ! "$dsh_bin" --profile headless --help >/dev/null 2>&1; then
  echo "DeepSeek Harness headless profile preflight failed." >&2
  exit 69
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
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
  echo "DeepSeek cannot start because an allowed path has uncommitted main-workspace changes." >&2
  exit 65
fi
rm -f "$preflight_paths"

run_root="$(mktemp -d "${TMPDIR:-/tmp}/subagent-orchestrator-dsh.XXXXXX")"
worktree="$run_root/worktree"

retain_on_failure() {
  local exit_code=$?
  if [[ "$artifacts_complete" -ne 1 && "$worktree_registered" -eq 1 ]]; then
    echo "DeepSeek worktree retained for recovery: $worktree" >&2
  fi
  exit "$exit_code"
}
trap retain_on_failure EXIT

git -C "$repo_root" worktree add --detach "$worktree" HEAD >/dev/null
worktree_registered=1
head_commit="$(git -C "$worktree" rev-parse HEAD)"

prompt="$(cat <<'PROMPT'
You are a bounded implementation worker controlled by a root/main agent.
Follow the task packet exactly. Do not call spawn_agent, create child workers,
or delegate any part of the task. Modify only Allowed paths and do not expand
scope. Do not create commits, branches, worktrees, or change Git configuration.
Do not read, request, print, or store secrets. Run the required verification and
inspect your diff. Finish with status, files changed, implementation summary,
verification results, and blockers.
PROMPT
)"$'\n\n'"$(<"$task_file")"

set +e
(
  cd "$worktree"
  "$dsh_bin" --profile headless "$prompt"
) >"$output_dir/final.txt" 2>"$output_dir/reasoning.log"
dsh_exit_code=$?
set -e

git -C "$worktree" add -N -- . >/dev/null
git -C "$worktree" status --short > "$output_dir/status.txt"
git -C "$worktree" diff --name-only --no-ext-diff | awk 'NF' | sort -u > "$output_dir/changed-paths.txt"
git -C "$worktree" diff --binary --no-ext-diff > "$output_dir/changes.patch"
printf '%s\n' "$dsh_exit_code" > "$output_dir/exit-code"

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

runner_exit_code="$dsh_exit_code"
if [[ "$scope_ok" != true ]]; then
  runner_exit_code=65
elif [[ "$worktree_cleaned" != true ]]; then
  runner_exit_code=74
fi

python3 - "$output_dir/manifest.json" "$repo_root" "$head_commit" \
  "$dsh_exit_code" "$runner_exit_code" "$scope_ok" "$worktree_cleaned" "$worktree" <<'PY'
import json
import sys

(
    manifest_path,
    repo_root,
    head_commit,
    dsh_exit_code,
    runner_exit_code,
    scope_ok,
    worktree_cleaned,
    worktree_path,
) = sys.argv[1:]

manifest = {
    "worker": "deepseek-harness",
    "profile": "headless",
    "repo_root": repo_root,
    "head_commit": head_commit,
    "dsh_exit_code": int(dsh_exit_code),
    "runner_exit_code": int(runner_exit_code),
    "scope_ok": scope_ok == "true",
    "worktree_cleaned": worktree_cleaned == "true",
    "worktree_path": None if worktree_cleaned == "true" else worktree_path,
    "artifacts": [
        "final.txt",
        "reasoning.log",
        "status.txt",
        "changed-paths.txt",
        "changes.patch",
        "exit-code",
        "scope-check.txt",
    ],
}

with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

artifacts_complete=1
trap - EXIT
exit "$runner_exit_code"
