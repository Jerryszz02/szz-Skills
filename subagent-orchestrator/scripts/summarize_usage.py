#!/usr/bin/env python3
"""Aggregate manager and worker receipt token usage from a run manifest."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROLES = {"manager", "worker", "integrator"}
ACCEPTANCE = {"passed", "failed", "incomplete"}


class ValidationError(ValueError):
    pass


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a nonempty string")
    return value


def _number(value: Any, name: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValidationError(f"{name} must be a finite number")
    if value < 0:
        raise ValidationError(f"{name} must be nonnegative")
    return value


def _core_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{name} must be a nonnegative integer")
    return value


def _load_json(path: Path, what: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"cannot read {what} {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"malformed JSON in {what} {path}: {exc}") from exc


def _usage(receipt: dict[str, Any], path: Path) -> tuple[bool, int | None]:
    usage = receipt.get("usage")
    if not isinstance(usage, dict):
        raise ValidationError(f"receipt {path} usage must be an object")
    available = usage.get("available")
    if not isinstance(available, bool):
        raise ValidationError(f"receipt {path} usage.available must be boolean")
    source = usage.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValidationError(f"receipt {path} usage.source must explain the evidence or its absence")
    if not available:
        return False, None
    values = {key: _core_int(usage.get(key), f"receipt {path} usage.{key}") for key in
              ("input_tokens", "output_tokens", "total_tokens")}
    if values["total_tokens"] != values["input_tokens"] + values["output_tokens"]:
        raise ValidationError(f"receipt {path} usage.total_tokens must equal input_tokens + output_tokens")
    return True, values["total_tokens"]


def summarize(run_path: Path) -> dict[str, Any]:
    manifest = _load_json(run_path, "run manifest")
    if not isinstance(manifest, dict):
        raise ValidationError("run manifest must be an object")
    if type(manifest.get("schema_version")) is not int or manifest.get("schema_version") != 1:
        raise ValidationError("run manifest schema_version must be 1")
    task_id = _nonempty(manifest.get("task_id"), "task_id")
    variant = manifest.get("variant")
    if not isinstance(variant, str) or variant not in {"baseline", "orchestrated"}:
        raise ValidationError("variant must be baseline or orchestrated")
    acceptance = manifest.get("acceptance")
    if not isinstance(acceptance, str) or acceptance not in ACCEPTANCE:
        raise ValidationError("acceptance must be passed, failed, or incomplete")
    elapsed = _number(manifest.get("elapsed_seconds"), "elapsed_seconds")
    entries = manifest.get("runs")
    if not isinstance(entries, list) or not entries:
        raise ValidationError("runs must be a nonempty list")

    seen_ids: set[str] = set()
    seen_identity: set[tuple[str, str, int]] = set()
    seen_paths: set[Path] = set()
    seen_responses: set[tuple[str, str]] = set()
    manager_count = 0
    results: list[dict[str, Any]] = []
    manager_values: list[int] = []
    worker_values: list[int] = []
    missing: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValidationError("each run entry must be an object")
        run_id = _nonempty(entry.get("id"), "run id")
        if run_id in seen_ids:
            raise ValidationError(f"duplicate run id: {run_id}")
        seen_ids.add(run_id)
        role = entry.get("role")
        if not isinstance(role, str) or role not in ROLES:
            raise ValidationError(f"run {run_id} role must be manager, worker, or integrator")
        slice_id = _nonempty(entry.get("slice_id"), f"run {run_id} slice_id")
        attempt = entry.get("attempt")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt <= 0:
            raise ValidationError(f"run {run_id} attempt must be a positive integer")
        identity = (role, slice_id, attempt)
        if identity in seen_identity:
            raise ValidationError(f"duplicate role/slice_id/attempt entry for run {run_id}")
        seen_identity.add(identity)
        if role == "manager":
            manager_count += 1
            if attempt != 1:
                raise ValidationError("manager entry must use attempt 1 for whole-task usage")
        receipt_ref = entry.get("receipt")
        available = False
        tokens: int | None = None
        receipt_status = None
        actual_model = None
        resolved = None
        if receipt_ref is not None:
            if not isinstance(receipt_ref, str) or not receipt_ref:
                raise ValidationError(f"run {run_id} receipt must be a path or null")
            resolved = Path(receipt_ref)
            if not resolved.is_absolute():
                resolved = run_path.parent / resolved
            resolved = resolved.resolve()
            if resolved in seen_paths:
                raise ValidationError(f"duplicate resolved receipt path: {resolved}")
            seen_paths.add(resolved)
            if not resolved.exists():
                missing.append(run_id)
                results.append({"id": run_id, "role": role, "slice_id": slice_id, "attempt": attempt,
                                "receipt": str(resolved), "receipt_status": None,
                                "actual_model": None, "usage_complete": False})
                continue
            receipt = _load_json(resolved, "receipt")
            if not isinstance(receipt, dict):
                raise ValidationError(f"receipt {resolved} must be an object")
            receipt_worker = receipt.get("worker")
            if not isinstance(receipt_worker, str) or not receipt_worker.strip():
                raise ValidationError(f"receipt {resolved} worker must be a nonempty string")
            if role == "manager" and receipt_worker != "manager":
                raise ValidationError(f"manager run {run_id} must reference a manager receipt")
            if role != "manager" and receipt_worker == "manager":
                raise ValidationError(f"non-manager run {run_id} cannot reference a manager receipt")
            receipt_status = receipt.get("status")
            actual_model = receipt.get("actual_model")
            if not isinstance(receipt_status, str) or not receipt_status.strip():
                raise ValidationError(f"receipt {resolved} status must be a nonempty string")
            if actual_model is not None and (not isinstance(actual_model, str) or not actual_model.strip()):
                raise ValidationError(f"receipt {resolved} actual_model must be a nonempty string or null")
            available, tokens = _usage(receipt, resolved)
            evidence = receipt.get("evidence", {})
            if isinstance(evidence, dict) and "response_ids" in evidence:
                thread_id = _nonempty(evidence.get("thread_id"), "evidence.thread_id")
                response_ids = evidence["response_ids"]
                if not isinstance(response_ids, list):
                    raise ValidationError("evidence.response_ids must be a list")
                for response_id in response_ids:
                    key = (thread_id, _nonempty(response_id, "response_id"))
                    if key in seen_responses:
                        raise ValidationError(f"overlapping native response usage: {response_id}")
                    seen_responses.add(key)
        if not available:
            missing.append(run_id)
        else:
            assert tokens is not None
            if role == "manager":
                manager_values.append(tokens)
            else:
                worker_values.append(tokens)
        results.append({"id": run_id, "role": role, "slice_id": slice_id, "attempt": attempt,
                        "receipt": str(resolved) if resolved else None, "receipt_status": receipt_status,
                        "actual_model": actual_model, "usage_complete": available,
                        "usage": receipt.get("usage") if resolved else None})
    if manager_count != 1:
        raise ValidationError("runs must contain exactly one manager entry")
    # Route decisions live outside runs: a preflight skip is not a model attempt.
    route_refs = manifest.get("routes", [])
    if not isinstance(route_refs, list):
        raise ValidationError("routes must be a list of diagnostic paths")
    routing = []
    seen_routes: set[Path] = set()
    unaccounted = []
    for reference in route_refs:
        path = Path(_nonempty(reference, "route path"))
        path = (path if path.is_absolute() else run_path.parent / path).resolve()
        if path in seen_routes:
            raise ValidationError(f"duplicate route path: {path}")
        seen_routes.add(path)
        route = _load_json(path, "route diagnostics")
        if not isinstance(route, dict) or route.get("schema_version") != 1:
            raise ValidationError("route diagnostics schema_version must be 1")
        state = route.get("execution_state")
        if state not in ("not_started", "unknown", "observed"):
            raise ValidationError("invalid route execution_state")
        _nonempty(route.get("reason_code"), "route reason_code")
        _nonempty(route.get("provider"), "route provider")
        receipt_ref = route.get("receipt")
        route_receipt = Path(receipt_ref) if isinstance(receipt_ref, str) else None
        if route_receipt is not None:
            route_receipt = (route_receipt if route_receipt.is_absolute() else path.parent / route_receipt).resolve()
        if state != "not_started" and route_receipt not in seen_paths:
            unaccounted.append(str(path))
        routing.append({"path": str(path), **route})
    manager_tokens = manager_values[0] if len(manager_values) == 1 else None
    worker_tokens = sum(worker_values) if len(worker_values) == len([r for r in entries if r["role"] != "manager"]) else None
    if unaccounted:
        worker_tokens = None
    observed = sum(manager_values) + sum(worker_values)
    return {"schema_version": 1, "task_id": task_id, "variant": variant, "acceptance": acceptance,
            "elapsed_seconds": elapsed, "runs": results, "manager_tokens": manager_tokens,
            "worker_tokens": worker_tokens, "total_tokens": manager_tokens + worker_tokens
            if manager_tokens is not None and worker_tokens is not None else None,
            "observed_tokens": observed, "usage_complete": not missing and not unaccounted, "missing_usage": missing,
            "routing": routing, "unaccounted_routes": unaccounted,
            "skipped_routes": [r for r in routing if r["execution_state"] == "not_started"
                               and r["reason_code"] != "cli_found"],
            "worker_attempts": sum(1 for r in entries if r["role"] in {"worker", "integrator"}),
            "retry_attempts": sum(1 for r in entries if r["role"] != "manager" and r["attempt"] > 1)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        value = summarize(args.run.resolve())
        encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 0
    except (ValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
