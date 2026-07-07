#!/usr/bin/env bash
set -euo pipefail

model="${DEEPSEEK_MODEL:-deepseek-chat}"
cwd="$(pwd)"
sandbox="workspace-write"
task_file=""
task=""
output=""
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) model="${2:-}"; shift 2 ;;
    --cwd) cwd="${2:-}"; shift 2 ;;
    --sandbox) sandbox="${2:-}"; shift 2 ;;
    --task-file) task_file="${2:-}"; shift 2 ;;
    --task) task="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help)
      echo "Usage: run-deepseek-worker.sh --model MODEL --cwd /abs/path --task-file FILE --output FILE [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$model" || -z "$output" ]]; then
  echo "--model and --output are required." >&2
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

endpoint="${DEEPSEEK_BASE_URL:-https://api.deepseek.com/v1/chat/completions}"
if [[ "$dry_run" -eq 1 ]]; then
  printf 'deepseek endpoint=%s model=%s cwd=%s sandbox=%s output=%s\n' "$endpoint" "$model" "$cwd" "$sandbox" "$output"
  exit 0
fi
if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required for deepseek provider. Provide it as an environment variable; do not put it in prompts or files." >&2
  exit 2
fi

prompt_file="$(mktemp "${TMPDIR:-/tmp}/non-gpt-deepseek.XXXXXX")"
trap 'rm -f "$prompt_file"' EXIT
{
  cat <<PROMPT
You are an external text-only worker for a Codex main agent.

Project root: $cwd
Permission requested by main agent: $sandbox

Important limits:
- You do not have Codex tools or direct repository access through this API call.
- Use only the context in this prompt.
- Do not request or print secrets, tokens, cookies, private keys, or .env values.
- Do not claim to have inspected files unless their contents are included in the prompt.

Task:
PROMPT
  if [[ -n "$task_file" ]]; then
    cat "$task_file"
  else
    printf '%s\n' "$task"
  fi
  cat <<'PROMPT'

Return:
- Summary
- Evidence used
- Suggested files or commands for the main agent to inspect
- Findings or implementation notes
- Remaining risks
PROMPT
} > "$prompt_file"

mkdir -p "$(dirname "$output")"
DEEPSEEK_ENDPOINT="$endpoint" DEEPSEEK_MODEL_NAME="$model" PROMPT_FILE="$prompt_file" OUTPUT_FILE="$output" python3 - <<'PY'
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

endpoint = os.environ["DEEPSEEK_ENDPOINT"]
model = os.environ["DEEPSEEK_MODEL_NAME"]
api_key = os.environ["DEEPSEEK_API_KEY"]
prompt_file = os.environ["PROMPT_FILE"]
output_file = os.environ["OUTPUT_FILE"]

with open(prompt_file, "r", encoding="utf-8") as handle:
    prompt = handle.read()

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a concise coding-analysis worker. Follow the user's output contract exactly."},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
}
request = urllib.request.Request(
    endpoint,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read().decode("utf-8")
except urllib.error.HTTPError as exc:
    sys.stderr.write(f"DeepSeek request failed with HTTP {exc.code}; response body omitted to avoid leaking provider details.\n")
    raise SystemExit(1)
except urllib.error.URLError as exc:
    sys.stderr.write(f"DeepSeek request failed: {exc.reason}\n")
    raise SystemExit(1)

try:
    data = json.loads(body)
    content = data["choices"][0]["message"]["content"]
except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
    sys.stderr.write(f"DeepSeek response had an unexpected shape: {exc}\n")
    raise SystemExit(1)

with open(output_file, "w", encoding="utf-8") as handle:
    handle.write(content.rstrip() + "\n")
print(output_file)
PY
