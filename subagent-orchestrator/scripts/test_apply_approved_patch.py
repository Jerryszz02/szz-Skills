#!/usr/bin/env python3
"""Behavioral tests for the approved-patch helper using real Git repositories."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("apply_approved_patch.py")
ZERO_SHA256 = "0" * 64
ZERO_HEAD = "0" * 40


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def bullets(value: str) -> str:
    return "\n".join(f"- {item.strip()}" for item in value.split(",") if item.strip())


def write_packet(path: Path, allowed: str, forbidden: str) -> None:
    path.write_text(
        f"""# Task Packet

## Objective

Exercise the approved-patch helper.

## Dependencies

none

## Allowed paths

{bullets(allowed)}

## Forbidden paths

{bullets(forbidden)}

## Acceptance criteria

- The helper behaves deterministically.

## Required verification

- python3 -B -m unittest test_apply_approved_patch -v

## Explicit non-goals

- No edits outside the worktree.

## Nested delegation

forbidden

## HEAD-only dependency

yes
""",
        encoding="utf-8",
    )


def text_edit_patch(rel: str, old: str, new: str) -> bytes:
    return (
        f"diff --git a/{rel} b/{rel}\n"
        "index 1111111..2222222 100644\n"
        f"--- a/{rel}\n"
        f"+++ b/{rel}\n"
        "@@ -1 +1 @@\n"
        f"-{old}\n"
        f"+{new}\n"
    ).encode("utf-8")


def text_add_patch(rel: str, text: str) -> bytes:
    return (
        f"diff --git a/{rel} b/{rel}\n"
        "new file mode 100644\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{rel}\n"
        "@@ -0,0 +1 @@\n"
        f"+{text}\n"
    ).encode("utf-8")


def mode_patch(rel: str, mode: str, text: str = "x") -> bytes:
    return (
        f"diff --git a/{rel} b/{rel}\n"
        f"new file mode {mode}\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{rel}\n"
        "@@ -0,0 +1 @@\n"
        f"+{text}\n"
    ).encode("utf-8")


class ApprovedPatchTests(unittest.TestCase):
    allowed = "work/**"
    forbidden = ".git/**,work/secret/**"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, capture_output=True)
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        self.write("work/target.txt", "old\n")
        self.write("work/staged.txt", "staged-base\n")
        self.write("work/unstaged.txt", "unstaged-base\n")
        self.write("work/secret/hidden.txt", "secret\n")
        self.write("outside.txt", "outside\n")
        self.write(".gitignore", "ignored.txt\n")
        self.commit()
        self.packet = self.root / "task.md"
        write_packet(self.packet, self.allowed, self.forbidden)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- fixture helpers -------------------------------------------------

    def write(self, rel: str, text: str) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, rel: str, data: bytes) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def read(self, rel: str) -> str:
        return (self.repo / rel).read_text(encoding="utf-8")

    def commit(self, message: str = "base") -> None:
        git(self.repo, "add", "-A")
        proc = git(self.repo, "commit", "-qm", message)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())

    def head(self) -> str:
        return git(self.repo, "rev-parse", "HEAD").stdout.decode().strip()

    def make_edit_patch(self, rel: str, new_text: str) -> bytes:
        path = self.write(rel, new_text)
        patch = git(self.repo, "diff", "--", rel).stdout
        proc = git(self.repo, "checkout", "--", rel)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertTrue(path.exists())
        return patch

    def make_add_patch(self, rel: str, text: str) -> bytes:
        self.write(rel, text)
        git(self.repo, "add", "-N", "--", rel)
        patch = git(self.repo, "diff", "--", rel).stdout
        git(self.repo, "reset", "-q", "--", rel)
        (self.repo / rel).unlink()
        self.assertEqual(git(self.repo, "status", "--porcelain").stdout, b"")
        return patch

    def invoke(
        self,
        patch: bytes,
        *,
        apply: bool = False,
        sha256: str | None = None,
        expected_head: str | None = None,
        cwd: Path | None = None,
        task_file: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        patch_file = self.root / "change.patch"
        patch_file.write_bytes(patch)
        command = [
            sys.executable,
            str(SCRIPT),
            "--cwd",
            str(cwd or self.repo),
            "--patch",
            str(patch_file),
            "--sha256",
            sha256 if sha256 is not None else hashlib.sha256(patch).hexdigest(),
            "--expected-head",
            expected_head if expected_head is not None else self.head(),
            "--task-file",
            str(task_file or self.packet),
        ]
        if apply:
            command.append("--apply")
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def result(self, proc: subprocess.CompletedProcess[str]) -> dict:
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return json.loads(proc.stdout)

    # -- check-only and successful apply --------------------------------

    def test_check_only_leaves_bytes_and_index_unchanged(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        before_status = git(self.repo, "status", "--porcelain=v1", "-z").stdout
        proc = self.invoke(patch)
        data = self.result(proc)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(data["status"], "checked")
        self.assertEqual(data["touched_paths"], ["work/target.txt"])
        self.assertEqual(data["actual_head"], self.head())
        self.assertEqual((self.repo / "work/target.txt").read_bytes(), b"old\n")
        self.assertEqual(git(self.repo, "status", "--porcelain=v1", "-z").stdout, before_status)
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only", "-z").stdout, b"")

    def test_apply_edit_preserves_unrelated_staged_and_unstaged(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        self.write("work/staged.txt", "staged-change\n")
        git(self.repo, "add", "work/staged.txt")
        self.write("work/unstaged.txt", "unstaged-change\n")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(data["status"], "applied")
        self.assertEqual(self.read("work/target.txt"), "new\n")
        self.assertEqual(self.read("work/staged.txt"), "staged-change\n")
        self.assertEqual(self.read("work/unstaged.txt"), "unstaged-change\n")
        self.assertIn(b"work/staged.txt", git(self.repo, "diff", "--cached", "--name-only", "-z").stdout)
        self.assertIn(b"work/unstaged.txt", git(self.repo, "diff", "--name-only", "-z").stdout)

    def test_apply_add_and_delete_text_files(self) -> None:
        add = self.make_add_patch("work/added.txt", "added\n")
        proc = self.invoke(add, apply=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.read("work/added.txt"), "added\n")
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only", "-z").stdout, b"")

        self.write("work/doomed.txt", "doomed\n")
        self.commit("add doomed")
        (self.repo / "work/doomed.txt").unlink()
        delete = git(self.repo, "diff", "--", "work/doomed.txt").stdout
        git(self.repo, "checkout", "--", "work/doomed.txt")
        proc = self.invoke(delete, apply=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.repo / "work/doomed.txt").exists())

    # -- digest and HEAD gates ------------------------------------------

    def test_content_edit_of_executable_preserves_mode_and_index(self) -> None:
        path = self.write("work/run.sh", "#!/bin/sh\necho old\n")
        path.chmod(0o755)
        self.commit("executable base")
        self.write("work/run.sh", "#!/bin/sh\necho new\n")
        patch = git(self.repo, "diff", "--binary", "--", "work/run.sh").stdout
        git(self.repo, "checkout", "--", "work/run.sh")
        self.assertIn(b" 100755\n", patch)
        before_index = git(self.repo, "ls-files", "--stage", "-z").stdout
        before_mode = path.stat().st_mode
        checked = self.invoke(patch)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertEqual(self.read("work/run.sh"), "#!/bin/sh\necho old\n")
        applied = self.invoke(patch, apply=True)
        self.assertEqual(applied.returncode, 0, applied.stdout)
        self.assertEqual(self.read("work/run.sh"), "#!/bin/sh\necho new\n")
        self.assertEqual(path.stat().st_mode, before_mode)
        self.assertEqual(git(self.repo, "ls-files", "--stage", "-z").stdout, before_index)

    def test_delete_executable_text_file_preserves_index(self) -> None:
        path = self.write("work/run.sh", "#!/bin/sh\necho old\n")
        path.chmod(0o755)
        self.commit("executable base")
        path.unlink()
        patch = git(self.repo, "diff", "--binary", "--", "work/run.sh").stdout
        git(self.repo, "checkout", "--", "work/run.sh")
        self.assertIn(b"deleted file mode 100755\n", patch)
        before_index = git(self.repo, "ls-files", "--stage", "-z").stdout
        checked = self.invoke(patch)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertTrue(path.exists())
        applied = self.invoke(patch, apply=True)
        self.assertEqual(applied.returncode, 0, applied.stdout)
        self.assertFalse(path.exists())
        self.assertEqual(git(self.repo, "ls-files", "--stage", "-z").stdout, before_index)

    def test_sha256_repository_requires_exact_full_head(self) -> None:
        self.repo = self.root / "sha256-repo"
        proc = subprocess.run(
            ["git", "init", "-q", "--object-format=sha256", str(self.repo)],
            capture_output=True, check=False,
        )
        if proc.returncode:
            self.skipTest("installed Git cannot initialize SHA-256 repositories")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        self.write("work/target.txt", "old\n")
        self.commit()
        head = self.head()
        self.assertEqual(len(head), 64)
        patch = self.make_edit_patch("work/target.txt", "new\n")
        for expected, reason in ((head[:40], "head_mismatch"),
                                 (head[:63], "head_invalid"),
                                 ("0" * 64, "head_mismatch")):
            with self.subTest(expected=expected):
                rejected = self.invoke(patch, apply=True, expected_head=expected)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(self.result(rejected)["reason_code"], reason)
                self.assertEqual(self.read("work/target.txt"), "old\n")
        checked = self.invoke(patch)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertEqual(self.result(checked)["actual_head"], head)
        self.assertEqual(self.read("work/target.txt"), "old\n")
        applied = self.invoke(patch, apply=True)
        self.assertEqual(applied.returncode, 0, applied.stdout)
        self.assertEqual(self.read("work/target.txt"), "new\n")
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only").stdout, b"")

    def test_digest_mismatch(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        proc = self.invoke(patch, sha256=ZERO_SHA256)
        data = self.result(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(data["status"], "rejected")
        self.assertEqual(data["reason_code"], "digest_mismatch")
        self.assertEqual(self.read("work/target.txt"), "old\n")

    def test_head_mismatch(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        proc = self.invoke(patch, expected_head=ZERO_HEAD)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "head_mismatch")
        self.assertEqual(data["actual_head"], self.head())
        self.assertEqual(data["expected_head"], ZERO_HEAD)

    def test_head_and_digest_format_rejected(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        data = self.result(self.invoke(patch, expected_head="abc"))
        self.assertEqual(data["reason_code"], "head_invalid")
        data = self.result(self.invoke(patch, sha256="xyz"))
        self.assertEqual(data["reason_code"], "digest_invalid")

    # -- packet scope ----------------------------------------------------

    def test_out_of_scope_path(self) -> None:
        patch = self.make_edit_patch("outside.txt", "changed\n")
        data = self.result(self.invoke(patch))
        self.assertEqual(data["reason_code"], "out_of_scope")
        self.assertEqual(self.read("outside.txt"), "outside\n")

    def test_forbidden_path(self) -> None:
        patch = self.make_edit_patch("work/secret/hidden.txt", "leaked\n")
        data = self.result(self.invoke(patch))
        self.assertEqual(data["reason_code"], "forbidden_path")
        self.assertEqual(self.read("work/secret/hidden.txt"), "secret\n")

    def test_invalid_task_packet(self) -> None:
        bad = self.root / "bad-task.md"
        bad.write_text("no sections here", encoding="utf-8")
        patch = self.make_edit_patch("work/target.txt", "new\n")
        data = self.result(self.invoke(patch, task_file=bad))
        self.assertEqual(data["reason_code"], "task_packet_invalid")

    def test_cwd_must_be_worktree_root(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        data = self.result(self.invoke(patch, cwd=self.repo / "work"))
        self.assertEqual(data["reason_code"], "cwd_not_worktree_root")

    # -- dirty overlap ---------------------------------------------------

    def test_git_path_identity_is_not_normalized_into_allowed_scope(self) -> None:
        for rel, allowed in (("work/name\\file.txt", "work/name/file.txt"),
                             ("work/name.txt ", "work/name.txt")):
            with self.subTest(rel=rel):
                self.write(rel, "old\n")
                self.commit()
                write_packet(self.packet, allowed, self.forbidden)
                patch = self.make_edit_patch(rel, "new\n")
                proc = self.invoke(patch, apply=True)
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(self.result(proc)["reason_code"], "path_invalid")
                self.assertEqual(self.read(rel), "old\n")

    def test_case_alias_cannot_bypass_scope_or_local_edits(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        patch = patch.replace(b"work/target.txt", b"WORK/target.txt")
        write_packet(self.packet, "WORK/**", self.forbidden)
        self.write("work/target.txt", "old\nuser data\n")
        proc = self.invoke(patch, apply=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.result(proc)["reason_code"], "path_alias")
        self.assertEqual(self.read("work/target.txt"), "old\nuser data\n")

    def test_case_alias_cannot_bypass_forbidden_directory(self) -> None:
        patch = text_add_patch("work/SECRET/new.txt", "new")
        proc = self.invoke(patch, apply=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.result(proc)["reason_code"], "path_alias")
        self.assertFalse((self.repo / "work/secret/new.txt").exists())

    def test_unicode_alias_is_rejected(self) -> None:
        self.write("work/caf\u00e9.txt", "old\n")
        self.commit()
        tracked = git(self.repo, "ls-files", "-z", "work/caf*").stdout.split(b"\0")[0].decode()
        import unicodedata
        existing = next(p.name for p in (self.repo / "work").iterdir() if p.name.startswith("caf"))
        other = unicodedata.normalize("NFD" if existing == unicodedata.normalize("NFC", existing) else "NFC", existing)
        patch = text_edit_patch("work/" + other, "old", "new")
        proc = self.invoke(patch, apply=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.result(proc)["reason_code"], "path_alias")
        self.assertEqual(self.read(tracked), "old\n")

    def test_hidden_index_flags_are_not_treated_as_clean(self) -> None:
        for flag in ("assume-unchanged", "skip-worktree"):
            with self.subTest(flag=flag):
                patch = self.make_edit_patch("work/target.txt", "new\n")
                self.assertEqual(git(self.repo, "update-index", "--" + flag, "work/target.txt").returncode, 0)
                self.write("work/target.txt", "old\nlocal data\n")
                try:
                    proc = self.invoke(patch, apply=True)
                    self.assertNotEqual(proc.returncode, 0)
                    self.assertEqual(self.result(proc)["reason_code"], "dirty_overlap")
                    self.assertEqual(self.read("work/target.txt"), "old\nlocal data\n")
                finally:
                    git(self.repo, "update-index", "--no-" + flag, "work/target.txt")
                    self.write("work/target.txt", "old\n")

    def test_staged_overlap_rejected(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        self.write("work/target.txt", "staged-conflict\n")
        git(self.repo, "add", "work/target.txt")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "dirty_overlap")
        self.assertEqual(self.read("work/target.txt"), "staged-conflict\n")

    def test_unstaged_overlap_rejected(self) -> None:
        patch = self.make_edit_patch("work/target.txt", "new\n")
        self.write("work/target.txt", "unstaged-conflict\n")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "dirty_overlap")
        self.assertEqual(self.read("work/target.txt"), "unstaged-conflict\n")

    def test_untracked_overlap_rejected(self) -> None:
        patch = self.make_add_patch("work/newfile.txt", "new\n")
        self.write("work/newfile.txt", "untracked\n")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "dirty_overlap")
        self.assertEqual(self.read("work/newfile.txt"), "untracked\n")

    def test_ignored_overlap_rejected(self) -> None:
        patch = text_add_patch("work/ignored.txt", "ignored new")
        self.write("work/ignored.txt", "ignored existing\n")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "dirty_overlap")
        self.assertEqual(self.read("work/ignored.txt"), "ignored existing\n")

    def test_ancestor_descendant_overlap_rejected(self) -> None:
        patch = self.make_add_patch("work/a.txt", "a\n")
        self.write("work/a.txt/inner.txt", "inner\n")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "dirty_overlap")
        self.assertFalse((self.repo / "work/a.txt").is_file())

    # -- symlink guard ---------------------------------------------------

    def test_symlink_ancestor_path_rejected(self) -> None:
        self.write("work/real/target.txt", "old\n")
        os.symlink("real", self.repo / "work" / "linkdir")
        self.commit("symlink dir")
        patch = text_edit_patch("work/linkdir/target.txt", "old", "new")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "symlink_in_path")
        self.assertEqual(self.read("work/real/target.txt"), "old\n")

    # -- supported and unsupported patch shapes --------------------------

    def test_empty_and_malformed_patch_rejected(self) -> None:
        data = self.result(self.invoke(b""))
        self.assertEqual(data["reason_code"], "patch_empty")
        data = self.result(self.invoke(b"this is not a patch\n"))
        self.assertEqual(data["reason_code"], "patch_unsupported_format")
        corrupt = b"diff --git a/work/target.txt b/work/target.txt\n@@ nonsense @@\n"
        data = self.result(self.invoke(corrupt))
        self.assertEqual(data["reason_code"], "patch_invalid")

    def test_conflicting_patch_does_not_change_file(self) -> None:
        patch = text_edit_patch("work/target.txt", "WRONG", "new")
        proc = self.invoke(patch, apply=True)
        data = self.result(proc)
        self.assertEqual(data["reason_code"], "apply_check_failed")
        self.assertEqual(self.read("work/target.txt"), "old\n")

    def test_rename_patch_rejected(self) -> None:
        git(self.repo, "mv", "work/target.txt", "work/moved.txt")
        patch = git(self.repo, "diff", "--cached", "-M").stdout
        git(self.repo, "reset", "-q", "--hard")
        data = self.result(self.invoke(patch))
        self.assertEqual(data["reason_code"], "patch_rename")

    def test_copy_patch_rejected(self) -> None:
        patch = (
            "diff --git a/work/target.txt b/work/copied.txt\n"
            "similarity index 100%\n"
            "copy from work/target.txt\n"
            "copy to work/copied.txt\n"
        ).encode("utf-8")
        data = self.result(self.invoke(patch))
        self.assertEqual(data["reason_code"], "patch_copy")

    def test_binary_patch_rejected(self) -> None:
        self.write_bytes("work/data.bin", b"\x00\x01\x02base")
        self.commit("binary base")
        self.write_bytes("work/data.bin", b"\x00\x01\x03changed")
        plain = git(self.repo, "diff", "--", "work/data.bin").stdout
        binary = git(self.repo, "diff", "--binary", "--", "work/data.bin").stdout
        git(self.repo, "checkout", "--", "work/data.bin")
        self.assertIn(b"Binary files", plain)
        self.assertIn(b"GIT binary patch", binary)
        self.assertEqual(self.result(self.invoke(plain))["reason_code"], "patch_binary")
        self.assertEqual(self.result(self.invoke(binary))["reason_code"], "patch_binary")

    def test_mode_patch_rejected(self) -> None:
        for before, after in ((0o644, 0o755), (0o755, 0o644)):
            for content_change in (False, True):
                with self.subTest(before=before, content_change=content_change):
                    path = self.write("work/target.txt", "old\n")
                    path.chmod(before)
                    git(self.repo, "add", "work/target.txt")
                    committed = git(self.repo, "commit", "--allow-empty", "-qm", "mode base")
                    self.assertEqual(committed.returncode, 0, committed.stderr.decode())
                    path.chmod(after)
                    if content_change:
                        self.write("work/target.txt", "new\n")
                    patch = git(self.repo, "diff", "--binary", "--", "work/target.txt").stdout
                    git(self.repo, "checkout", "--", "work/target.txt")
                    proc = self.invoke(patch, apply=True)
                    self.assertNotEqual(proc.returncode, 0)
                    self.assertEqual(self.result(proc)["reason_code"], "patch_mode_change")
                    self.assertEqual(self.read("work/target.txt"), "old\n")
                    self.assertEqual(path.stat().st_mode & 0o777, before)

    def test_symlink_patch_rejected(self) -> None:
        os.symlink("target.txt", self.repo / "work" / "link.txt")
        git(self.repo, "add", "work/link.txt")
        patch = git(self.repo, "diff", "--cached", "--", "work/link.txt").stdout
        git(self.repo, "reset", "-q", "--hard")
        self.assertEqual(self.result(self.invoke(patch))["reason_code"], "patch_symlink")

    def test_unsupported_and_submodule_modes_rejected(self) -> None:
        executable = mode_patch("work/run.sh", "100755")
        self.assertEqual(self.result(self.invoke(executable))["reason_code"], "patch_unsupported_mode")
        directory = mode_patch("work/dir", "040000")
        self.assertEqual(self.result(self.invoke(directory))["reason_code"], "patch_unsupported_mode")
        submodule = mode_patch("work/sub", "160000", "Subproject commit 1111111111111111111111111111111111111111")
        self.assertEqual(self.result(self.invoke(submodule))["reason_code"], "patch_submodule")


if __name__ == "__main__":
    unittest.main()
