#!/usr/bin/env python3
"""Regression tests for non-gpt-subagent-worker routing."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from worker_routing import (
    RoutingError,
    codex_exec_command,
    deepseek_endpoint,
    normalize_provider,
    require_deepseek_key,
    shell_quote,
    validate_sandbox,
    validate_spec,
)


SCRIPT_DIR = Path(__file__).resolve().parent


class WorkerRoutingTests(unittest.TestCase):
    def test_provider_aliases(self) -> None:
        self.assertEqual(normalize_provider("ollama"), "ollama")
        self.assertEqual(normalize_provider("LM Studio"), "lmstudio")
        self.assertEqual(normalize_provider("lm-studio"), "lmstudio")
        self.assertEqual(normalize_provider("deepseek"), "deepseek")

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaises(RoutingError):
            normalize_provider("claude")

    def test_sandbox_rejects_danger_full_access(self) -> None:
        self.assertEqual(validate_sandbox("workspace-write"), "workspace-write")
        with self.assertRaises(RoutingError):
            validate_sandbox("danger-full-access")

    def test_codex_ollama_command_shape(self) -> None:
        spec = validate_spec("ollama", "qwen2.5-coder", "/tmp/project", "workspace-write", "/tmp/out.md")
        command = codex_exec_command(spec)
        self.assertEqual(command[:5], ["codex", "exec", "--oss", "--local-provider", "ollama"])
        self.assertIn("--sandbox", command)
        self.assertIn("--output-last-message", command)
        self.assertEqual(command[-1], "-")

    def test_codex_lmstudio_command_shape(self) -> None:
        spec = validate_spec("lm studio", "zai-org_glm-4.5-air", "/tmp/project", "read-only", "/tmp/out.md")
        command = codex_exec_command(spec)
        self.assertIn("lmstudio", command)
        self.assertIn("zai-org_glm-4.5-air", command)

    def test_deepseek_key_is_required_without_leaking_value(self) -> None:
        with self.assertRaises(RoutingError) as raised:
            require_deepseek_key({})
        self.assertNotIn("sk-", str(raised.exception))

    def test_deepseek_endpoint_default_and_override(self) -> None:
        self.assertEqual(deepseek_endpoint({}), "https://api.deepseek.com/v1/chat/completions")
        self.assertEqual(deepseek_endpoint({"DEEPSEEK_BASE_URL": "https://example.test/v1"}), "https://example.test/v1")

    def test_shell_quote(self) -> None:
        self.assertEqual(shell_quote(["a", "b c"]), "a 'b c'")

    def test_run_worker_dry_run_ollama(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            output_file = Path(tmpdir) / "out.md"
            task_file.write_text("inspect tests\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_DIR / "run-worker.sh"),
                    "--provider",
                    "ollama",
                    "--model",
                    "qwen2.5-coder",
                    "--cwd",
                    tmpdir,
                    "--task-file",
                    str(task_file),
                    "--output",
                    str(output_file),
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--local-provider ollama", proc.stdout)
            self.assertIn("--sandbox workspace-write", proc.stdout)

    def test_repeated_dry_runs_do_not_collide_on_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            output_file = Path(tmpdir) / "out.md"
            task_file.write_text("inspect tests\n", encoding="utf-8")
            cmd = [
                "bash",
                str(SCRIPT_DIR / "run-worker.sh"),
                "--provider",
                "lmstudio",
                "--model",
                "zai-org_glm-4.5-air",
                "--cwd",
                tmpdir,
                "--task-file",
                str(task_file),
                "--output",
                str(output_file),
                "--dry-run",
            ]
            first = subprocess.run(cmd, text=True, capture_output=True, check=False)
            second = subprocess.run(cmd, text=True, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)

    def test_deepseek_missing_key_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = dict(os.environ)
            env.pop("DEEPSEEK_API_KEY", None)
            task_file = Path(tmpdir) / "task.md"
            output_file = Path(tmpdir) / "out.md"
            task_file.write_text("summarize context\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_DIR / "run-deepseek-worker.sh"),
                    "--model",
                    "deepseek-chat",
                    "--cwd",
                    tmpdir,
                    "--task-file",
                    str(task_file),
                    "--output",
                    str(output_file),
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("DEEPSEEK_API_KEY is required", proc.stderr)


if __name__ == "__main__":
    unittest.main()
