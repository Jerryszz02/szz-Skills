#!/usr/bin/env python3
"""Focused tests for the native rollout receipt collector."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).with_name("collect_native_receipt.py")
THREAD = "thread-main"
OTHER = "thread-other"


def record_lines(rows: list[Any]) -> str:
    """Serialize rollout rows; str entries are written verbatim (e.g. broken JSON)."""
    parts: list[str] = []
    for row in rows:
        parts.append(row if isinstance(row, str) else json.dumps(row, separators=(",", ":")))
    return "\n".join(parts) + "\n"


def meta(thread_id: str = THREAD) -> dict[str, Any]:
    return {"type": "session_meta", "payload": {"id": thread_id}}


def context(thread: str, turn: str, model: str, *, include_thread: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {"turn_id": turn, "model": model}
    if include_thread:
        payload["thread_id"] = thread
    return {"type": "turn_context", "payload": payload}


def usage(
    thread: str,
    turn: str,
    response: str,
    *,
    input_: int,
    output: int,
    total: int,
    cached: int | None = None,
    write: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inner: dict[str, Any] = {
        "input_tokens": input_,
        "output_tokens": output,
        "total_tokens": total,
    }
    if cached is not None:
        inner["cached_input_tokens"] = cached
    if write is not None:
        inner["cache_write_input_tokens"] = write
    payload: dict[str, Any] = {
        "thread_id": thread,
        "turn_id": turn,
        "response_id": response,
        "usage": inner,
    }
    if extra:
        payload.update(extra)
    return {"type": "token_usage_record", "payload": payload}


def packet(root: Path) -> Path:
    path = root / "task.md"
    path.write_text("# Task Packet\n\n## Objective\n\nCollect the rollout receipt.\n", encoding="utf-8")
    return path


def collect(
    root: Path,
    rows: list[Any],
    turns: list[str],
    *,
    thread: str = THREAD,
    rollout_name: str = "rollout.jsonl",
    worker: str = "native",
    status: str = "completed",
    requested: str | None = None,
    reasoning: str | None = None,
    fork: str | None = None,
    raw_lines: bool = True,
) -> tuple[subprocess.CompletedProcess, dict[str, Any]]:
    rollout = root / rollout_name
    if raw_lines:
        rollout.write_text(record_lines(rows), encoding="utf-8")
    else:
        rollout.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return run_cli(root, rollout, turns, thread=thread, worker=worker, status=status,
                   requested=requested, reasoning=reasoning, fork=fork)


def run_cli(
    root: Path,
    rollout: Path,
    turns: list[str],
    *,
    thread: str = THREAD,
    worker: str = "native",
    status: str = "completed",
    requested: str | None = None,
    reasoning: str | None = None,
    fork: str | None = None,
) -> tuple[subprocess.CompletedProcess, dict[str, Any]]:
    task = packet(root)
    output = root / "receipt.json"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--rollout", str(rollout),
        "--thread-id", thread,
        "--task-file", str(task),
        "--output", str(output),
        "--worker", worker,
        "--status", status,
    ]
    for turn in turns:
        cmd += ["--turn-id", turn]
    if requested is not None:
        cmd += ["--requested-model", requested]
    if reasoning is not None:
        cmd += ["--reasoning-effort", reasoning]
    if fork is not None:
        cmd += ["--fork-turns", fork]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    value = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
    return proc, value


class CollectNativeReceiptTests(unittest.TestCase):
    def test_thread_and_turn_filtering(self) -> None:
        rows = [
            meta(),
            context(THREAD, "t1", "gpt-observed-a"),
            context(THREAD, "t2", "gpt-observed-b"),
            context(OTHER, "t1", "gpt-other-thread"),
            context(THREAD, "t3", "gpt-unselected-turn"),
            usage(THREAD, "t1", "resp_a", input_=100, output=20, total=120, cached=40, write=0),
            usage(THREAD, "t2", "resp_b", input_=50, output=30, total=80, cached=10, write=0),
            usage(OTHER, "t1", "resp_other", input_=999, output=1, total=1000),
            usage(THREAD, "t3", "resp_unselected", input_=700, output=7, total=707),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1", "t2"], requested="gpt-requested")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertTrue(usage_value["available"])
            self.assertEqual(usage_value["input_tokens"], 150)
            self.assertEqual(usage_value["output_tokens"], 50)
            self.assertEqual(usage_value["total_tokens"], 200)
            self.assertEqual(usage_value["cached_input_tokens"], 50)
            self.assertEqual(usage_value["cache_write_input_tokens"], 0)
            self.assertEqual(usage_value["uncached_input_tokens"], 100)
            self.assertEqual(value["requested_model"], "gpt-requested")
            self.assertEqual(value["actual_model"], "gpt-observed-b")
            self.assertEqual(value["actual_models"], ["gpt-observed-a", "gpt-observed-b"])
            evidence = value["evidence"]
            self.assertEqual(evidence["thread_id"], THREAD)
            self.assertEqual(evidence["turn_ids"], ["t1", "t2"])
            self.assertEqual(evidence["response_ids"], ["resp_a", "resp_b"])
            self.assertEqual(evidence["relevant_first_line"], 6)
            self.assertEqual(evidence["relevant_last_line"], 7)
            self.assertEqual(evidence["relevant_records"], 2)
            self.assertTrue(evidence["rollout_file"].endswith("rollout.jsonl"))
            self.assertEqual(evidence["rollout_file"], str((root / "rollout.jsonl").resolve()))

    def test_response_dedupe(self) -> None:
        rows = [
            meta(),
            context(THREAD, "t1", "gpt-a"),
            usage(THREAD, "t1", "resp_a", input_=100, output=20, total=120, cached=40, write=0),
            usage(THREAD, "t1", "resp_a", input_=100, output=20, total=120, cached=40, write=0),
            usage(THREAD, "t1", "resp_b", input_=25, output=5, total=30, cached=0, write=0),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["usage"]["input_tokens"], 125)
            self.assertEqual(value["usage"]["output_tokens"], 25)
            self.assertEqual(value["usage"]["total_tokens"], 150)
            self.assertEqual(value["evidence"]["response_ids"], ["resp_a", "resp_b"])
            self.assertEqual(value["evidence"]["relevant_records"], 3)

    def test_conflicting_duplicate_is_unavailable(self) -> None:
        rows = [
            meta(),
            context(THREAD, "t1", "gpt-a"),
            usage(THREAD, "t1", "resp_a", input_=100, output=20, total=120, cached=40, write=0),
            usage(THREAD, "t1", "resp_a", input_=90, output=20, total=110, cached=40, write=0),
            usage(THREAD, "t1", "resp_b", input_=5, output=1, total=6),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertFalse(usage_value["available"])
            self.assertIsNone(usage_value["input_tokens"])
            self.assertIsNone(usage_value["output_tokens"])
            self.assertIsNone(usage_value["total_tokens"])
            self.assertTrue(usage_value["source"])
            self.assertIn("conflicting duplicate response_id", usage_value["source"])
            self.assertEqual(value["evidence"]["response_ids"], ["resp_a", "resp_b"])

    def test_malformed_usage_variants(self) -> None:
        cases = [
            ("negative input", usage(THREAD, "t1", "r1", input_=-1, output=1, total=0), "nonnegative"),
            ("bool output", usage(THREAD, "t1", "r1", input_=1, output=True, total=1), "nonnegative"),
            ("bool total", usage(THREAD, "t1", "r1", input_=1, output=1, total=False), "nonnegative"),
            ("inconsistent total", usage(THREAD, "t1", "r1", input_=10, output=2, total=99), "must equal"),
            ("missing usage object", {**usage(THREAD, "t1", "r1", input_=1, output=1, total=2), "payload": {"thread_id": THREAD, "turn_id": "t1", "response_id": "r1"}}, "usage payload"),
            ("cache exceeds input", usage(THREAD, "t1", "r1", input_=10, output=2, total=12, cached=11), "cannot exceed"),
        ]
        for label, row, expected in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    proc, value = collect(root, [meta(), row], ["t1"])
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertFalse(value["usage"]["available"], label)
                    self.assertIsNone(value["usage"]["total_tokens"])
                    self.assertIn(expected, value["usage"]["source"], label)

    def test_one_bad_relevant_usage_poisons_valid_totals(self) -> None:
        rows = [
            meta(),
            usage(THREAD, "t1", "r_good", input_=10, output=2, total=12),
            usage(THREAD, "t1", "r_bad", input_=-4, output=2, total=-2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIsNone(value["usage"]["input_tokens"])
            self.assertIn("line 3", value["usage"]["source"])

    def test_missing_vs_zero_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [meta(), context(THREAD, "t1", "gpt-a")]
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertFalse(usage_value["available"])
            self.assertIsNone(usage_value["input_tokens"])
            self.assertIsNone(usage_value["output_tokens"])
            self.assertIsNone(usage_value["total_tokens"])
            self.assertIn("no token usage records", usage_value["source"])
            self.assertEqual(value["actual_model"], "gpt-a")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [meta(), usage(THREAD, "t1", "r_zero", input_=0, output=0, total=0, cached=0, write=0)]
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertTrue(usage_value["available"])
            self.assertEqual(usage_value["input_tokens"], 0)
            self.assertEqual(usage_value["output_tokens"], 0)
            self.assertEqual(usage_value["total_tokens"], 0)
            self.assertEqual(usage_value["cached_input_tokens"], 0)
            self.assertEqual(value["evidence"]["relevant_records"], 1)

    def test_cache_components_are_not_double_counted(self) -> None:
        rows = [
            meta(),
            usage(THREAD, "t1", "r1", input_=100, output=20, total=120, cached=40, write=0),
            usage(THREAD, "t1", "r2", input_=100, output=10, total=110, cached=30, write=5),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertEqual(usage_value["input_tokens"], 200)
            self.assertEqual(usage_value["output_tokens"], 30)
            self.assertEqual(usage_value["total_tokens"], 230)
            self.assertEqual(usage_value["cached_input_tokens"], 70)
            self.assertEqual(usage_value["cache_write_input_tokens"], 5)
            self.assertEqual(usage_value["uncached_input_tokens"], 125)
            self.assertEqual(
                usage_value["uncached_input_tokens"]
                + usage_value["cached_input_tokens"]
                + usage_value["cache_write_input_tokens"],
                usage_value["input_tokens"],
            )

    def test_missing_optional_cache_fields_are_null(self) -> None:
        rows = [
            meta(),
            usage(THREAD, "t1", "r1", input_=10, output=2, total=12),
            usage(THREAD, "t1", "r2", input_=20, output=3, total=23),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            usage_value = value["usage"]
            self.assertTrue(usage_value["available"])
            self.assertEqual(usage_value["input_tokens"], 30)
            self.assertEqual(usage_value["total_tokens"], 35)
            self.assertIsNone(usage_value["cached_input_tokens"])
            self.assertIsNone(usage_value["cache_write_input_tokens"])
            self.assertIsNone(usage_value["uncached_input_tokens"])

    def test_requested_model_is_never_copied_to_actual(self) -> None:
        rows = [meta(), context(THREAD, "t1", "gpt-observed"), usage(THREAD, "t1", "r1", input_=1, output=1, total=2)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"], requested="gpt-requested-alias")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["requested_model"], "gpt-requested-alias")
            self.assertEqual(value["actual_model"], "gpt-observed")
        rows = [meta(), usage(THREAD, "t1", "r1", input_=1, output=1, total=2)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"], requested="gpt-requested-alias")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsNone(value["actual_model"])
            self.assertEqual(value["actual_models"], [])
            self.assertEqual(value["requested_model"], "gpt-requested-alias")

    def test_manager_worker_and_defaults(self) -> None:
        rows = [meta(), context(THREAD, "t1", "gpt-a"), usage(THREAD, "t1", "r1", input_=4, output=1, total=5)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"], worker="manager", status="completed")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["worker"], "manager")
            self.assertEqual(value["status"], "completed")
            self.assertEqual(value["schema_version"], 1)
            self.assertEqual(value["fork_turns"], "none")
            self.assertIsNone(value["requested_model"])
            self.assertIsNone(value["reasoning_effort"])
            self.assertEqual(value["context_scope"], "native rollout thread/turn slice")
            self.assertEqual(value["task"]["objective"], "Collect the rollout receipt.")
            self.assertTrue(value["task"]["task_packet_sha256"])

    def test_explicit_reasoning_and_fork(self) -> None:
        rows = [meta(), usage(THREAD, "t1", "r1", input_=1, output=1, total=2)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"], reasoning="medium", fork="3-5")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["reasoning_effort"], "medium")
            self.assertEqual(value["fork_turns"], "3-5")

    def test_unreadable_rollout_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "does-not-exist.jsonl"
            proc, value = run_cli(root, rollout, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIsNone(value["usage"]["input_tokens"])
            self.assertIsNone(value["usage"]["total_tokens"])
            self.assertIn("unreadable", value["usage"]["source"])
            self.assertIsNone(value["actual_model"])
            self.assertEqual(value["evidence"]["rollout_file"], str(rollout.resolve()))

    def test_undecodable_rollout_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "rollout.jsonl"
            rollout.write_bytes(
                b'{"type":"session_meta","payload":{"id":"thread-main"}}\n'
                b'{"type":"token_usage_record","payload":{"thread_id":"thread-main",'
                b'"turn_id":"t1","response_id":"r1","usage":'
                b'{"input_tokens":1,"output_tokens":1,"total_tokens":2}}}\n'
                b"\xff\xfe broken utf-8\n"
            )
            proc, value = run_cli(root, rollout, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIn("unreadable", value["usage"]["source"])

    def test_invalid_json_makes_usage_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "rollout.jsonl"
            rollout.write_text(
                record_lines([
                    meta(),
                    usage(THREAD, "t1", "r1", input_=1, output=1, total=2),
                ]) + '{"type":"token_usage_record","payload": broken\n',
                encoding="utf-8",
            )
            proc, value = run_cli(root, rollout, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIn("invalid rollout JSON at line 3", value["usage"]["source"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "rollout.jsonl"
            rollout.write_text(record_lines([meta(), "[1,2,3]", usage(THREAD, "t1", "r1", input_=1, output=1, total=2)]), encoding="utf-8")
            proc, value = run_cli(root, rollout, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIn("invalid rollout JSON at line 2", value["usage"]["source"])

    def test_threadless_turn_context_needs_session_meta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                meta(THREAD),
                context(THREAD, "t1", "gpt-establ", include_thread=False),
                usage(THREAD, "t1", "r1", input_=1, output=1, total=2),
            ]
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["actual_model"], "gpt-establ")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                context(THREAD, "t1", "gpt-no-meta", include_thread=False),
                usage(THREAD, "t1", "r1", input_=1, output=1, total=2),
            ]
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsNone(value["actual_model"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                meta(OTHER),
                context(THREAD, "t1", "gpt-wrong-file", include_thread=False),
                usage(THREAD, "t1", "r1", input_=1, output=1, total=2),
            ]
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIsNone(value["actual_model"])

    def test_aggregate_and_event_msg_tokens_are_not_summed(self) -> None:
        rows = [
            meta(),
            context(THREAD, "t1", "gpt-a"),
            usage(
                THREAD, "t1", "resp_a", input_=100, output=20, total=120, cached=40, write=0,
                extra={
                    "turn_token_usage": {"input_tokens": 9000, "output_tokens": 900, "total_tokens": 9900},
                    "thread_token_usage": {"input_tokens": 8000, "output_tokens": 800, "total_tokens": 8800},
                },
            ),
            {
                "type": "event_msg",
                "payload": {
                    "token_count": {
                        "info": {
                            "last_token_usage": {"input_tokens": 5000, "output_tokens": 500, "total_tokens": 5500},
                            "total_token_usage": {"input_tokens": 7000, "output_tokens": 700, "total_tokens": 7700},
                        }
                    }
                },
            },
            {"type": "response_item", "payload": {"message": {"content": "do not copy this into the receipt"}}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["t1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(value["usage"]["input_tokens"], 100)
            self.assertEqual(value["usage"]["output_tokens"], 20)
            self.assertEqual(value["usage"]["total_tokens"], 120)
            serialized = json.dumps(value)
            self.assertNotIn("do not copy this into the receipt", serialized)
            self.assertNotIn("9000", serialized)

    def test_missing_turn_id_is_an_argument_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = packet(root)
            rollout = root / "rollout.jsonl"
            rollout.write_text(record_lines([meta()]), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--rollout", str(rollout),
                    "--thread-id", THREAD,
                    "--task-file", str(task),
                    "--output", str(root / "receipt.json"),
                    "--worker", "native",
                    "--status", "completed",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--turn-id", proc.stderr)

    def test_int_turn_id_does_not_match_string(self) -> None:
        rows = [
            meta(),
            context(THREAD, 1, "gpt-a"),
            usage(THREAD, 1, "r1", input_=7, output=3, total=10),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, value = collect(root, rows, ["1"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])
            self.assertIsNone(value["actual_model"])

    def test_response_cannot_belong_to_two_turns(self) -> None:
        rows = [meta(), usage(THREAD, "a", "r1", input_=7, output=3, total=10),
                usage(THREAD, "b", "r1", input_=7, output=3, total=10)]
        with tempfile.TemporaryDirectory() as directory:
            proc, value = collect(Path(directory), rows, ["a", "b"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(value["usage"]["available"])


if __name__ == "__main__":
    unittest.main()
