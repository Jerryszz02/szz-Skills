#!/usr/bin/env python3
"""Validate subagent task packets and enforce external-worker path ownership."""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path, PurePosixPath


REQUIRED_SECTIONS = (
    "objective",
    "dependencies",
    "allowed paths",
    "forbidden paths",
    "acceptance criteria",
    "required verification",
    "explicit non-goals",
    "nested delegation",
    "head-only dependency",
)
UNBOUNDED_PATTERNS = {".", "*", "**", "./*", "./**"}


class PacketError(ValueError):
    """Raised when a task packet violates the orchestration contract."""


def normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", raw_line)
        if match:
            current = normalize_heading(match.group(1))
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(raw_line)
    return sections


def nonempty_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def parse_bullets(lines: list[str], section: str) -> list[str]:
    values: list[str] = []
    for line in nonempty_lines(lines):
        if not line.startswith("-"):
            raise PacketError(f"{section} entries must use Markdown bullets")
        value = line[1:].strip().strip("`")
        if not value:
            raise PacketError(f"{section} contains an empty entry")
        values.append(value)
    if not values:
        raise PacketError(f"{section} must contain at least one entry")
    return values


def validate_pattern(pattern: str, *, allowed: bool) -> str:
    normalized = pattern.replace("\\", "/").removeprefix("./")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise PacketError(f"invalid repository-relative path pattern: {pattern}")
    if allowed and normalized in UNBOUNDED_PATTERNS:
        raise PacketError(f"allowed path is not bounded: {pattern}")
    if allowed and (normalized == ".git" or normalized.startswith(".git/")):
        raise PacketError(".git cannot be an allowed path")
    return normalized


def load_packet(path: Path) -> tuple[list[str], list[str]]:
    sections = parse_sections(path.read_text(encoding="utf-8"))
    missing = [name for name in REQUIRED_SECTIONS if not nonempty_lines(sections.get(name, []))]
    if missing:
        raise PacketError("missing or empty sections: " + ", ".join(missing))

    head_only = nonempty_lines(sections["head-only dependency"])[0].lower()
    if head_only not in {"yes", "true"}:
        raise PacketError("HEAD-only dependency must be yes")

    nested_delegation = nonempty_lines(sections["nested delegation"])[0].lower()
    if nested_delegation != "forbidden":
        raise PacketError("Nested delegation must be forbidden")

    allowed = [validate_pattern(value, allowed=True) for value in parse_bullets(sections["allowed paths"], "Allowed paths")]
    forbidden = [
        validate_pattern(value, allowed=False)
        for value in parse_bullets(sections["forbidden paths"], "Forbidden paths")
    ]
    return allowed, forbidden


def normalize_changed_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/").removeprefix("./")
    if not normalized or PurePosixPath(normalized).is_absolute() or ".." in PurePosixPath(normalized).parts:
        raise PacketError(f"invalid changed path: {value}")
    return normalized


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if pattern.endswith("/"):
        return path.startswith(pattern)
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")
    return len(path_parts) == len(pattern_parts) and all(
        fnmatch.fnmatchcase(path_part, pattern_part)
        for path_part, pattern_part in zip(path_parts, pattern_parts)
    )


def scope_errors(paths: list[str], allowed: list[str], forbidden: list[str]) -> list[str]:
    errors: list[str] = []
    for raw_path in paths:
        path = normalize_changed_path(raw_path)
        if any(matches(path, pattern) for pattern in forbidden):
            errors.append(f"forbidden path changed: {path}")
        elif not any(matches(path, pattern) for pattern in allowed):
            errors.append(f"path outside allowed scope: {path}")
    return errors


def allowed_overlaps(paths: list[str], allowed: list[str]) -> list[str]:
    overlaps: list[str] = []
    for raw_path in paths:
        path = normalize_changed_path(raw_path)
        if any(matches(path, pattern) or matches(pattern.rstrip("/**"), path + "/**") for pattern in allowed):
            overlaps.append(path)
    return overlaps


def read_paths(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--task-file", type=Path, required=True)

    check_parser = subparsers.add_parser("check-paths")
    check_parser.add_argument("--task-file", type=Path, required=True)
    check_parser.add_argument("--paths-file", type=Path, required=True)

    overlap_parser = subparsers.add_parser("check-overlap")
    overlap_parser.add_argument("--task-file", type=Path, required=True)
    overlap_parser.add_argument("--paths-file", type=Path, required=True)

    args = parser.parse_args()
    try:
        allowed, forbidden = load_packet(args.task_file)
        if args.command == "validate":
            return 0
        paths = read_paths(args.paths_file)
        if args.command == "check-paths":
            errors = scope_errors(paths, allowed, forbidden)
        else:
            errors = [f"allowed path has uncommitted changes: {path}" for path in allowed_overlaps(paths, allowed)]
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0
    except (OSError, UnicodeError, PacketError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
