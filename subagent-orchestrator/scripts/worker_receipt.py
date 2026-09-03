#!/usr/bin/env python3
"""Build auditable worker receipts from native, DSH, or Kimi runtime evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from task_packet import nonempty_lines, parse_sections


def read_json_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


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


def kimi_evidence(events_file: Path, session_index: Path) -> tuple[list[str], list[str], dict[str, Any], dict[str, Any]]:
    events = read_json_lines(events_file)
    session_ids = [
        row.get("session_id")
        for row in events
        if row.get("type") == "session.resume_hint"
    ]
    session_id = next((value for value in reversed(session_ids) if isinstance(value, str)), None)
    if session_id is None:
        return [], [], usage_record(
            uncached_input=None,
            cache_read=None,
            cache_write=None,
            output=None,
            source="kimi-session-wire: session id unavailable",
        ), {"session_id": None, "wire_file": None}

    session_dir: Path | None = None
    try:
        index_rows = read_json_lines(session_index)
    except (OSError, UnicodeError, json.JSONDecodeError):
        index_rows = []
    for row in reversed(index_rows):
        if row.get("sessionId") == session_id and isinstance(row.get("sessionDir"), str):
            session_dir = Path(row["sessionDir"])
            break
    wire_file = session_dir / "agents/main/wire.jsonl" if session_dir else None
    if wire_file is None or not wire_file.is_file():
        return [], [], usage_record(
            uncached_input=None,
            cache_read=None,
            cache_write=None,
            output=None,
            source="kimi-session-wire: wire file unavailable",
        ), {"session_id": session_id, "wire_file": None}

    rows = read_json_lines(wire_file)
    request_rows = [row for row in rows if row.get("type") == "llm.request"]
    actual_models = unique_strings([row.get("model") for row in request_rows])
    if not actual_models:
        actual_models = unique_strings(
            [row.get("model") for row in rows if row.get("type") == "usage.record"]
        )
    reasoning_efforts = unique_strings([row.get("thinkingEffort") for row in request_rows])
    usage_rows = [
        row.get("usage")
        for row in rows
        if row.get("type") == "usage.record"
        and row.get("usageScope") == "turn"
        and isinstance(row.get("usage"), dict)
    ]
    if usage_rows:
        uncached_input = sum(int(row.get("inputOther", 0)) for row in usage_rows)
        cache_read = sum(int(row.get("inputCacheRead", 0)) for row in usage_rows)
        cache_write = sum(int(row.get("inputCacheCreation", 0)) for row in usage_rows)
        output = sum(int(row.get("output", 0)) for row in usage_rows)
    else:
        uncached_input = cache_read = cache_write = output = None
    usage = usage_record(
        uncached_input=uncached_input,
        cache_read=cache_read,
        cache_write=cache_write,
        output=output,
        source="kimi-session-wire",
    )
    return actual_models, reasoning_efforts, usage, {
        "session_id": session_id,
        "wire_file": str(wire_file),
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

    kimi = subparsers.add_parser("kimi")
    common(kimi)
    kimi.add_argument("--events-file", type=Path, required=True)
    kimi.add_argument("--session-index", type=Path, required=True)
    kimi.add_argument("--requested-model", default="")
    kimi.add_argument("--require-complete", action="store_true")

    dsh = subparsers.add_parser("dsh")
    common(dsh)
    dsh.add_argument("--session-root", type=Path, required=True)
    dsh.add_argument("--run-id", required=True)
    dsh.add_argument("--configured-model", required=True)
    dsh.add_argument("--require-complete", action="store_true")

    native = subparsers.add_parser("native")
    common(native)
    native.add_argument("--worker", choices=("luna", "terra"), required=True)
    native.add_argument("--actual-model", required=True)
    native.add_argument("--reasoning-effort", required=True)
    native.add_argument("--fork-turns", required=True)
    native.add_argument("--input-tokens", type=int)
    native.add_argument("--cached-input-tokens", type=int)
    native.add_argument("--output-tokens", type=int)

    args = parser.parse_args()
    if args.command == "kimi":
        actual_models, efforts, usage, evidence = kimi_evidence(args.events_file, args.session_index)
        value = receipt(
            worker="kimi",
            task_file=args.task_file,
            requested_model=args.requested_model or None,
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
