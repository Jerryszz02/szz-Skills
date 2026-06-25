#!/usr/bin/env python3
"""Score travel research evidence without performing network requests."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


SCORES = {"strong": 3, "positive": 1, "negative": -3, "neutral": 0}
VALID_TYPES = {"attraction", "restaurant"}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def independence_keys(item: dict[str, Any], index: int) -> set[str]:
    keys: set[str] = set()
    source = str(item.get("source", "unknown")).strip().lower()
    author = str(item.get("author", "")).strip().lower()
    if author:
        keys.add(f"author:{source}:{author}")
    fingerprint = item.get("content_fingerprint")
    if fingerprint:
        keys.add(f"fingerprint:{fingerprint.strip().lower()}")
    if not keys:
        keys.add(f"url:{item.get('url', index)}")
    return keys


def score_candidate(candidate: dict[str, Any], as_of: date) -> dict[str, Any]:
    kind = candidate.get("type")
    if kind not in VALID_TYPES:
        raise ValueError(f"candidate {candidate.get('name', '<unnamed>')} has invalid type: {kind!r}")

    cutoff = as_of - timedelta(days=365)
    kept: list[dict[str, Any]] = []
    seen_independence_keys: set[str] = set()
    excluded = {"marketing": 0, "stale": 0, "unknown_date": 0, "duplicate": 0}

    for index, evidence in enumerate(candidate.get("evidence", [])):
        if evidence.get("is_marketing"):
            excluded["marketing"] += 1
            continue
        published = parse_date(evidence.get("published_at"))
        if published is None:
            excluded["unknown_date"] += 1
            continue
        if published < cutoff or published > as_of:
            excluded["stale"] += 1
            continue
        stance = evidence.get("stance", "neutral")
        if stance not in SCORES:
            raise ValueError(f"invalid stance {stance!r} for {candidate.get('name', '<unnamed>')}")

        keys = independence_keys(evidence, index)
        if keys & seen_independence_keys:
            excluded["duplicate"] += 1
            continue
        seen_independence_keys.update(keys)
        kept.append(evidence)

    effective = kept
    score = sum(SCORES[item.get("stance", "neutral")] for item in effective)
    positive_sources = sum(SCORES[item.get("stance", "neutral")] > 0 for item in effective)
    negative_sources = sum(SCORES[item.get("stance", "neutral")] < 0 for item in effective)
    hard_risks = list(candidate.get("hard_risks", []))

    if hard_risks:
        tier = "excluded"
        reason = "严重风险：" + "、".join(hard_risks)
    elif kind == "attraction" and positive_sources >= 2 and score >= 3:
        tier = "priority"
        reason = "达到景点优先门槛"
    elif kind == "restaurant" and positive_sources >= 3 and score >= 5:
        tier = "priority"
        reason = "达到餐厅优先门槛"
    elif positive_sources >= 1 and score > 0:
        tier = "backup"
        reason = "有正向证据但未达到优先门槛"
    else:
        tier = "excluded"
        reason = "正向证据或净分不足"

    return {
        "name": candidate.get("name"),
        "type": kind,
        "tier": tier,
        "net_score": score,
        "positive_sources": positive_sources,
        "negative_sources": negative_sources,
        "hard_risks": hard_risks,
        "reason": reason,
        "effective_evidence": effective,
        "excluded_evidence": excluded,
    }


def read_json(path: str | None) -> dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score travel research candidates from JSON evidence.")
    parser.add_argument("--input", help="Input JSON path; defaults to stdin")
    parser.add_argument("--output", help="Output JSON path; defaults to stdout")
    parser.add_argument("--as-of", help="Research date in YYYY-MM-DD; defaults to today")
    args = parser.parse_args()

    as_of = parse_date(args.as_of) if args.as_of else date.today()
    if as_of is None:
        parser.error("--as-of must use YYYY-MM-DD")

    payload = read_json(args.input)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        parser.error("input must contain a candidates array")

    result = {
        "as_of": as_of.isoformat(),
        "candidates": [score_candidate(candidate, as_of) for candidate in candidates],
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
