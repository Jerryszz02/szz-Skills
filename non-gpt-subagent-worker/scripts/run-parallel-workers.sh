#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
tasks=""
output_dir=""
max_parallel=3
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tasks) tasks="${2:-}"; shift 2 ;;
    --output-dir) output_dir="${2:-}"; shift 2 ;;
    --max-parallel) max_parallel="${2:-}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help)
      echo "Usage: run-parallel-workers.sh --tasks tasks.json --output-dir DIR [--max-parallel 3] [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$tasks" || -z "$output_dir" ]]; then
  echo "--tasks and --output-dir are required." >&2
  exit 2
fi
if ! [[ "$max_parallel" =~ ^[0-9]+$ ]] || [[ "$max_parallel" -lt 1 ]]; then
  echo "--max-parallel must be a positive integer." >&2
  exit 2
fi

mkdir -p "$output_dir"
SCRIPT_DIR="$script_dir" TASKS_FILE="$tasks" OUTPUT_DIR="$output_dir" MAX_PARALLEL="$max_parallel" DRY_RUN="$dry_run" python3 - <<'PY'
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
from pathlib import Path

script_dir = Path(os.environ["SCRIPT_DIR"])
tasks_file = Path(os.environ["TASKS_FILE"])
output_dir = Path(os.environ["OUTPUT_DIR"])
max_parallel = int(os.environ["MAX_PARALLEL"])
dry_run = os.environ["DRY_RUN"] == "1"

with tasks_file.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)
if not isinstance(payload, list):
    raise SystemExit("tasks file must contain a JSON array")


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "task"


def run_task(item: dict[str, object]) -> dict[str, object]:
    if not isinstance(item, dict):
        raise ValueError("each task must be an object")
    task_id = safe_id(str(item.get("id", "task")))
    task_text = str(item.get("task", "")).strip()
    if not task_text:
        raise ValueError(f"{task_id}: task is required")
    provider = str(item.get("provider", "")).strip()
    model = str(item.get("model", "")).strip()
    cwd = str(item.get("cwd", "")).strip()
    sandbox = str(item.get("sandbox", "workspace-write")).strip()
    if not provider or not model or not cwd:
        raise ValueError(f"{task_id}: provider, model, and cwd are required")

    task_file = output_dir / f"{task_id}.task.md"
    result_file = output_dir / f"{task_id}.result.md"
    stdout_file = output_dir / f"{task_id}.stdout.log"
    stderr_file = output_dir / f"{task_id}.stderr.log"
    task_file.write_text(task_text + "\n", encoding="utf-8")

    cmd = [
        "bash",
        str(script_dir / "run-worker.sh"),
        "--provider",
        provider,
        "--model",
        model,
        "--cwd",
        cwd,
        "--sandbox",
        sandbox,
        "--task-file",
        str(task_file),
        "--output",
        str(result_file),
    ]
    if dry_run:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    stdout_file.write_text(proc.stdout, encoding="utf-8")
    stderr_file.write_text(proc.stderr, encoding="utf-8")
    return {
        "id": task_id,
        "returncode": proc.returncode,
        "result": str(result_file),
        "stdout": str(stdout_file),
        "stderr": str(stderr_file),
    }


summary: list[dict[str, object]] = []
with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as pool:
    futures = [pool.submit(run_task, item) for item in payload]
    for future in concurrent.futures.as_completed(futures):
        summary.append(future.result())

summary.sort(key=lambda item: str(item["id"]))
(output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(output_dir / "summary.json")
failed = [item for item in summary if item["returncode"] != 0]
if failed:
    raise SystemExit(1)
PY
