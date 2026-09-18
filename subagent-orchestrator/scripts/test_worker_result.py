#!/usr/bin/env python3
"""Focused tests for the deterministic worker-result normalizer."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
HELPER = SCRIPT_DIR / "worker_result.py"


def report_json(**overrides: object) -> dict:
    value = {
        "schema_version": 1,
        "status": "completed",
        "summary": "did the work",
        "checks": [
            {"command": "test -f generated.txt", "cwd": "/tmp/work", "exit_code": 0, "result": "present"}
        ],
        "unresolved": [],
        "evidence": ["generated.txt"],
        "changed_paths": ["generated.txt"],
    }
    value.update(overrides)
    return value


class WorkerResultTests(unittest.TestCase):
    def run_helper(self, report=None, changed_paths=None, raw=None):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        report_path = root / "final.txt"
        if raw is not None:
            report_path.write_text(raw, encoding="utf-8")
        elif report is not None:
            report_path.write_text(json.dumps(report), encoding="utf-8")
        args = [
            "python3",
            str(HELPER),
            "--report",
            str(report_path),
            "--output",
            str(root / "worker-result.json"),
        ]
        if changed_paths is not None:
            paths_file = root / "changed-paths.txt"
            paths_file.write_text("".join(f"{path}\n" for path in changed_paths), encoding="utf-8")
            args += ["--changed-paths", str(paths_file)]
        result = subprocess.run(args, text=True, capture_output=True, check=False)
        output = root / "worker-result.json"
        value = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
        return result, value, root

    def test_whole_json_document_is_accepted(self) -> None:
        result, value, _ = self.run_helper(report_json())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(value["status"], "completed")
        self.assertEqual(value["status_source"], "worker-report")
        self.assertEqual(value["report"]["parse"], "json-document")
        self.assertEqual(value["changed_paths"]["source"], "unavailable")
        self.assertEqual(value["reported_changed_paths"], {"source": "worker-reported", "paths": ["generated.txt"]})
        self.assertTrue(Path(value["report"]["reference"]).is_file())

    def test_fenced_json_block_is_accepted(self) -> None:
        raw = "```json\n" + json.dumps(report_json()) + "\n```\n"
        result, value, _ = self.run_helper(raw=raw, changed_paths=["git-observed.txt"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(value["report"]["parse"], "fenced-json")
        self.assertEqual(value["changed_paths"]["source"], "git-observed")
        self.assertEqual(value["changed_paths"]["paths"], ["git-observed.txt"])
        self.assertEqual(value["reported_changed_paths"]["paths"], ["generated.txt"])

    def test_prose_around_fence_is_unverified(self) -> None:
        raw = "Additional unresolved concern.\n```json\n" + json.dumps(report_json()) + "\n```\n"
        result, value, _ = self.run_helper(raw=raw)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertEqual(Path(value["report"]["reference"]).read_text(), raw)

    def test_oversized_raw_report_is_unverified_even_with_valid_fields(self) -> None:
        report = report_json(extra_log="x" * 140000)
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertIn(report["extra_log"], Path(value["report"]["reference"]).read_text())

    def test_empty_check_result_is_unverified(self) -> None:
        report = report_json(checks=[{"command": "true", "cwd": "/tmp", "exit_code": 0, "result": ""}])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")

    def test_noninteger_schema_version_is_unverified(self) -> None:
        result, value, _ = self.run_helper(report_json(schema_version=1.0))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")

    def test_normalized_result_is_bounded_with_large_observed_paths(self) -> None:
        paths = [str(i) + "/" + "x" * 1000 for i in range(200)]
        result, value, root = self.run_helper(report_json(), changed_paths=paths)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertLessEqual((root / "worker-result.json").stat().st_size, 32768)
        self.assertEqual(Path(value["changed_paths"]["reference"]).read_text().splitlines(), paths)

    def test_missing_report_is_unverified(self) -> None:
        result, value, _ = self.run_helper(changed_paths=["generated.txt"])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertEqual(value["status_source"], "report-validation")
        self.assertEqual(value["report"]["parse"], "missing")
        self.assertTrue(any("not found" in issue for issue in value["issues"]))

    def test_prose_without_json_is_unverified(self) -> None:
        result, value, _ = self.run_helper(raw="Everything passed. Tests are green.\n")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertEqual(value["report"]["parse"], "missing")

    def test_multiple_fenced_blocks_are_ambiguous(self) -> None:
        raw = "```json\n{}\n```\n\nmore\n\n```json\n{}\n```\n"
        result, value, _ = self.run_helper(raw=raw)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertEqual(value["report"]["parse"], "ambiguous")

    def test_malformed_json_is_unverified(self) -> None:
        result, value, _ = self.run_helper(raw="```json\n{not valid json\n```\n")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertEqual(value["report"]["parse"], "malformed")

    def test_missing_fields_are_unverified(self) -> None:
        result, value, _ = self.run_helper(report_json(summary=""))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("summary" in issue for issue in value["issues"]))

    def test_completed_without_checks_is_unverified(self) -> None:
        result, value, _ = self.run_helper(report_json(checks=[]))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("no executed checks" in issue for issue in value["issues"]))

    def test_false_completed_claim_with_failed_check_is_unverified(self) -> None:
        report = report_json(checks=[{"command": "false", "cwd": "/tmp", "exit_code": 1, "result": "failed"}])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("nonzero or null" in issue for issue in value["issues"]))

    def test_completed_with_null_exit_code_is_unverified(self) -> None:
        report = report_json(checks=[{"command": "maybe", "cwd": "/tmp", "exit_code": None, "result": ""}])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")

    def test_completed_with_unresolved_criteria_is_unverified(self) -> None:
        result, value, _ = self.run_helper(report_json(unresolved=["follow-up review"]))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("unresolved" in issue for issue in value["issues"]))

    def test_relative_cwd_is_unverified(self) -> None:
        report = report_json(checks=[{"command": "cmd", "cwd": "relative/path", "exit_code": 0, "result": "ok"}])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("absolute path" in issue for issue in value["issues"]))

    def test_partial_report_is_preserved_but_not_success(self) -> None:
        report = report_json(
            status="partial",
            checks=[{"command": "test -f generated.txt", "cwd": "/tmp", "exit_code": 1, "result": "missing"}],
            unresolved=["finish the fixture"],
        )
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(value["status"], "partial")
        self.assertEqual(value["unresolved"], ["finish the fixture"])
        self.assertEqual(value["issues"], [])

    def test_blocked_report_is_valid_but_not_success(self) -> None:
        report = report_json(status="blocked", checks=[], unresolved=["dependency unavailable"])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(value["status"], "blocked")
        self.assertEqual(value["unresolved"], ["dependency unavailable"])
        self.assertEqual(value["issues"], [])

    def test_overlong_result_is_unverified_and_raw_is_preserved(self) -> None:
        long_result = "x" * 4000
        report = report_json(checks=[{"command": "cmd", "cwd": "/tmp", "exit_code": 0, "result": long_result}])
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(value["status"], "unverified")
        self.assertTrue(any("result" in issue and "exceeds" in issue for issue in value["issues"]))
        self.assertLess(len(value["checks"][0]["result"]), len(long_result))
        raw_reference = Path(value["report"]["reference"])
        self.assertIn(long_result, raw_reference.read_text(encoding="utf-8"))

    def test_observed_paths_are_kept_separate_from_reported(self) -> None:
        report = report_json(changed_paths=["worker/claim.py"])
        result, value, _ = self.run_helper(report, changed_paths=["git/observed.py", "git/observed.py"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(value["changed_paths"]["source"], "git-observed")
        self.assertEqual(value["changed_paths"]["paths"], ["git/observed.py"])
        self.assertEqual(
            value["reported_changed_paths"],
            {"source": "worker-reported", "paths": ["worker/claim.py"]},
        )

    def test_absent_reported_paths_are_labeled_not_reported(self) -> None:
        report = report_json()
        del report["changed_paths"]
        result, value, _ = self.run_helper(report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(value["reported_changed_paths"], {"source": "not-reported", "paths": []})


if __name__ == "__main__":
    unittest.main()
