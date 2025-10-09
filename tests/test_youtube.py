"""Tests for YouTube timestamp link generation."""

import pytest
from src.utils.youtube import (
    extract_youtube_id,
    is_youtube_url,
    timestamp_to_seconds,
    format_youtube_timestamp_link,
    format_timestamp_link,
)


def test_extract_youtube_id():
    """Test YouTube ID extraction."""
    assert extract_youtube_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_id("https://example.com") is None


def test_is_youtube_url():
    """Test YouTube URL detection."""
    assert is_youtube_url("https://youtube.com/watch?v=abc")
    assert is_youtube_url("https://youtu.be/abc")
    assert not is_youtube_url("https://example.com")


def test_timestamp_to_seconds():
    """Test timestamp conversion."""
    assert timestamp_to_seconds("01:30") == 90
    assert timestamp_to_seconds("1:05:30") == 3930
    assert timestamp_to_seconds("00:45") == 45


def test_format_youtube_timestamp_link():
    """Test YouTube timestamp link formatting."""
    url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
    result = format_youtube_timestamp_link(url, "12:34")

    assert "dQw4w9WgXcQ" in result
    assert "t=754s" in result


def test_format_timestamp_link_youtube():
    """Test timestamp link formatting for YouTube."""
    url = "https://youtube.com/watch?v=abc123"
    result = format_timestamp_link(url, "5:00")

    assert "[5:00]" in result
    assert "youtube.com" in result
    assert "abc123" in result  # Video ID should be present


def test_format_timestamp_link_non_youtube():
    """Test timestamp link formatting for non-YouTube."""
    url = "https://example.com/podcast.mp3"
    result = format_timestamp_link(url, "10:30")

    assert result == "[10:30]"
