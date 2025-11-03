"""Tests for digest aggregation helpers."""

import json

from src.cli import digests


def test_collect_highlights_deduplicates_and_limits():
    """Aggregated highlights should dedupe topics and respect the limit."""

    summary_one = json.dumps(
        {
            "key_topics": [
                {"topic": "AI", "summary": "Discussion about AI."},
                {"topic": "Startups", "summary": "Founder lessons."},
            ],
            "takeaways": [
                {"text": "Try the new tool."},
                {"text": "Share episode."},
            ],
        }
    )
    summary_two = json.dumps(
        {
            "key_topics": [
                {"topic": "AI", "summary": "Duplicate topic."},
                {"topic": "Robotics", "summary": "Robotics update."},
            ],
            "takeaways": [
                {"text": "Try the new tool."},
                {"text": "Invest in robotics."},
            ],
        }
    )

    themes, actionables = digests._collect_highlights([summary_one, summary_two], limit=2)

    assert [theme["title"] for theme in themes] == ["AI", "Startups"]
    assert actionables == ["Try the new tool.", "Share episode."]


def test_extract_highlights_handles_malformed(caplog):
    """Malformed JSON payloads should return empty results and log a warning."""

    with caplog.at_level("WARNING"):
        topics, actionables = digests._extract_highlights("{bad json}")

    assert topics == []
    assert actionables == []
    assert any("Skipping malformed structured summary" in rec.message for rec in caplog.records)
