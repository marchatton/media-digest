"""Database query functions for Media Digest."""

from datetime import datetime
from typing import Any

from src.logging_config import get_logger

logger = get_logger(__name__)


def upsert_episode(
    conn,
    guid: str,
    feed_url: str,
    title: str,
    publish_date: str,
    author: str | None = None,
    audio_url: str | None = None,
    video_url: str | None = None,
    status: str = "pending",
) -> None:
    """Insert or update an episode.

    Args:
        conn: Database connection
        guid: Episode GUID (unique identifier)
        feed_url: RSS feed URL
        title: Episode title
        publish_date: Publication date
        author: Author/host name
        audio_url: Audio file URL
        video_url: Video file URL (if available)
        status: Processing status
    """
    conn.execute(
        """
        INSERT INTO episodes (guid, feed_url, title, publish_date, author, audio_url, video_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (guid) DO UPDATE SET
            title = excluded.title,
            audio_url = excluded.audio_url,
            video_url = excluded.video_url,
            updated_at = now()
        """,
        (guid, feed_url, title, publish_date, author, audio_url, video_url, status),
    )
    conn.commit()
    logger.debug(f"Upserted episode: {title} ({guid})")


def upsert_newsletter(
    conn,
    message_id: str,
    subject: str,
    sender: str,
    date: str,
    body_html: str | None = None,
    body_text: str | None = None,
    link: str | None = None,
    status: str = "pending",
) -> None:
    """Insert or update a newsletter.

    Args:
        conn: Database connection
        message_id: Email message ID
        subject: Email subject
        sender: Sender email
        date: Email date
        body_html: HTML body
        body_text: Plain text body
        link: Web version link
        status: Processing status
    """
    conn.execute(
        """
        INSERT INTO newsletters (message_id, subject, sender, date, body_html, body_text, link, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (message_id) DO UPDATE SET
            subject = excluded.subject,
            body_html = excluded.body_html,
            body_text = excluded.body_text,
            link = excluded.link,
            updated_at = now()
        """,
        (message_id, subject, sender, date, body_html, body_text, link, status),
    )
    conn.commit()
    logger.debug(f"Upserted newsletter: {subject} ({message_id})")


def update_episode_status(conn, guid: str, status: str, error_reason: str | None = None) -> None:
    """Update episode processing status.

    Args:
        conn: Database connection
        guid: Episode GUID
        status: New status
        error_reason: Error message if status is 'failed'
    """
    conn.execute(
        """
        UPDATE episodes
        SET status = ?, error_reason = ?, updated_at = now()
        WHERE guid = ?
        """,
        (status, error_reason, guid),
    )
    conn.commit()
    logger.debug(f"Updated episode {guid} status to {status}")


def update_newsletter_status(conn, message_id: str, status: str, error_reason: str | None = None) -> None:
    """Update newsletter processing status.

    Args:
        conn: Database connection
        message_id: Newsletter message ID
        status: New status
        error_reason: Error message if status is 'failed'
    """
    conn.execute(
        """
        UPDATE newsletters
        SET status = ?, error_reason = ?, updated_at = now()
        WHERE message_id = ?
        """,
        (status, error_reason, message_id),
    )
    conn.commit()
    logger.debug(f"Updated newsletter {message_id} status to {status}")


def get_pending_episodes(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get episodes with pending status.

    Args:
        conn: Database connection
        limit: Max number of episodes to return

    Returns:
        List of episode records
    """
    query = "SELECT * FROM episodes WHERE status = 'pending' ORDER BY publish_date DESC"
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]


def get_pending_newsletters(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get newsletters with pending status.

    Args:
        conn: Database connection
        limit: Max number of newsletters to return

    Returns:
        List of newsletter records
    """
    query = "SELECT * FROM newsletters WHERE status = 'pending' ORDER BY date DESC"
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]


def save_transcript(conn, episode_guid: str, transcript_text: str, transcript_path: str) -> None:
    """Save transcript to database.

    Args:
        conn: Database connection
        episode_guid: Episode GUID
        transcript_text: Full transcript text
        transcript_path: Path to transcript file
    """
    conn.execute(
        """
        INSERT INTO transcripts (episode_guid, transcript_text, transcript_path)
        VALUES (?, ?, ?)
        ON CONFLICT (episode_guid) DO UPDATE SET
            transcript_text = excluded.transcript_text,
            transcript_path = excluded.transcript_path
        """,
        (episode_guid, transcript_text, transcript_path),
    )
    conn.commit()
    logger.debug(f"Saved transcript for episode {episode_guid}")


def get_completed_episodes_needing_summary(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get completed episodes that don't have summaries yet.

    Args:
        conn: Database connection
        limit: Max number of episodes to return

    Returns:
        List of episode records with transcript info
    """
    query = """
        SELECT e.*, t.transcript_text, t.transcript_path
        FROM episodes e
        INNER JOIN transcripts t ON e.guid = t.episode_guid
        LEFT JOIN summaries s ON e.guid = s.item_id AND s.item_type = 'podcast'
        WHERE e.status = 'completed' AND s.item_id IS NULL
        ORDER BY e.publish_date DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]


def get_completed_newsletters_needing_summary(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get completed newsletters that don't have summaries yet.

    Args:
        conn: Database connection
        limit: Max number of newsletters to return

    Returns:
        List of newsletter records
    """
    query = """
        SELECT n.*
        FROM newsletters n
        LEFT JOIN summaries s ON n.message_id = s.item_id AND s.item_type = 'newsletter'
        WHERE n.status = 'completed' AND s.item_id IS NULL
        ORDER BY n.date DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]


def save_summary(
    conn,
    item_id: str,
    item_type: str,
    summary: str,
    key_topics: str,
    companies: str,
    tools: str,
    quotes: str,
    raw_rating: int,
    final_rating: int,
) -> None:
    """Save summary to database.

    Args:
        conn: Database connection
        item_id: Episode GUID or newsletter message ID
        item_type: 'podcast' or 'newsletter'
        summary: Summary text
        key_topics: JSON string of key topics
        companies: JSON string of companies
        tools: JSON string of tools
        quotes: JSON string of quotes
        raw_rating: Raw LLM rating
        final_rating: Final calibrated rating
    """
    conn.execute(
        """
        INSERT INTO summaries (item_id, item_type, summary, key_topics, companies, tools, quotes, raw_rating, final_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (item_id) DO UPDATE SET
            summary = excluded.summary,
            key_topics = excluded.key_topics,
            companies = excluded.companies,
            tools = excluded.tools,
            quotes = excluded.quotes,
            raw_rating = excluded.raw_rating,
            final_rating = excluded.final_rating
        """,
        (item_id, item_type, summary, key_topics, companies, tools, quotes, raw_rating, final_rating),
    )
    conn.commit()
    logger.debug(f"Saved summary for {item_type} {item_id}")
