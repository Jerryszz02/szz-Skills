"""Executable discovery and preflight evidence tests without provider traffic."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from route_diagnostics import resolve_cli
import test_dsh_runner
import test_kimi_runner


class ResolutionTests(unittest.TestCase):
    def test_user_install_fallback_and_invalid_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for provider, rel in [("dsh", ".local/bin/dsh"), ("kimi", ".kimi-code/bin/kimi")]:
                binary = home / rel
                binary.parent.mkdir(parents=True, exist_ok=True)
                binary.write_text("#!/bin/sh\nexit 0\n")
                binary.chmod(0o755)
                with patch("route_diagnostics.Path.home", return_value=home), patch.dict(os.environ, {"PATH": ""}, clear=True):
                    result = resolve_cli(provider)
                    self.assertEqual(result["executable"], str(binary))
                    self.assertEqual(result["resolution_source"], "user_install")
                    with patch.dict(os.environ, {provider.upper() + "_BIN": str(home / "missing")}):
                        self.assertIsNone(resolve_cli(provider)["executable"])

    def test_path_wins_and_nonexecutable_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"PATH": tmp}, clear=True):
            executable = Path(tmp) / "dsh"
            executable.write_text("#!/bin/sh\n")
            with patch("route_diagnostics.Path.home", return_value=Path(tmp) / "absent"):
                self.assertIsNone(resolve_cli("dsh")["executable"])
                executable.chmod(0o755)
                self.assertEqual(resolve_cli("dsh")["resolution_source"], "PATH")

    def test_policy_skip_makes_no_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "route.json"
            result = subprocess.run([
                "python3", str(Path(__file__).with_name("route_diagnostics.py")), "skip",
                "--provider", "dsh", "--output", str(output), "--slice-id", "auth",
                "--reason", "external_boundary", "--detail", "Authentication changes are native-only",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(output.read_text())
            self.assertEqual(value["execution_state"], "not_started")
            self.assertNotIn("usage", value)


class DshDiagnosticsTests(unittest.TestCase):
    setUp = test_dsh_runner.DshRunnerTests.setUp
    tearDown = test_dsh_runner.DshRunnerTests.tearDown
    invoke = test_dsh_runner.DshRunnerTests.invoke

    def test_missing_binary_has_diagnostic_without_execution(self):
        output = self.root / "missing-cli"
        result = self.invoke(output, DSH_BIN=str(self.root / "missing"))
        self.assertEqual(result.returncode, 69)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "cli_missing")
        self.assertEqual(value["execution_state"], "not_started")
        self.assertFalse((output / "worker-receipt.json").exists())

    def test_help_failure_has_specific_reason(self):
        output = self.root / "help-failed"
        result = self.invoke(output, FAKE_DSH_PREFLIGHT_EXIT="3")
        self.assertEqual(result.returncode, 69)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "headless_preflight_failed")
        self.assertEqual(value["execution_state"], "not_started")

    def test_success_links_runtime_usage(self):
        output = self.root / "success"
        self.assertEqual(self.invoke(output).returncode, 0)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "completed")
        self.assertEqual(value["execution_state"], "observed")
        self.assertEqual(value["usage"]["total_tokens"], 170)
        self.assertTrue(Path(value["receipt"]).is_file())

    def test_bad_packet_is_not_an_attempt(self):
        output = self.root / "bad-packet"
        self.packet.write_text("invalid packet")
        self.assertNotEqual(self.invoke(output).returncode, 0)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "task_packet_invalid")
        self.assertEqual(value["execution_state"], "not_started")

    def test_dirty_overlap_records_no_execution(self):
        output = self.root / "dirty"
        (self.repo / "generated.txt").write_text("uncommitted")
        self.assertEqual(self.invoke(output).returncode, 65)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "dirty_overlap")
        self.assertEqual(value["execution_state"], "not_started")

    def test_missing_post_launch_usage_stays_unknown(self):
        output = self.root / "missing-usage"
        self.assertEqual(self.invoke(output, FAKE_DSH_NO_SESSION="1").returncode, 75)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "metadata_incomplete")
        self.assertEqual(value["execution_state"], "unknown")
        self.assertIsNone(value["usage"]["total_tokens"])


class KimiDiagnosticsTests(unittest.TestCase):
    setUp = test_kimi_runner.KimiRunnerTests.setUp
    tearDown = test_kimi_runner.KimiRunnerTests.tearDown
    invoke = test_kimi_runner.KimiRunnerTests.invoke

    def test_missing_binary_has_diagnostic(self):
        output = self.root / "missing-cli"
        result = self.invoke(output, KIMI_BIN=str(self.root / "missing"))
        self.assertEqual(result.returncode, 69)
        value = json.loads((output / "route.json").read_text())
        self.assertEqual(value["reason_code"], "cli_missing")
        self.assertEqual(value["execution_state"], "not_started")


if __name__ == "__main__":
    unittest.main()
