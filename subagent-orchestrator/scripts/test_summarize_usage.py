#!/usr/bin/env python3
"""Focused tests for summarize_usage."""

import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("summarize_usage.py")


def write_receipt(path: Path, total: int = 10, available: bool = True,
                  status: str = "completed", model: object = "test-model",
                  worker: str = "manager") -> None:
    usage = {"available": available, "source": "test"}
    if available:
        usage.update(input_tokens=total - 2, output_tokens=2, total_tokens=total,
                     cached_input_tokens=1)
    path.write_text(json.dumps({"worker": worker, "status": status,
                                "actual_model": model, "usage": usage}), encoding="utf-8")


def manifest(runs: list[dict], **updates: object) -> dict:
    value = {"schema_version": 1, "task_id": "task", "variant": "orchestrated",
             "acceptance": "passed", "elapsed_seconds": 1.5, "runs": runs}
    value.update(updates)
    return value


def run_cli(root: Path, value: object, *extra: str) -> subprocess.CompletedProcess:
    run = root / "run.json"
    run.write_text(json.dumps(value), encoding="utf-8")
    return subprocess.run(("python3", str(SCRIPT), "--run", str(run), *extra), capture_output=True, text=True)


class SummarizeTests(unittest.TestCase):
    def test_routes_separate_preflight_from_unaccounted_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", 10)
            runs = [{"id": "main", "role": "manager", "slice_id": "main", "attempt": 1,
                     "receipt": "manager.json"}]
            route = {"schema_version": 1, "provider": "dsh", "reason_code": "cli_missing",
                     "execution_state": "not_started"}
            (root / "route.json").write_text(json.dumps(route))
            value = manifest(runs, routes=["route.json"])
            result = run_cli(root, value)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["worker_attempts"], 0)
            self.assertEqual(summary["retry_attempts"], 0)
            self.assertEqual(summary["total_tokens"], 10)
            self.assertEqual(summary["skipped_routes"][0]["reason_code"], "cli_missing")
            route.update(execution_state="unknown", reason_code="worker_failed")
            (root / "route.json").write_text(json.dumps(route))
            summary = json.loads(run_cli(root, value).stdout)
            self.assertFalse(summary["usage_complete"])
            self.assertIsNone(summary["total_tokens"])
            self.assertEqual(len(summary["unaccounted_routes"]), 1)

    def test_copied_native_receipts_cannot_overlap_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", 10)
            write_receipt(root / "worker.json", 20, worker="native")
            receipt = json.loads((root / "worker.json").read_text())
            receipt["evidence"] = {"thread_id": "child", "response_ids": ["response1"]}
            for name in ("worker.json", "copy.json"):
                (root / name).write_text(json.dumps(receipt))
            runs = [{"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"},
                    {"id": "worker", "role": "worker", "slice_id": "build", "attempt": 1, "receipt": "worker.json"},
                    {"id": "retry", "role": "worker", "slice_id": "build", "attempt": 2, "receipt": "copy.json"}]
            result = run_cli(root, manifest(runs))
            self.assertEqual(result.returncode, 2)
            self.assertIn("overlapping native response usage", result.stderr)

    def test_totals_cached_once_failed_attempt_and_relative_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", 10)
            write_receipt(root / "worker.json", 20, worker="luna")
            write_receipt(root / "failed.json", 5, status="failed", worker="luna")
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "manager.json"},
                    {"id": "worker", "role": "worker", "slice_id": "slice", "attempt": 1, "receipt": "worker.json"},
                    {"id": "failed", "role": "integrator", "slice_id": "slice", "attempt": 2, "receipt": "failed.json"}]
            output = root / "summary.json"
            result = run_cli(root, manifest(runs), "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(summary["manager_tokens"], 10)
            self.assertEqual(summary["worker_tokens"], 25)
            self.assertEqual(summary["total_tokens"], 35)
            self.assertEqual(summary["observed_tokens"], 35)
            self.assertEqual(summary["retry_attempts"], 1)
            self.assertEqual(summary["runs"][2]["receipt_status"], "failed")

    def test_missing_usage_and_zero_workers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", available=False)
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "manager.json"}]
            result = run_cli(root, manifest(runs, variant="baseline", acceptance="incomplete"))
            summary = json.loads(result.stdout)
            self.assertIsNone(summary["manager_tokens"])
            self.assertEqual(summary["worker_tokens"], 0)
            self.assertFalse(summary["usage_complete"])
            self.assertEqual(summary["missing_usage"], ["manager"])

    def test_missing_receipt_path_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "missing.json"}]
            result = run_cli(root, manifest(runs))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(json.loads(result.stdout)["manager_tokens"])

    def test_unavailable_usage_requires_source_explanation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path = root / "manager.json"
            write_receipt(receipt_path, available=False)
            value = json.loads(receipt_path.read_text(encoding="utf-8"))
            del value["usage"]["source"]
            receipt_path.write_text(json.dumps(value), encoding="utf-8")
            runs = [{"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"}]
            result = run_cli(root, manifest(runs))
            self.assertEqual(result.returncode, 2)
            self.assertIn("source", result.stderr)

    def test_missing_worker_keeps_known_manager_and_partial_subtotal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", 10)
            write_receipt(root / "worker.json", available=False, worker="luna")
            for reference in (None, "absent.json", "worker.json"):
                with self.subTest(reference=reference):
                    runs = [
                        {"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"},
                        {"id": "worker", "role": "worker", "slice_id": "build", "attempt": 1, "receipt": reference},
                    ]
                    result = run_cli(root, manifest(runs))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    summary = json.loads(result.stdout)
                    self.assertEqual(summary["manager_tokens"], 10)
                    self.assertEqual(summary["observed_tokens"], 10)
                    self.assertIsNone(summary["worker_tokens"])
                    self.assertIsNone(summary["total_tokens"])
                    self.assertEqual(summary["missing_usage"], ["worker"])

    def test_baseline_with_known_usage_and_unknown_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json", 10, model=None)
            runs = [{"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"}]
            result = run_cli(root, manifest(runs, variant="baseline"))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["total_tokens"], 10)
            self.assertTrue(summary["usage_complete"])
            self.assertEqual(summary["worker_attempts"], 0)
            self.assertIsNone(summary["runs"][0]["actual_model"])

    def test_rejects_alias_duplicate_and_duplicate_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "manager.json")
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "manager.json"},
                    {"id": "worker", "role": "worker", "slice_id": "slice", "attempt": 1, "receipt": "./manager.json"}]
            result = run_cli(root, manifest(runs))
            self.assertIn("duplicate resolved receipt path", result.stderr)
            runs[1]["receipt"] = None
            runs.append({"id": "retry", "role": "worker", "slice_id": "slice", "attempt": 1, "receipt": None})
            result = run_cli(root, manifest(runs))
            self.assertIn("duplicate role/slice_id/attempt", result.stderr)

    def test_rejects_receipt_role_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "worker.json", worker="luna")
            worker_runs = [{"id": "worker", "role": "worker", "slice_id": "build", "attempt": 1, "receipt": "worker.json"}]
            result = run_cli(root, manifest([{**worker_runs[0], "role": "manager", "slice_id": "root"}]))
            self.assertIn("manager receipt", result.stderr)
            write_receipt(root / "manager.json")
            (root / "manager-copy.json").write_text((root / "manager.json").read_text(encoding="utf-8"), encoding="utf-8")
            manager_runs = [{"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "manager.json"},
                            {"id": "worker", "role": "worker", "slice_id": "build", "attempt": 1, "receipt": "manager-copy.json"}]
            result = run_cli(root, manifest(manager_runs))
            self.assertIn("cannot reference a manager receipt", result.stderr)

    def test_rejects_receipt_without_worker_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_receipt(root / "receipt.json")
            value = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
            del value["worker"]
            (root / "receipt.json").write_text(json.dumps(value), encoding="utf-8")
            runs = [{"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": "receipt.json"}]
            result = run_cli(root, manifest(runs))
            self.assertIn("worker must be a nonempty string", result.stderr)

    def test_rejects_malformed_receipt_and_invalid_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "bad.json"
            bad.write_text("{broken", encoding="utf-8")
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "bad.json"}]
            result = run_cli(root, manifest(runs))
            self.assertIn("malformed JSON", result.stderr)
            write_receipt(root / "bad.json")
            cases = [(True, "schema_version"), (1.0, "schema_version"), ({}, "variant"), ([], "acceptance"), (-1, "elapsed_seconds"), (True, "elapsed_seconds"), (math.inf, "elapsed_seconds")]
            for value, field in cases:
                result = run_cli(root, manifest(runs, **{field: value}))
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)

    def test_rejects_bad_receipt_totals_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt_path = root / "receipt.json"
            write_receipt(receipt_path)
            runs = [{"id": "manager", "role": "manager", "slice_id": "main", "attempt": 1, "receipt": "receipt.json"}]
            cases = [("negative", {"input_tokens": -1}), ("bool", {"output_tokens": True}), ("nonfinite", {"total_tokens": math.nan}), ("contradictory", {"total_tokens": 99}), ("no source", {"source": ""})]
            for label, change in cases:
                write_receipt(receipt_path)
                value = json.loads(receipt_path.read_text(encoding="utf-8"))
                value["usage"].update(change)
                receipt_path.write_text(json.dumps(value, allow_nan=True), encoding="utf-8")
                result = run_cli(root, manifest(runs))
                self.assertNotEqual(result.returncode, 0, label)
                self.assertNotIn("Traceback", result.stderr)
            write_receipt(receipt_path, model={})
            result = run_cli(root, manifest(runs))
            self.assertIn("actual_model", result.stderr)

    def test_invalid_entries_and_manager_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            main = {"id": "main", "role": "manager", "slice_id": "root", "attempt": 1, "receipt": None}
            for change in ({"role": {}}, {"attempt": True}, {"attempt": 0}, {"attempt": 2}, {"receipt": 7}):
                with self.subTest(change=change):
                    result = run_cli(root, manifest([{**main, **change}]))
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn("Traceback", result.stderr)
            for runs in ([{**main, "role": "worker"}], [main, {**main, "id": "second", "slice_id": "second"}]):
                result = run_cli(root, manifest(runs))
                self.assertEqual(result.returncode, 2)
                self.assertIn("exactly one manager", result.stderr)


if __name__ == "__main__":
    unittest.main()
