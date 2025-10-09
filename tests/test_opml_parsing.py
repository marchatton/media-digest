"""Tests for OPML parsing."""

import pytest
from pathlib import Path
import tempfile
from src.ingest.podcasts import parse_opml


@pytest.fixture
def sample_opml():
    """Create a sample OPML file."""
    opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Test Podcasts</title>
  </head>
  <body>
    <outline text="Podcasts" title="Podcasts">
      <outline type="rss" text="Test Podcast 1" xmlUrl="https://example.com/feed1.xml" />
      <outline type="rss" text="Test Podcast 2" xmlUrl="https://example.com/feed2.xml" />
      <outline type="rss" text="Test Podcast 3" xmlUrl="https://example.com/feed3.xml" />
    </outline>
  </body>
</opml>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.opml', delete=False) as f:
        f.write(opml_content)
        opml_path = Path(f.name)

    yield opml_path

    # Cleanup
    opml_path.unlink(missing_ok=True)


def test_parse_opml_success(sample_opml):
    """Test successful OPML parsing."""
    feed_urls = parse_opml(sample_opml)

    assert len(feed_urls) == 3
    assert "https://example.com/feed1.xml" in feed_urls
    assert "https://example.com/feed2.xml" in feed_urls
    assert "https://example.com/feed3.xml" in feed_urls


def test_parse_opml_nonexistent():
    """Test parsing non-existent file."""
    feed_urls = parse_opml(Path("/nonexistent/file.opml"))
    assert feed_urls == []


def test_parse_opml_empty():
    """Test parsing empty OPML."""
    opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Empty</title></head>
  <body></body>
</opml>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.opml', delete=False) as f:
        f.write(opml_content)
        opml_path = Path(f.name)

    try:
        feed_urls = parse_opml(opml_path)
        assert feed_urls == []
    finally:
        opml_path.unlink(missing_ok=True)
