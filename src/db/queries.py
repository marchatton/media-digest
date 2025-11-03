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


def _get_pending_items(conn, table: str, order_column: str, limit: int | None) -> list[dict[str, Any]]:
    """Fetch pending rows from the given table ordered by the provided column."""
    query = f"SELECT * FROM {table} WHERE status = 'pending' ORDER BY {order_column} DESC"
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    result = conn.execute(query, params).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]


def get_pending_episodes(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get episodes with pending status."""
    return _get_pending_items(conn, "episodes", "publish_date", limit)


def get_pending_newsletters(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Get newsletters with pending status."""
    return _get_pending_items(conn, "newsletters", "date", limit)


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
    structured_summary: str | None,
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
        INSERT INTO summaries (item_id, item_type, summary, key_topics, companies, tools, quotes, raw_rating, final_rating, structured_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (item_id) DO UPDATE SET
            summary = excluded.summary,
            key_topics = excluded.key_topics,
            companies = excluded.companies,
            tools = excluded.tools,
            quotes = excluded.quotes,
            raw_rating = excluded.raw_rating,
            final_rating = excluded.final_rating,
            structured_summary = excluded.structured_summary
        """,
        (
            item_id,
            item_type,
            summary,
            key_topics,
            companies,
            tools,
            quotes,
            raw_rating,
            final_rating,
            structured_summary,
        ),
    )
    conn.commit()
    logger.debug(f"Saved summary for {item_type} {item_id}")


def get_items_needing_summary(conn, limit: int | None = None) -> list[dict[str, Any]]:
    """Return processed items (episodes/newsletters) that lack entries in summaries.

    Returns rows with a unified shape: {item_type, id, title, date, author, link?, text_source}
    """
    # Episodes completed without summary
    episodes_query = (
        "SELECT 'podcast' AS item_type, e.guid AS id, e.title, e.publish_date AS date, coalesce(e.author, '') AS author, "
        "coalesce(e.video_url, e.audio_url, '') AS link "
        "FROM episodes e LEFT JOIN summaries s ON s.item_id = e.guid AND s.item_type = 'podcast' "
        "WHERE e.status = 'completed' AND s.item_id IS NULL"
    )

    union_query = f"{episodes_query} ORDER BY date DESC"
    if limit:
        union_query += f" LIMIT {limit}"

    result = conn.execute(union_query).fetchall()
    columns = [desc[0] for desc in conn.description]
    return [dict(zip(columns, row)) for row in result]
