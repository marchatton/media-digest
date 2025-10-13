"""Tests for filename sanitization utility."""

from src.export.obsidian import sanitize_filename


def test_sanitize_filename_replaces_illegal_chars():
    raw = '2025/10/10: Report *Draft* | "Alpha"?'
    safe = sanitize_filename(raw)
    assert "/" not in safe and "|" not in safe and "*" not in safe
    assert ":" not in safe and "?" not in safe and '"' not in safe


def test_sanitize_filename_trims_and_collapses_space():
    raw = "  Hello   World  "
    safe = sanitize_filename(raw)
    assert safe == "Hello World"
