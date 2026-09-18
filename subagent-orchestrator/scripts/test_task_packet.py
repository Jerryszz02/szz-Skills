#!/usr/bin/env python3
"""Focused tests for task-packet validation and path scope."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from task_packet import PacketError, load_packet, scope_errors


def write_packet(path: Path, allowed: str = "generated.txt") -> None:
    path.write_text(
        f"""# Task Packet

## Objective

Create the requested fixture.

## Dependencies

none

## Allowed paths

- {allowed}

## Forbidden paths

- .git/**

## Acceptance criteria

- The fixture exists.

## Required verification

- test -f {allowed.rstrip('/**')}

## Explicit non-goals

- Do not edit other files.

## Nested delegation

forbidden

## HEAD-only dependency

yes
""",
        encoding="utf-8",
    )


class TaskPacketTests(unittest.TestCase):
    def test_valid_packet_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "task.md"
            write_packet(packet, "src/**")
            allowed, forbidden = load_packet(packet)
            self.assertEqual(allowed, ["src/**"])
            self.assertEqual(scope_errors(["src/example.py"], allowed, forbidden), [])
            self.assertEqual(scope_errors(["README.md"], allowed, forbidden), ["path outside allowed scope: README.md"])

    def test_single_star_does_not_cross_path_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "task.md"
            write_packet(packet, "src/*.py")
            allowed, forbidden = load_packet(packet)
            self.assertEqual(scope_errors(["src/example.py"], allowed, forbidden), [])
            self.assertEqual(
                scope_errors(["src/internal/config.py"], allowed, forbidden),
                ["path outside allowed scope: src/internal/config.py"],
            )

    def test_unbounded_allowed_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "task.md"
            write_packet(packet, "**")
            with self.assertRaises(PacketError):
                load_packet(packet)

    def test_nested_delegation_must_be_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "task.md"
            write_packet(packet)
            packet.write_text(
                packet.read_text(encoding="utf-8").replace(
                    "## Nested delegation\n\nforbidden",
                    "## Nested delegation\n\nallowed",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PacketError, "Nested delegation must be forbidden"):
                load_packet(packet)


if __name__ == "__main__":
    unittest.main()
