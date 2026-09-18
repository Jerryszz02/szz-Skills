#!/usr/bin/env python3
"""Build auditable worker receipts from native or DSH runtime evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from task_packet import nonempty_lines, parse_sections


def task_details(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    sections = parse_sections(raw.decode("utf-8"))
    objective = " ".join(nonempty_lines(sections.get("objective", [])))
    return {
        "objective": objective,
        "task_packet_sha256": hashlib.sha256(raw).hexdigest(),
    }


def unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in result:
            result.append(value)
    return result


def usage_record(
    *,
    uncached_input: int | None,
    cache_read: int | None,
    cache_write: int | None,
    output: int | None,
    source: str,
) -> dict[str, Any]:
    values = (uncached_input, cache_read, cache_write, output)
    if any(value is None for value in values):
        return {
            "available": False,
            "input_tokens": None,
            "uncached_input_tokens": uncached_input,
            "cached_input_tokens": cache_read,
            "cache_write_input_tokens": cache_write,
            "output_tokens": output,
            "total_tokens": None,
            "source": source,
        }
    assert all(isinstance(value, int) for value in values)
    input_tokens = int(uncached_input) + int(cache_read) + int(cache_write)
    return {
        "available": True,
        "input_tokens": input_tokens,
        "uncached_input_tokens": uncached_input,
        "cached_input_tokens": cache_read,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output,
        "total_tokens": input_tokens + int(output),
        "source": source,
    }


def receipt(
    *,
    worker: str,
    task_file: Path,
    requested_model: str | None,
    actual_models: list[str],
    reasoning_efforts: list[str],
    fork_turns: str | None,
    context_scope: str,
    status: str,
    usage: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "worker": worker,
        "task": task_details(task_file),
        "requested_model": requested_model,
        "actual_model": actual_models[-1] if actual_models else None,
        "actual_models": actual_models,
        "reasoning_effort": reasoning_efforts[-1] if reasoning_efforts else None,
        "fork_turns": fork_turns,
        "context_scope": context_scope,
        "status": status,
        "usage": usage,
        "evidence": evidence,
    }


def recursive_strings(value: Any, names: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in names and isinstance(child, str):
                found.append(child)
            found.extend(recursive_strings(child, names))
    elif isinstance(value, list):
        for child in value:
            found.extend(recursive_strings(child, names))
    return found


def dsh_evidence(session_root: Path, run_id: str, configured_model: str) -> tuple[list[str], list[str], dict[str, Any], dict[str, Any]]:
    matches: list[Path] = []
    for candidate in session_root.glob("*.json"):
        try:
            if run_id in candidate.read_text(encoding="utf-8"):
                matches.append(candidate)
        except (OSError, UnicodeError):
            continue
    session_file = max(matches, key=lambda path: path.stat().st_mtime) if matches else None
    actual_models = [configured_model] if configured_model else []
    reasoning_efforts: list[str] = []
    totals: dict[str, Any] | None = None
    if session_file is not None:
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            data = {}
        actual_models = unique_strings(actual_models + recursive_strings(data, {"model", "modelId", "modelName"}))
        reasoning_efforts = unique_strings(recursive_strings(data, {"thinkingEffort", "reasoningEffort"}))
        totals = (
            data.get("record", {})
            .get("rows", {})
            .get("tokenUsage", {})
            .get("val", {})
            .get("totals")
        )
    if not reasoning_efforts:
        reasoning_efforts = ["not-exposed"]
    if isinstance(totals, dict):
        usage = usage_record(
            uncached_input=int(totals.get("uncachedInputTokens", 0)),
            cache_read=int(totals.get("cacheReadTokens", 0)),
            cache_write=int(totals.get("cacheWriteTokens", 0)),
            output=int(totals.get("outputTokens", 0)),
            source="dsh-session-tokenUsage.totals",
        )
    else:
        usage = usage_record(
            uncached_input=None,
            cache_read=None,
            cache_write=None,
            output=None,
            source="dsh-session-tokenUsage.totals: session unavailable",
        )
    return actual_models, reasoning_efforts, usage, {
        "run_id": run_id,
        "session_file": str(session_file) if session_file else None,
        "model_source": "dsh composed headless profile" if configured_model else None,
    }


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--task-file", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--status", required=True)

    dsh = subparsers.add_parser("dsh")
    common(dsh)
    dsh.add_argument("--session-root", type=Path, required=True)
    dsh.add_argument("--run-id", required=True)
    dsh.add_argument("--configured-model", required=True)
    dsh.add_argument("--require-complete", action="store_true")

    native = subparsers.add_parser("native")
    common(native)
    native.add_argument("--worker", choices=("spark", "luna", "terra"), required=True)
    native.add_argument("--actual-model", required=True)
    native.add_argument("--reasoning-effort", required=True)
    native.add_argument("--fork-turns", required=True)
    native.add_argument("--input-tokens", type=int)
    native.add_argument("--cached-input-tokens", type=int)
    native.add_argument("--output-tokens", type=int)

    args = parser.parse_args()
    if args.command == "dsh":
        actual_models, efforts, usage, evidence = dsh_evidence(
            args.session_root,
            args.run_id,
            args.configured_model,
        )
        value = receipt(
            worker="deepseek-harness",
            task_file=args.task_file,
            requested_model=None,
            actual_models=actual_models,
            reasoning_efforts=efforts,
            fork_turns="not-applicable",
            context_scope="HEAD-only detached worktree",
            status=args.status,
            usage=usage,
            evidence=evidence,
        )
        write_receipt(args.output, value)
        if args.require_complete and (
            value["actual_model"] is None
            or value["reasoning_effort"] is None
            or not usage["available"]
        ):
            return 1
        return 0

    cached = args.cached_input_tokens
    input_tokens = args.input_tokens
    native_usage_values = (input_tokens, cached, args.output_tokens)
    if any(value is not None for value in native_usage_values) and any(
        value is None for value in native_usage_values
    ):
        parser.error("native token usage requires input, cached input, and output together")
    if input_tokens is not None and cached is not None and cached > input_tokens:
        parser.error("cached input tokens cannot exceed input tokens")
    uncached = None if input_tokens is None else input_tokens - (cached or 0)
    usage = usage_record(
        uncached_input=uncached,
        cache_read=cached,
        cache_write=0 if input_tokens is not None and cached is not None else None,
        output=args.output_tokens,
        source="native runtime evidence" if input_tokens is not None else "native runtime: usage unavailable",
    )
    value = receipt(
        worker=args.worker,
        task_file=args.task_file,
        requested_model=args.actual_model,
        actual_models=[args.actual_model],
        reasoning_efforts=[args.reasoning_effort],
        fork_turns=args.fork_turns,
        context_scope="native conversation fork",
        status=args.status,
        usage=usage,
        evidence={"source": "spawn_agent call and returned runtime evidence"},
    )
    write_receipt(args.output, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
