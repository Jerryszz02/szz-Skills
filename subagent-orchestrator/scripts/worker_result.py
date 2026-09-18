#!/usr/bin/env python3
"""Normalize a bounded worker's final JSON report into a compact result record.

The helper is deterministic and offline. It never executes the commands a report
mentions, never infers success from a CLI exit code, and never invents evidence.
A report that is missing, malformed, overlong, or contradicts a ``completed``
claim is recorded as ``unverified`` with concise issues while the raw report is
preserved next to the normalized output.

The worker-supplied ``changed_paths`` field is kept strictly separate from the
Git-observed ``--changed-paths`` input: observed paths are labeled
``git-observed`` and reported paths are labeled ``worker-reported``.

Contract for a worker report (schema_version 1)::

    {
      "schema_version": 1,
      "status": "completed" | "partial" | "blocked",
      "summary": "nonempty text",
      "checks": [
        {"command": "text", "cwd": "/absolute/path",
         "exit_code": 0, "result": "text"}
      ],
      "unresolved": ["text"],
      "evidence": ["text"]
    }

A completed report needs at least one executed check, every check exit code
zero, and no unresolved criteria. The report may be a whole JSON document or a
single whole JSON fenced block; arbitrary prose is not scraped for JSON.

Exit codes:
  0  normalized report is a valid ``completed`` report
  1  normalized report is a valid ``partial`` or ``blocked`` report
  2  command-line usage error
  3  report is missing, malformed, overlong, or contradicted (``unverified``)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
WORKER_STATUSES = ("completed", "partial", "blocked")

MAX_SUMMARY_CHARS = 2000
MAX_COMMAND_CHARS = 500
MAX_CWD_CHARS = 500
MAX_RESULT_CHARS = 2000
MAX_CHECK_COUNT = 50
MAX_UNRESOLVED_COUNT = 50
MAX_UNRESOLVED_CHARS = 500
MAX_EVIDENCE_COUNT = 50
MAX_EVIDENCE_CHARS = 500
MAX_PATH_COUNT = 200
MAX_PATH_CHARS = 500
MAX_REPORT_BYTES = 32768
MAX_NORMALIZED_BYTES = 32768

_TRUNCATION_MARKER = "…[truncated; see raw report]"
_FENCE = re.compile(r"```([A-Za-z0-9_+.-]*)[ \t]*\r?\n(.*?)```", re.DOTALL)
_JSON_FENCE_LABELS = {"", "json"}


def _truncate(text: str, limit: int, label: str, issues: list[str]) -> str:
    if len(text) > limit:
        issues.append(f"{label} exceeds {limit} characters")
        return text[:limit] + _TRUNCATION_MARKER
    return text


def _extract_report(text: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    """Parse exactly one JSON document or one whole JSON fenced block."""
    issues: list[str] = []
    stripped = text.strip()
    if stripped:
        try:
            candidate = json.loads(stripped)
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, dict):
            return candidate, "json-document", issues
        if candidate is not None:
            issues.append("report JSON is not an object")
            return None, "malformed", issues
    fences = _FENCE.findall(text)
    if len(fences) > 1:
        issues.append("report contains multiple fenced blocks; expected one")
        return None, "ambiguous", issues
    if not fences:
        issues.append("report contains no JSON object or JSON fenced block")
        return None, "missing", issues
    if _FENCE.fullmatch(stripped) is None:
        issues.append("report has text outside the JSON fenced block")
        return None, "ambiguous", issues
    label, content = fences[0]
    if label.lower() not in _JSON_FENCE_LABELS:
        issues.append(f"fenced block is not labeled json: {label or '<unlabeled>'}")
        return None, "malformed", issues
    try:
        candidate = json.loads(content)
    except json.JSONDecodeError as exc:
        issues.append(f"fenced JSON is malformed: {exc.msg}")
        return None, "malformed", issues
    if not isinstance(candidate, dict):
        issues.append("fenced JSON is not an object")
        return None, "malformed", issues
    return candidate, "fenced-json", issues


def _parse_checks(value: Any, issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        issues.append("checks must be an array")
        return []
    if len(value) > MAX_CHECK_COUNT:
        issues.append(f"checks exceeds {MAX_CHECK_COUNT} items")
        value = value[:MAX_CHECK_COUNT]
    parsed: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            issues.append(f"checks[{index}] must be an object")
            continue
        command = item.get("command")
        if not isinstance(command, str) or not command.strip():
            issues.append(f"checks[{index}].command must be nonempty text")
            command = ""
        else:
            command = _truncate(command, MAX_COMMAND_CHARS, f"checks[{index}].command", issues)
        cwd = item.get("cwd")
        if not isinstance(cwd, str) or not cwd.startswith("/"):
            issues.append(f"checks[{index}].cwd must be an absolute path")
            cwd = cwd if isinstance(cwd, str) else ""
        else:
            cwd = _truncate(cwd, MAX_CWD_CHARS, f"checks[{index}].cwd", issues)
        if "exit_code" not in item:
            issues.append(f"checks[{index}].exit_code must be an integer or null")
            exit_code = None
        else:
            exit_code = item.get("exit_code")
            if isinstance(exit_code, bool) or (exit_code is not None and not isinstance(exit_code, int)):
                issues.append(f"checks[{index}].exit_code must be an integer or null")
                exit_code = None
        result = item.get("result")
        if not isinstance(result, str) or not result.strip():
            issues.append(f"checks[{index}].result must be nonempty text")
            result = ""
        else:
            result = _truncate(result, MAX_RESULT_CHARS, f"checks[{index}].result", issues)
        parsed.append({"command": command, "cwd": cwd, "exit_code": exit_code, "result": result})
    return parsed


def _parse_text_list(
    value: Any,
    label: str,
    max_count: int,
    max_chars: int,
    issues: list[str],
    *,
    optional: bool = False,
) -> list[str] | None:
    if value is None and optional:
        return None
    if not isinstance(value, list):
        issues.append(f"{label} must be an array of strings")
        return []
    if len(value) > max_count:
        issues.append(f"{label} exceeds {max_count} items")
        value = value[:max_count]
    parsed: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            issues.append(f"{label}[{index}] must be nonempty text")
            continue
        parsed.append(_truncate(item, max_chars, f"{label}[{index}]", issues))
    return parsed


def _read_observed_paths(path: Path | None, issues: list[str]) -> list[str] | None:
    if path is None:
        return None
    if not path.is_file():
        issues.append(f"changed-paths file not found: {path}")
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        issues.append(f"changed-paths file unreadable: {exc}")
        return None
    observed: list[str] = []
    for line in lines:
        value = line.strip()
        if value and value not in observed:
            observed.append(value)
    if len(observed) > MAX_PATH_COUNT:
        issues.append(f"changed-paths exceeds {MAX_PATH_COUNT} items")
        observed = observed[:MAX_PATH_COUNT]
    return observed


def _serialize(result: dict[str, Any], max_bytes: int) -> str:
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if len(data.encode("utf-8")) <= max_bytes:
        return data
    result["status"] = "unverified"
    result["status_source"] = "report-validation"
    result["issues"] = [f"normalized result exceeds {max_bytes} bytes; see raw report and path references"]
    result["summary"] = "Report requires inspection; detailed fields are in the referenced artifacts."
    for key in ("evidence", "unresolved", "checks"):
        result[key] = []
    for key in ("changed_paths", "reported_changed_paths"):
        result[key]["paths"] = []
        result[key]["complete"] = False
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def normalize(report_path: Path, changed_paths_path: Path | None, output_path: Path) -> dict[str, Any]:
    issues: list[str] = []
    raw_bytes = b""
    parse_mode = "missing"
    report: dict[str, Any] | None = None

    if report_path.is_file():
        try:
            raw_bytes = report_path.read_bytes()
        except OSError as exc:
            issues.append(f"report file unreadable: {exc}")
        else:
            if len(raw_bytes) > MAX_REPORT_BYTES:
                issues.append(f"raw report exceeds {MAX_REPORT_BYTES} bytes")
                parse_mode = "oversized"
            else:
                try:
                    text = raw_bytes.decode("utf-8")
                except UnicodeError as exc:
                    issues.append(f"report is not valid UTF-8: {exc}")
                else:
                    report, parse_mode, parse_issues = _extract_report(text)
                    issues.extend(parse_issues)
    else:
        issues.append(f"report file not found: {report_path}")

    status = "unverified"
    summary = ""
    checks: list[dict[str, Any]] = []
    unresolved: list[str] = []
    evidence: list[str] = []
    reported_paths: list[str] | None = None

    if report is not None:
        if type(report.get("schema_version")) is not int or report.get("schema_version") != SCHEMA_VERSION:
            issues.append(f"schema_version must be {SCHEMA_VERSION}")
        raw_status = report.get("status")
        if raw_status not in WORKER_STATUSES:
            issues.append("status must be completed, partial, or blocked")
        else:
            status = raw_status
        raw_summary = report.get("summary")
        if not isinstance(raw_summary, str) or not raw_summary.strip():
            issues.append("summary must be nonempty text")
        else:
            summary = _truncate(raw_summary, MAX_SUMMARY_CHARS, "summary", issues)
        checks = _parse_checks(report.get("checks"), issues)
        unresolved = _parse_text_list(
            report.get("unresolved"), "unresolved", MAX_UNRESOLVED_COUNT, MAX_UNRESOLVED_CHARS, issues
        ) or []
        evidence = _parse_text_list(
            report.get("evidence"), "evidence", MAX_EVIDENCE_COUNT, MAX_EVIDENCE_CHARS, issues
        ) or []
        reported_paths = _parse_text_list(
            report.get("changed_paths"),
            "reported_changed_paths",
            MAX_PATH_COUNT,
            MAX_PATH_CHARS,
            issues,
            optional=True,
        )

        if status == "completed":
            if not checks:
                issues.append("completed report has no executed checks")
            if any(check["exit_code"] != 0 for check in checks):
                issues.append("completed report has a check with nonzero or null exit_code")
            if unresolved:
                issues.append("completed report has unresolved criteria")

    observed = _read_observed_paths(changed_paths_path, issues)

    if issues:
        status = "unverified"

    raw_copy = output_path.with_name(output_path.stem + ".raw.txt")
    raw_copy.parent.mkdir(parents=True, exist_ok=True)
    raw_copy.write_bytes(raw_bytes)

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "status_source": "worker-report" if status in WORKER_STATUSES else "report-validation",
        "summary": summary,
        "checks": checks,
        "unresolved": unresolved,
        "evidence": evidence,
        "changed_paths": {
            "source": "git-observed" if observed is not None else "unavailable",
            "reference": str(changed_paths_path) if changed_paths_path is not None else None,
            "paths": observed or [],
        },
        "reported_changed_paths": {
            "source": "worker-reported" if reported_paths is not None else "not-reported",
            "paths": reported_paths or [],
        },
        "report": {
            "reference": str(raw_copy),
            "source": str(report_path),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "bytes": len(raw_bytes),
            "parse": parse_mode,
        },
        "issues": issues,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_serialize(result, MAX_NORMALIZED_BYTES), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="worker final report (text/JSON)")
    parser.add_argument("--changed-paths", type=Path, default=None, help="Git-observed changed paths")
    parser.add_argument("--output", type=Path, required=True, help="normalized worker-result.json path")
    args = parser.parse_args(argv)

    result = normalize(args.report, args.changed_paths, args.output)
    print(f"worker-result: {args.output} status={result['status']}")
    if result["status"] == "completed":
        return 0
    if result["status"] in {"partial", "blocked"}:
        return 1
    return 3


if __name__ == "__main__":
    sys.exit(main())
