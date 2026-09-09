#!/usr/bin/env python3
"""Resolve external CLIs and keep safe, local route diagnostics; never call a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone


SKIP_REASONS = (
    "external_boundary", "data_transfer_denied", "head_only_unavailable",
    "runtime_unsupported", "capacity_queued", "recovery_exhausted",
    "direct_exception",
)


def resolve_cli(provider: str) -> dict:
    override = os.environ.get("DSH_BIN" if provider == "dsh" else "KIMI_BIN")
    home = Path.home()
    candidates = [(override, "override")] if override else [
        (provider, "PATH"),
        (str(home / (".local/bin/dsh" if provider == "dsh" else ".kimi-code/bin/kimi")), "user_install"),
    ]
    checked = []
    for candidate, source in candidates:
        found = shutil.which(candidate)
        if found:
            # Keep the executable symlink: resolving it can change launcher behavior.
            found = os.path.abspath(found)
        checked.append({"candidate": candidate, "source": source, "found": bool(found)})
        if found:
            return {"executable": found, "resolution_source": source, "checked": checked}
    return {"executable": None, "resolution_source": None, "checked": checked}


def save(path: Path, data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("probe", help="Resolve CLI only; no API request")
    probe.add_argument("--provider", choices=("dsh", "kimi"), required=True)
    probe.add_argument("--output", type=Path)
    probe.add_argument("--task-file", type=Path)
    probe.add_argument("--slice-id")
    probe.add_argument("--attempt", type=int, default=1)
    probe.add_argument("--print-executable", action="store_true")
    finish = sub.add_parser("finish")
    finish.add_argument("--output", type=Path, required=True)
    finish.add_argument("--stage", required=True)
    finish.add_argument("--reason", required=True)
    finish.add_argument("--exit-code", type=int, required=True)
    finish.add_argument("--execution-state", choices=("not_started", "unknown", "observed"), required=True)
    skip = sub.add_parser("skip", help="Record a manager route decision without probing a provider")
    skip.add_argument("--provider", required=True)
    skip.add_argument("--output", type=Path, required=True)
    skip.add_argument("--slice-id", required=True)
    skip.add_argument("--reason", choices=SKIP_REASONS, required=True)
    skip.add_argument("--detail", required=True, help="Concrete reason; never include secrets")
    args = parser.parse_args()
    if args.command == "finish":
        data = json.loads(args.output.read_text(encoding="utf-8"))
        data.update(stage=args.stage, reason_code=args.reason, exit_code=args.exit_code,
                    execution_state=args.execution_state)
        receipt_path = args.output.parent / "worker-receipt.json"
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            data["receipt"] = str(receipt_path.resolve())
            data["actual_model"] = receipt.get("actual_model")
            data["usage"] = receipt.get("usage")
            if data["usage"] and data["usage"].get("available"):
                data["execution_state"] = "observed"
        save(args.output, data)
        print(json.dumps({key: data.get(key) for key in (
            "provider", "slice_id", "attempt", "stage", "reason_code", "execution_state",
            "exit_code", "actual_model", "usage", "receipt",
        )}))
        return 0
    if args.command == "skip":
        if not args.detail.strip() or not args.slice_id.strip():
            parser.error("detail and slice-id must be nonempty")
        data = {"schema_version": 1, "provider": args.provider, "slice_id": args.slice_id,
                "attempt": None, "stage": "routing", "execution_state": "not_started",
                "reason_code": args.reason, "detail": args.detail, "exit_code": None}
        if args.output.exists():
            parser.error("output already exists; keep each route decision separately")
        save(args.output, data)
        return 0
    if args.attempt < 1:
        parser.error("attempt must be positive")
    if args.output and args.output.exists():
        parser.error("output already exists; use an empty attempt directory")
    result = resolve_cli(args.provider)
    digest = None
    if args.task_file and args.task_file.is_file():
        digest = hashlib.sha256(args.task_file.read_bytes()).hexdigest()
    data = {"schema_version": 1, "provider": args.provider,
            "slice_id": args.slice_id or (digest[:12] if digest else None),
            "attempt": args.attempt, "task_packet_sha256": digest,
            "stage": "executable_probe", "execution_state": "not_started",
            "reason_code": "cli_found" if result["executable"] else "cli_missing",
            "exit_code": 0 if result["executable"] else 69, **result}
    if args.output:
        save(args.output, data)
    if args.print_executable:
        if result["executable"]:
            print(result["executable"])
    else:
        print(json.dumps(data, indent=2))
    return 0 if result["executable"] else 69


if __name__ == "__main__":
    sys.exit(main())
