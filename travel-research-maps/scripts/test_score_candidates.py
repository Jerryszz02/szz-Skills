#!/usr/bin/env python3
"""Regression tests for score_candidates.py."""

import unittest
from datetime import date

from score_candidates import score_candidate


AS_OF = date(2026, 6, 24)


def evidence(author, stance, source="xiaohongshu", **extra):
    return {
        "source": source,
        "url": f"https://example.test/{source}/{author}/{stance}",
        "author": author,
        "published_at": "2026-05-01",
        "stance": stance,
        **extra,
    }


class ScoreCandidateTests(unittest.TestCase):
    def test_attraction_needs_two_independent_positive_sources(self):
        candidate = {
            "name": "测试景点",
            "type": "attraction",
            "evidence": [evidence("a", "strong"), evidence("b", "positive")],
        }
        result = score_candidate(candidate, AS_OF)
        self.assertEqual(result["tier"], "priority")
        self.assertEqual(result["net_score"], 4)
        self.assertEqual(result["positive_sources"], 2)

    def test_restaurant_threshold_and_negative_score(self):
        candidate = {
            "name": "测试餐厅",
            "type": "restaurant",
            "evidence": [
                evidence("a", "strong"),
                evidence("b", "strong"),
                evidence("c", "negative"),
            ],
        }
        result = score_candidate(candidate, AS_OF)
        self.assertEqual(result["tier"], "backup")
        self.assertEqual(result["net_score"], 3)
        self.assertEqual(result["positive_sources"], 2)

    def test_marketing_duplicates_and_stale_posts_do_not_count(self):
        candidate = {
            "name": "过滤测试",
            "type": "attraction",
            "evidence": [
                evidence("a", "strong"),
                evidence("a", "strong", url="https://example.test/repost"),
                evidence("ad", "strong", is_marketing=True),
                evidence("old", "strong", published_at="2024-01-01"),
            ],
        }
        result = score_candidate(candidate, AS_OF)
        self.assertEqual(result["tier"], "backup")
        self.assertEqual(result["positive_sources"], 1)
        self.assertEqual(result["excluded_evidence"], {"marketing": 1, "stale": 1, "unknown_date": 0, "duplicate": 1})

    def test_author_and_content_fingerprint_both_deduplicate(self):
        candidate = {
            "name": "去重测试",
            "type": "attraction",
            "evidence": [
                evidence("same-author", "positive", content_fingerprint="original"),
                evidence("same-author", "strong", content_fingerprint="follow-up"),
                evidence("reposter", "strong", content_fingerprint="original"),
                evidence("independent", "strong", content_fingerprint="independent"),
            ],
        }
        result = score_candidate(candidate, AS_OF)
        self.assertEqual(result["positive_sources"], 2)
        self.assertEqual(result["excluded_evidence"]["duplicate"], 2)

    def test_hard_risk_overrides_score(self):
        candidate = {
            "name": "关闭餐厅",
            "type": "restaurant",
            "hard_risks": ["Google Maps 显示永久关闭"],
            "evidence": [evidence("a", "strong"), evidence("b", "strong"), evidence("c", "strong")],
        }
        result = score_candidate(candidate, AS_OF)
        self.assertEqual(result["tier"], "excluded")
        self.assertIn("严重风险", result["reason"])

    def test_cross_platform_positive_sources_can_reach_priority(self):
        candidate = {
            "name": "跨平台景点",
            "type": "attraction",
            "evidence": [
                evidence("a", "strong", source="xiaohongshu"),
                evidence("b", "positive", source="bilibili"),
            ],
        }
        result = score_candidate(candidate, AS_OF, min_positive_platforms_for_priority=2)
        self.assertEqual(result["tier"], "priority")
        self.assertEqual(result["positive_platforms"], ["bilibili", "xiaohongshu"])

    def test_single_platform_high_score_is_downgraded_when_two_platforms_required(self):
        candidate = {
            "name": "单平台高分餐厅",
            "type": "restaurant",
            "evidence": [
                evidence("a", "strong", source="xiaohongshu"),
                evidence("b", "strong", source="xiaohongshu"),
                evidence("c", "strong", source="xiaohongshu"),
            ],
        }
        result = score_candidate(candidate, AS_OF, min_positive_platforms_for_priority=2)
        self.assertEqual(result["tier"], "backup")
        self.assertEqual(result["positive_platforms"], ["xiaohongshu"])
        self.assertIn("正向平台少于 2 个", result["reason"])

    def test_same_content_fingerprint_deduplicates_across_platforms(self):
        candidate = {
            "name": "跨平台转载",
            "type": "attraction",
            "evidence": [
                evidence("a", "strong", source="xiaohongshu", content_fingerprint="same-video"),
                evidence("b", "strong", source="bilibili", content_fingerprint="same-video"),
                evidence("c", "positive", source="youtube", content_fingerprint="original"),
            ],
        }
        result = score_candidate(candidate, AS_OF, min_positive_platforms_for_priority=2)
        self.assertEqual(result["positive_sources"], 2)
        self.assertEqual(result["excluded_evidence"]["duplicate"], 1)
        self.assertEqual(result["positive_platforms"], ["xiaohongshu", "youtube"])


if __name__ == "__main__":
    unittest.main()
