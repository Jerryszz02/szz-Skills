#!/usr/bin/env python3
"""Focused tests for the unified native worker receipt schema."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RECEIPT = SCRIPT_DIR / "worker_receipt.py"


class NativeReceiptTests(unittest.TestCase):
    def test_native_receipt_records_dispatch_and_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "task.md"
            packet.write_text("# Task Packet\n\n## Objective\n\nInspect the target.\n", encoding="utf-8")
            output = root / "receipt.json"
            result = subprocess.run(
                (
                    "python3",
                    str(RECEIPT),
                    "native",
                    "--task-file",
                    str(packet),
                    "--output",
                    str(output),
                    "--status",
                    "completed",
                    "--worker",
                    "luna",
                    "--actual-model",
                    "gpt-5.6-luna",
                    "--reasoning-effort",
                    "low",
                    "--fork-turns",
                    "none",
                    "--input-tokens",
                    "100",
                    "--cached-input-tokens",
                    "40",
                    "--output-tokens",
                    "20",
                ),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["actual_model"], "gpt-5.6-luna")
            self.assertEqual(receipt["reasoning_effort"], "low")
            self.assertEqual(receipt["fork_turns"], "none")
            self.assertEqual(receipt["usage"]["input_tokens"], 100)
            self.assertEqual(receipt["usage"]["total_tokens"], 120)

    def test_native_receipt_rejects_partial_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "task.md"
            packet.write_text("# Task Packet\n\n## Objective\n\nInspect the target.\n", encoding="utf-8")
            result = subprocess.run(
                (
                    "python3",
                    str(RECEIPT),
                    "native",
                    "--task-file",
                    str(packet),
                    "--output",
                    str(root / "receipt.json"),
                    "--status",
                    "completed",
                    "--worker",
                    "terra",
                    "--actual-model",
                    "gpt-5.6-terra",
                    "--reasoning-effort",
                    "medium",
                    "--fork-turns",
                    "none",
                    "--input-tokens",
                    "100",
                ),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires input, cached input, and output together", result.stderr)


if __name__ == "__main__":
    unittest.main()
