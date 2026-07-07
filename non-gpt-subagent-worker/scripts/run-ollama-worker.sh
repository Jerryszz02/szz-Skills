#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
source "$script_dir/shared_worker.sh"

parse_common_args ollama "$@"
run_codex_local_worker ollama
