#!/usr/bin/env python3
"""Collect a native Codex receipt from a thread/turn-scoped rollout JSONL stream.

This collector reads a Codex rollout file (JSON Lines) and builds the shared
worker receipt schema (see worker_receipt.py) for one native thread slice.

Rules honoured here:

- Only ``type == "token_usage_record"`` payloads whose ``thread_id`` exactly
  matches the requested ``--thread-id`` AND whose ``turn_id`` is one of the
  selected ``--turn-id`` values contribute token usage.  ``payload.usage`` is a
  per-response delta; turn/thread cumulative fields and ``event_msg`` token
  counts are never summed.
- Usage is all-or-nothing over the relevant records: any malformed/incomplete
  relevant usage, conflicting duplicate ``response_id``, or invalid rollout
  JSON line makes every core total null with ``available: false``.  No valid
  relevant usage means unknown (never zero).  A missing or unreadable rollout
  is likewise unknown.
- Actual model is observed only from the matching thread's ``turn_context``
  payload for a selected turn.  A ``turn_context`` without ``thread_id`` is
  accepted only when a ``session_meta`` payload id (or session_id)
  establishes this file as the requested thread.  ``--requested-model`` is
  recorded separately and never copied into ``actual_model``.
- The rollout is streamed line by line; messages and full rollouts are never
  copied into the receipt or its evidence.

This module is stdlib only.  Missing telemetry still writes a receipt and
exits 0; invalid command line arguments exit 2 through argparse.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from worker_receipt import receipt, unique_strings, usage_record, write_receipt

USAGE_SOURCE = "codex-rollout-token_usage_record"
CONTEXT_SCOPE = "native rollout thread/turn slice"


def _is_nonneg_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _matches(value: Any, expected: str) -> bool:
    return isinstance(value, str) and value == expected


def _response_usage(usage: Any) -> tuple[bool, str, tuple[Any, ...] | None]:
    """Validate one per-response usage delta.

    Returns (ok, reason, canonical) where canonical carries
    (input_tokens, output_tokens, total_tokens, cached_input_tokens or None,
    cache_write_input_tokens or None).  Optional cache components must be
    nonnegative and their sum may not exceed input_tokens; reasoning output is
    ignored because it is already inside output_tokens.
    """
    if not isinstance(usage, dict):
        return False, "usage payload must be an object", None
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        if not _is_nonneg_int(usage.get(key)):
            return False, f"usage.{key} must be a nonnegative integer", None
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    total_tokens = usage["total_tokens"]
    if total_tokens != input_tokens + output_tokens:
        return False, "usage.total_tokens must equal input_tokens + output_tokens", None
    cached = usage.get("cached_input_tokens")
    has_cached = "cached_input_tokens" in usage
    if has_cached and not _is_nonneg_int(cached):
        return False, "usage.cached_input_tokens must be a nonnegative integer", None
    cache_write = usage.get("cache_write_input_tokens")
    has_cache_write = "cache_write_input_tokens" in usage
    if has_cache_write and not _is_nonneg_int(cache_write):
        return False, "usage.cache_write_input_tokens must be a nonnegative integer", None
    combined = (cached or 0) + (cache_write or 0)
    if combined > input_tokens:
        return False, "usage.cached_input_tokens plus cache_write_input_tokens cannot exceed input_tokens", None
    canonical = (
        input_tokens,
        output_tokens,
        total_tokens,
        cached if has_cached else None,
        cache_write if has_cache_write else None,
    )
    return True, "", canonical


def _read_lines(rollout: Path):
    """Yield (line_no, raw) while streaming a rollout; read errors propagate."""
    with rollout.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            yield line_no, raw


def _unknown_usage(reason: str) -> dict[str, Any]:
    return usage_record(
        uncached_input=None,
        cache_read=None,
        cache_write=None,
        output=None,
        source=f"{USAGE_SOURCE}: {reason}",
    )


def _available_usage(
    *,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    cached: int | None,
    cache_write: int | None,
) -> dict[str, Any]:
    if cached is None or cache_write is None:
        uncached = None
    else:
        uncached = input_tokens - cached - cache_write
    return {
        "available": True,
        "input_tokens": input_tokens,
        "uncached_input_tokens": uncached,
        "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "source": USAGE_SOURCE,
    }


def scan_rollout(
    rollout: Path,
    thread_id: str,
    turn_ids: Iterable[str],
) -> dict[str, Any]:
    """Stream *rollout* and summarise the selected thread/turn slice.

    Returns {"usage": receipt usage object, "actual_models": [..],
    "evidence": {..}}.  Evidence stores the resolved rollout path, selected
    thread/turn ids, unique response ids, and the relevant record line range
    and count; it never stores message content.
    """
    resolved = str(rollout.resolve())
    selected_turns = list(dict.fromkeys(turn_ids))
    evidence: dict[str, Any] = {
        "rollout_file": resolved,
        "thread_id": thread_id,
        "turn_ids": selected_turns,
        "response_ids": [],
        "relevant_first_line": None,
        "relevant_last_line": None,
        "relevant_records": 0,
    }

    file_thread_ids: set[str] = set()
    observed: list[tuple[int, str]] = []
    threadless: list[tuple[int, str]] = []
    invalid_first: int | None = None
    invalid_count = 0
    problems: list[str] = []
    response_ids: list[str] = []
    response_seen: set[str] = set()
    response_turns: dict[str, str] = {}
    canonical_by_response: dict[str, tuple[Any, ...]] = {}
    relevant_lines: list[int] = []

    valid = 0
    input_total = 0
    output_total = 0
    total_total = 0
    cached_total = 0
    cache_write_total = 0
    cached_all_present = True
    cache_write_all_present = True

    def select_turn(payload: Any) -> bool:
        return isinstance(payload, dict) and any(
            _matches(payload.get("turn_id"), turn) for turn in selected_turns
        )

    try:
        for line_no, raw in _read_lines(rollout):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                invalid_count += 1
                invalid_first = line_no if invalid_first is None else invalid_first
                continue
            if not isinstance(value, dict):
                invalid_count += 1
                invalid_first = line_no if invalid_first is None else invalid_first
                continue
            record_type = value.get("type")
            payload = value.get("payload")

            if record_type == "session_meta" and isinstance(payload, dict):
                identity = payload.get("id")
                if not isinstance(identity, str) or not identity:
                    identity = payload.get("session_id")
                if isinstance(identity, str) and identity:
                    file_thread_ids.add(identity)
                continue

            if record_type == "turn_context" and isinstance(payload, dict):
                model = payload.get("model")
                if not isinstance(model, str) or not model:
                    continue
                if not select_turn(payload):
                    continue
                if "thread_id" in payload and payload.get("thread_id") is not None:
                    if _matches(payload["thread_id"], thread_id):
                        observed.append((line_no, model))
                else:
                    threadless.append((line_no, model))
                continue

            if record_type != "token_usage_record" or not isinstance(payload, dict):
                continue
            if not _matches(payload.get("thread_id"), thread_id):
                continue
            if not select_turn(payload):
                continue
            relevant_lines.append(line_no)

            response_id = payload.get("response_id")
            if not isinstance(response_id, str) or not response_id:
                problems.append(f"line {line_no}: token usage record has no response_id")
                continue
            if response_id not in response_seen:
                response_seen.add(response_id)
                response_ids.append(response_id)
                response_turns[response_id] = payload["turn_id"]
            elif response_turns[response_id] != payload["turn_id"]:
                problems.append(f"line {line_no}: response_id occurs in different turns")
                continue

            ok, reason, canonical = _response_usage(payload.get("usage"))
            if not ok:
                problems.append(f"line {line_no}: {reason}")
                continue
            previous = canonical_by_response.get(response_id)
            if previous is not None and previous != canonical:
                problems.append(f"line {line_no}: conflicting duplicate response_id {response_id!r}")
                continue
            if previous is not None:
                continue  # exact identical duplicate response; deduplicated
            canonical_by_response[response_id] = canonical
            assert canonical is not None
            input_tokens, output_tokens, total_tokens, cached, cache_write = canonical
            valid += 1
            input_total += input_tokens
            output_total += output_tokens
            total_total += total_tokens
            if cached is None:
                cached_all_present = False
            else:
                cached_total += cached
            if cache_write is None:
                cache_write_all_present = False
            else:
                cache_write_total += cache_write
    except (OSError, UnicodeError) as exc:
        return {
            "usage": _unknown_usage(f"rollout missing or unreadable: {exc}"),
            "actual_models": [],
            "evidence": evidence,
        }

    if thread_id in file_thread_ids:
        observed.extend(threadless)
    observed.sort(key=lambda item: item[0])
    actual_models = unique_strings([model for _, model in observed])

    evidence["response_ids"] = response_ids
    if relevant_lines:
        evidence["relevant_first_line"] = relevant_lines[0]
        evidence["relevant_last_line"] = relevant_lines[-1]
        evidence["relevant_records"] = len(relevant_lines)

    if invalid_count:
        reason = f"invalid rollout JSON at line {invalid_first}"
        if invalid_count > 1:
            reason += f" (and {invalid_count - 1} more)"
        return {
            "usage": _unknown_usage(reason),
            "actual_models": actual_models,
            "evidence": evidence,
        }
    if problems:
        reason = problems[0]
        if len(problems) > 1:
            reason += f" (and {len(problems) - 1} more)"
        return {
            "usage": _unknown_usage(reason),
            "actual_models": actual_models,
            "evidence": evidence,
        }
    if valid == 0:
        return {
            "usage": _unknown_usage(
                f"no token usage records matching thread {thread_id!r} and the selected turn ids"
            ),
            "actual_models": actual_models,
            "evidence": evidence,
        }
    cached_value = cached_total if cached_all_present else None
    cache_write_value = cache_write_total if cache_write_all_present else None
    return {
        "usage": _available_usage(
            input_tokens=input_total,
            output_tokens=output_total,
            total_tokens=total_total,
            cached=cached_value,
            cache_write=cache_write_value,
        ),
        "actual_models": actual_models,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a native Codex receipt from a rollout thread/turn slice."
    )
    parser.add_argument("--rollout", type=Path, required=True, help="rollout JSONL file")
    parser.add_argument("--thread-id", required=True, help="thread id to collect")
    parser.add_argument(
        "--turn-id",
        action="append",
        required=True,
        metavar="ID",
        help="turn id to collect (repeatable)",
    )
    parser.add_argument("--task-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", choices=("native", "manager"), required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--requested-model", default=None)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--fork-turns", default="none")
    args = parser.parse_args()
    if not args.thread_id.strip() or any(not turn.strip() for turn in args.turn_id):
        parser.error("thread-id and turn-id must be nonempty")

    scanned = scan_rollout(args.rollout, args.thread_id, args.turn_id)
    reasoning_efforts = [args.reasoning_effort] if args.reasoning_effort else []
    try:
        value = receipt(
            worker=args.worker,
            task_file=args.task_file,
            requested_model=args.requested_model or None,
            actual_models=scanned["actual_models"],
            reasoning_efforts=reasoning_efforts,
            fork_turns=args.fork_turns,
            context_scope=CONTEXT_SCOPE,
            status=args.status,
            usage=scanned["usage"],
            evidence=scanned["evidence"],
        )
        write_receipt(args.output, value)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
