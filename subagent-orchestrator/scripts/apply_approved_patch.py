#!/usr/bin/env python3
"""Check and optionally apply one root-approved patch inside a Git worktree.

The helper never writes anything unless ``--apply`` is given, never stages to
the index, and reads the patch bytes exactly once so every Git invocation sees
the same digest-verified input. It is deliberately not a cross-process lock or
an OS sandbox: the root serializes writers and this process must be run with
exclusive access to the worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath

from task_packet import PacketError, load_packet, matches, normalize_changed_path, scope_errors


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEAD_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
MODE_LINE_RE = re.compile(r"^(new file mode|deleted file mode) ([0-7]{6})$")
INDEX_LINE_RE = re.compile(r"^index [0-9a-fA-F]+\.\.[0-9a-fA-F]+(?: ([0-7]{6}))?$")
BINARY_LINE_RE = re.compile(r"^Binary files .* differ$")


class Rejection(Exception):
    """A deterministic refusal that maps to a stable reason code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def run_git(root: Path, args: list[str], data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run Git with an explicit argument list and no shell."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        input=b"" if data is None else data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_error(proc: subprocess.CompletedProcess[bytes]) -> str:
    for stream in (proc.stderr, proc.stdout):
        text = stream.decode("utf-8", "replace").strip()
        if text:
            return text.splitlines()[0][:200]
    return f"git exited with {proc.returncode}"


def resolve_root(cwd: Path) -> Path:
    if not cwd.is_dir():
        raise Rejection("cwd_not_worktree_root", f"--cwd is not a directory: {cwd}")
    proc = run_git(cwd, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise Rejection("cwd_not_worktree_root", git_error(proc))
    top = proc.stdout.decode("utf-8", "surrogateescape").strip()
    if not top or os.path.realpath(cwd) != os.path.realpath(top):
        raise Rejection("cwd_not_worktree_root", "--cwd must be the Git worktree root")
    return Path(os.path.realpath(cwd))


def get_head(root: Path) -> str:
    proc = run_git(root, ["rev-parse", "--verify", "HEAD"])
    if proc.returncode != 0:
        raise Rejection("head_unavailable", git_error(proc))
    return proc.stdout.decode("ascii", "replace").strip()


def analyze_patch(text: str) -> None:
    """Reject unsupported patch features before any Git application step.

    Only column-zero directive lines can appear outside hunk bodies, so matching
    them there cannot mistake regular file content for a directive.
    """
    saw_diff = False
    for raw_line in text.split("\n"):
        line = raw_line.rstrip("\r")
        if line.startswith("diff --git "):
            saw_diff = True
            continue
        if line.startswith("diff --cc ") or line.startswith("diff --combined "):
            raise Rejection("patch_unsupported_format", "combined merge diffs are not supported")
        if line.startswith("@@@"):
            raise Rejection("patch_unsupported_format", "combined merge hunks are not supported")
        if line.startswith("GIT binary patch") or BINARY_LINE_RE.match(line):
            raise Rejection("patch_binary", "binary patches are not supported")
        if line.startswith("rename from ") or line.startswith("rename to "):
            raise Rejection("patch_rename", "rename patches are not supported")
        if line.startswith("copy from ") or line.startswith("copy to "):
            raise Rejection("patch_copy", "copy patches are not supported")
        if line.startswith("old mode ") or line.startswith("new mode "):
            raise Rejection("patch_mode_change", "file mode changes are not supported")
        mode_match = MODE_LINE_RE.match(line)
        if mode_match:
            _check_mode(mode_match.group(2), allow_executable=mode_match.group(1) == "deleted file mode")
            continue
        index_match = INDEX_LINE_RE.match(line)
        if index_match and index_match.group(1):
            _check_mode(index_match.group(1), allow_executable=True)
    if not saw_diff:
        raise Rejection("patch_unsupported_format", "not a standard git diff patch")


def _check_mode(mode: str, *, allow_executable: bool = False) -> None:
    if mode == "100644" or (allow_executable and mode == "100755"):
        return
    if mode == "120000":
        raise Rejection("patch_symlink", "symlink patches are not supported")
    if mode == "160000":
        raise Rejection("patch_submodule", "submodule patches are not supported")
    raise Rejection("patch_unsupported_mode", f"unsupported file mode {mode}")


def parse_numstat(raw: bytes) -> list[str]:
    records = [record for record in raw.split(b"\0") if record]
    if not records:
        raise Rejection("patch_empty", "patch has no applicable file changes")
    paths: list[str] = []
    for record in records:
        parts = record.split(b"\t", 2)
        if len(parts) != 3:
            raise Rejection("patch_unsupported_format", "unexpected numstat record")
        added, deleted, path = parts
        if added == b"-" or deleted == b"-":
            raise Rejection("patch_binary", "binary patches are not supported")
        if not path:
            raise Rejection("patch_unsupported_format", "numstat record without a path")
        paths.append(path.decode("utf-8", "surrogateescape"))
    return paths


def load_scope(task_file: Path) -> tuple[list[str], list[str]]:
    try:
        return load_packet(task_file)
    except PacketError as exc:
        raise Rejection("task_packet_invalid", str(exc)) from exc
    except (OSError, UnicodeError) as exc:
        raise Rejection("task_packet_invalid", f"cannot read task packet: {exc}") from exc


def validate_paths(raw_paths: list[str], allowed: list[str], forbidden: list[str]) -> list[str]:
    paths: list[str] = []
    for raw in raw_paths:
        try:
            path = normalize_changed_path(raw)
        except PacketError as exc:
            raise Rejection("path_invalid", str(exc)) from exc
        if path != raw or PurePosixPath(path).as_posix() != raw:
            raise Rejection("path_invalid", "Git path must not change during normalization")
        if any(part.lower() == ".git" for part in PurePosixPath(path).parts):
            raise Rejection("git_dir_path", f"refusing a path inside .git: {path}")
        if any(matches(path, pattern) for pattern in forbidden):
            raise Rejection("forbidden_path", f"forbidden path changed: {path}")
        paths.append(path)
    errors = scope_errors(paths, allowed, forbidden)
    if errors:
        raise Rejection("out_of_scope", errors[0])
    return paths


def ensure_no_symlink(root: Path, path: str) -> None:
    current = root
    for part in PurePosixPath(path).parts:
        # Reject aliases conservatively, including on case-sensitive hosts, so
        # packet scope and dirty checks always refer to the same filesystem path.
        if current.is_dir():
            for entry in current.iterdir():
                if entry.name != part and path_key(entry.name) == path_key(part):
                    raise Rejection("path_alias", f"ambiguous filesystem spelling: {path}")
        current = current / part
        if current.is_symlink():
            raise Rejection("symlink_in_path", f"symlink in touched path: {path}")


def collect_dirty_paths(root: Path) -> list[str]:
    commands = (
        ["diff", "--cached", "--name-only", "-z", "--no-renames"],
        ["diff", "--name-only", "-z", "--no-renames"],
        ["ls-files", "--others", "--exclude-standard", "-z"],
        ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
    )
    paths: list[str] = []
    seen: set[str] = set()
    for command in commands:
        proc = run_git(root, command)
        if proc.returncode != 0:
            raise Rejection("git_error", git_error(proc))
        for chunk in proc.stdout.split(b"\0"):
            if not chunk:
                continue
            path = chunk.decode("utf-8", "surrogateescape").rstrip("/")
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    # Git diff can hide local edits under these index flags. Treat the flagged
    # paths as occupied rather than assuming their worktree contents are clean.
    proc = run_git(root, ["ls-files", "-v", "-z"])
    if proc.returncode != 0:
        raise Rejection("git_error", git_error(proc))
    for entry in proc.stdout.split(b"\0"):
        if len(entry) > 2 and (entry[:1].islower() or entry[:1] == b"S"):
            paths.append(entry[2:].decode("utf-8", "surrogateescape"))
    return paths


def path_key(path: str) -> str:
    return unicodedata.normalize("NFD", path).casefold()


def path_overlaps(target: str, dirty: str) -> bool:
    target, dirty = path_key(target), path_key(dirty)
    return target == dirty or target.startswith(dirty + "/") or dirty.startswith(target + "/")


def ensure_no_overlap(root: Path, targets: list[str]) -> None:
    for dirty in collect_dirty_paths(root):
        for target in targets:
            if path_overlaps(target, dirty):
                raise Rejection("dirty_overlap", f"target overlaps existing changes: {dirty}")


def run(args: argparse.Namespace, result: dict) -> None:
    approved = args.sha256.strip().lower()
    result["approved_sha256"] = approved
    if not SHA256_RE.fullmatch(approved):
        raise Rejection("digest_invalid", "--sha256 must be 64 lowercase hex characters")

    expected = args.expected_head.strip().lower()
    result["expected_head"] = expected
    if not HEAD_RE.fullmatch(expected):
        raise Rejection("head_invalid", "--expected-head must be the full 40- or 64-hex commit id")

    root = resolve_root(Path(args.cwd))
    head = get_head(root)
    result["actual_head"] = head
    if head.lower() != expected:
        raise Rejection("head_mismatch", "current HEAD does not match --expected-head")

    try:
        data = args.patch.read_bytes()
    except OSError as exc:
        raise Rejection("patch_unreadable", f"cannot read patch: {exc.strerror or exc}") from exc

    if hashlib.sha256(data).hexdigest() != approved:
        raise Rejection("digest_mismatch", "patch sha256 does not match --sha256")
    if not data.strip():
        raise Rejection("patch_empty", "patch is empty")

    analyze_patch(data.decode("utf-8", "surrogateescape"))

    numstat = run_git(root, ["apply", "--numstat", "-z"], data)
    if numstat.returncode != 0:
        raise Rejection("patch_invalid", git_error(numstat))
    raw_paths = parse_numstat(numstat.stdout)

    allowed, forbidden = load_scope(Path(args.task_file))
    paths = validate_paths(raw_paths, allowed, forbidden)
    result["touched_paths"] = paths

    for path in paths:
        ensure_no_symlink(root, path)
    ensure_no_overlap(root, paths)

    check = run_git(root, ["apply", "--check"], data)
    if check.returncode != 0:
        raise Rejection("apply_check_failed", git_error(check))

    if not args.apply:
        result["status"] = "checked"
        result["reason_code"] = "ok"
        result["reason"] = "patch verified; nothing written without --apply"
        return

    recheck_head = get_head(root)
    result["actual_head"] = recheck_head
    if recheck_head.lower() != expected:
        raise Rejection("head_mismatch", "HEAD changed before apply")
    for path in paths:
        ensure_no_symlink(root, path)
    ensure_no_overlap(root, paths)

    applied = run_git(root, ["apply"], data)
    if applied.returncode != 0:
        raise Rejection("apply_failed", git_error(applied))
    result["status"] = "applied"
    result["reason_code"] = "applied"
    result["reason"] = "patch applied to the worktree without staging"


def emit(result: dict) -> None:
    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True, help="target Git worktree root")
    parser.add_argument("--patch", type=Path, required=True, help="approved patch file")
    parser.add_argument("--sha256", required=True, help="exact root-approved SHA-256")
    parser.add_argument("--expected-head", required=True, help="exact full current HEAD")
    parser.add_argument("--task-file", type=Path, required=True, help="external task packet")
    parser.add_argument("--apply", action="store_true", help="apply after all checks pass")
    args = parser.parse_args(argv)

    result: dict = {
        "status": "rejected",
        "reason_code": "internal_error",
        "reason": "",
        "expected_head": args.expected_head,
        "actual_head": None,
        "approved_sha256": args.sha256,
        "touched_paths": [],
    }
    try:
        run(args, result)
    except Rejection as exc:
        result["status"] = "rejected"
        result["reason_code"] = exc.code
        result["reason"] = exc.message
        emit(result)
        return 1
    except (OSError, UnicodeError) as exc:
        result["status"] = "rejected"
        result["reason_code"] = "io_error"
        result["reason"] = str(exc)[:200]
        emit(result)
        return 2
    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
