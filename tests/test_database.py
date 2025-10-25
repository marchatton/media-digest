"""Tests for database operations."""

import pytest
import tempfile
from pathlib import Path
from src.db.connection import get_connection, close_connection
from src.db.queries import (
    upsert_episode,
    upsert_newsletter,
    update_episode_status,
    update_newsletter_status,
    get_pending_episodes,
    get_pending_newsletters,
    get_items_needing_summary,
    save_transcript,
    save_summary,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    import duckdb
    from src.db.schema import init_schema

    # Create temp directory for test database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create connection directly (don't use global)
        conn = duckdb.connect(str(db_path))
        init_schema(conn)

        yield conn

        # Cleanup
        conn.close()


def test_upsert_episode(temp_db):
    """Test episode insertion and update."""
    conn = temp_db

    # Insert episode
    upsert_episode(
        conn,
        guid="test-episode-1",
        feed_url="https://example.com/feed",
        title="Test Episode",
        publish_date="2025-10-09",
        author="Test Host",
        audio_url="https://example.com/audio.mp3",
    )

    # Query episode
    result = conn.execute("SELECT * FROM episodes WHERE guid = ?", ("test-episode-1",)).fetchone()
    assert result is not None
    assert result[2] == "Test Episode"  # title
    assert result[5] == "https://example.com/audio.mp3"  # audio_url

    # Update episode (upsert)
    upsert_episode(
        conn,
        guid="test-episode-1",
        feed_url="https://example.com/feed",
        title="Updated Test Episode",
        publish_date="2025-10-09",
        author="Test Host",
        audio_url="https://example.com/audio.mp3",
    )

    # Verify update
    result = conn.execute("SELECT * FROM episodes WHERE guid = ?", ("test-episode-1",)).fetchone()
    assert result[2] == "Updated Test Episode"


def test_episode_status_update(temp_db):
    """Test episode status updates."""
    conn = temp_db

    # Insert episode
    upsert_episode(
        conn,
        guid="test-episode-2",
        feed_url="https://example.com/feed",
        title="Test Episode 2",
        publish_date="2025-10-09",
        audio_url="https://example.com/audio.mp3",
    )

    # Update to in_progress
    update_episode_status(conn, "test-episode-2", "in_progress")
    result = conn.execute("SELECT status FROM episodes WHERE guid = ?", ("test-episode-2",)).fetchone()
    assert result[0] == "in_progress"

    # Update to failed with error
    update_episode_status(conn, "test-episode-2", "failed", "Download timeout")
    result = conn.execute("SELECT status, error_reason FROM episodes WHERE guid = ?", ("test-episode-2",)).fetchone()
    assert result[0] == "failed"
    assert result[1] == "Download timeout"


def test_episode_status_with_transcript(temp_db):
    """Episodes with transcripts should still update status without FK violations."""
    conn = temp_db

    upsert_episode(
        conn,
        guid="ep-with-transcript",
        feed_url="https://example.com/feed",
        title="Episode With Transcript",
        publish_date="2025-10-09",
        audio_url="https://example.com/audio.mp3",
    )

    save_transcript(
        conn,
        episode_guid="ep-with-transcript",
        transcript_text="Lorem ipsum",
        transcript_path="/tmp/ep-with-transcript.json",
    )

    # Should not raise even though transcript row exists
    update_episode_status(conn, "ep-with-transcript", "completed")

    result = conn.execute(
        "SELECT status FROM episodes WHERE guid = ?", ("ep-with-transcript",)
    ).fetchone()
    assert result[0] == "completed"


def test_get_pending_episodes(temp_db):
    """Test retrieving pending episodes."""
    conn = temp_db

    # Insert multiple episodes
    upsert_episode(
        conn, "ep-1", "https://feed.com", "Episode 1", "2025-10-09", audio_url="https://audio.mp3"
    )
    upsert_episode(
        conn, "ep-2", "https://feed.com", "Episode 2", "2025-10-10", audio_url="https://audio.mp3"
    )
    upsert_episode(
        conn, "ep-3", "https://feed.com", "Episode 3", "2025-10-11", audio_url="https://audio.mp3"
    )

    # Mark one as completed
    update_episode_status(conn, "ep-2", "completed")

    # Get pending
    pending = get_pending_episodes(conn)
    assert len(pending) == 2
    guids = [ep["guid"] for ep in pending]
    assert "ep-1" in guids
    assert "ep-3" in guids
    assert "ep-2" not in guids


def test_idempotency(temp_db):
    """Test that upsert is idempotent."""
    conn = temp_db

    # Insert same episode twice
    for _ in range(2):
        upsert_episode(
            conn, "ep-id", "https://feed.com", "Episode", "2025-10-09", audio_url="https://audio.mp3"
        )

    # Should only have one record
    count = conn.execute("SELECT COUNT(*) FROM episodes WHERE guid = ?", ("ep-id",)).fetchone()[0]
    assert count == 1


def test_get_items_needing_summary(temp_db):
    """Test retrieving items that need summarization."""
    conn = temp_db

    # Insert episodes
    upsert_episode(
        conn, "ep-1", "https://feed.com", "Episode 1", "2025-10-09", audio_url="https://audio.mp3"
    )
    upsert_episode(
        conn, "ep-2", "https://feed.com", "Episode 2", "2025-10-10", audio_url="https://audio.mp3"
    )
    upsert_episode(
        conn, "ep-3", "https://feed.com", "Episode 3", "2025-10-11", audio_url="https://audio.mp3"
    )

    # Mark episodes as completed
    update_episode_status(conn, "ep-1", "completed")
    update_episode_status(conn, "ep-2", "completed")
    update_episode_status(conn, "ep-3", "pending")  # This one stays pending

    # Add transcripts for completed episodes
    save_transcript(conn, "ep-1", "Transcript 1", "/path/to/transcript1.json")
    save_transcript(conn, "ep-2", "Transcript 2", "/path/to/transcript2.json")

    # Add summary for ep-1
    save_summary(
        conn,
        item_id="ep-1",
        item_type="podcast",
        summary="Summary 1",
        key_topics='["topic1"]',
        companies="[]",
        tools="[]",
        quotes="[]",
        raw_rating=4,
        final_rating=4,
    )

    # Get items needing summary
    # Should return ep-2 only (completed + has transcript + no summary)
    items = get_items_needing_summary(conn)
    assert len(items) == 1
    assert items[0]["id"] == "ep-2"
    assert items[0]["item_type"] == "podcast"

